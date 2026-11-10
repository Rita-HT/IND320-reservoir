
# Import libraries for data handling, calculations and plotting
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

# Open-Meteos API
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

#Weather variables used 
HOURLY_VARS = [
    "temperature_2m",       # Air temperature
    "precipitation",        # Total precipitation
    "rain",                 # Rainfall
    "snowfall",              # Snowfall
    "wind_speed_10m",       # Wind speed
    "relative_humidity_2m", # Relative humidity
    "surface_pressure",     # Air pressure
    "cloud_cover"           # Cloud cover
]


# Download hourly weather data for one region
def download_weather(region, start, end, locations,
                     n_locations=50, batch_size=25):

    # Select locations belonging to said region
    points = (
        locations[locations["region"] == region]
        .head(n_locations)
        .reset_index(drop=True)
    )

    # Empty list to store the downloaded data
    frames = []

    # Download the locations in smaller batches
    for i in range(0, len(points), batch_size):
        batch = points.iloc[i:i + batch_size]

        # Prepare the information needed for the API request
        params = {
            "latitude": ",".join(f"{v:.4f}" for v in batch["lat"]),
            "longitude": ",".join(f"{v:.4f}" for v in batch["lon"]),
            "start_date": start,
            "end_date": end,
            "hourly": ",".join(HOURLY_VARS),
            "models": "era5"
        }

        # Trys again if the API request reaches the rate limit
        for attempt in range(6):
            response = requests.get(
                ARCHIVE_URL,
                params=params,
                timeout=120
            )

            # Wait longer between attempts if the API is busy
            if response.status_code == 429:
                time.sleep(15 * 2 ** attempt)
                continue

            # Check whether the request was successful
            response.raise_for_status()
            break

        # Convert the API into data
        data = response.json()

        # Make sure the API response is a list
        if isinstance(data, dict):
            data = [data]

        # Store weather data for each location
        for j, location in enumerate(data):
            df = pd.DataFrame(location["hourly"])

            # Convert time column to datetime format
            df["time"] = pd.to_datetime(df["time"])

            # Give each location its own ID
            df["location_id"] = i + j

            frames.append(df)

        # Wait briefly before the next request
        time.sleep(1)

    # Combine all downloaded data into one DataFrame
    return pd.concat(frames, ignore_index=True)


# Applies DCT high-pass filter to the time series
def dct_highpass(series, cutoff_per_year=10.0,
                 samples_per_year=8766):

    # Fill missing values using interpolation
    series = np.asarray(
        pd.Series(series).interpolate(limit_direction="both"),
        dtype=float
    )

    # Find the length of the time series
    n = len(series)

    # Calculate the frequency cutoff
    cutoff = int(round(
        cutoff_per_year * 2 * n / samples_per_year
    ))

    # Keep the cutoff within the valid range
    cutoff = min(max(cutoff, 1), n)

    # Transform the data into frequency coefficients
    coefficients = dct(series, type=2, norm="ortho")

    # Remove the higher frequency coefficients
    coefficients[cutoff:] = 0

    # Transform the filtered coefficients back into data
    lowpass = idct(coefficients, type=2, norm="ortho")

    # Calculate the short-term variations
    highpass = series - lowpass

    return highpass, lowpass


# Detect unusual observations using SPC limits
def plot_spc_outliers(series, cutoff_per_year=10.0,
                      n_std=3.0,
                      title="Average precipitation",
                      ylabel="Precipitation (mm/h)"):

    # Convert the data to numerical values
    series = series.astype(float)

    # Separate long-term and short-term variations
    highpass, lowpass = dct_highpass(series, cutoff_per_year)

    # Calculate the median of the short-term variations
    median = np.median(highpass)

    # Estimate the variation using the median absolute deviation
    sigma = 1.4826 * np.median(np.abs(highpass - median))

    # Use standard deviation if the estimated variation is zero
    if sigma == 0:
        sigma = highpass.std()

    # Calculate the upper and lower control limits
    upper = lowpass + median + n_std * sigma
    lower = lowpass + median - n_std * sigma

    # Find observations outside the control limits
    is_outlier = (
        (highpass > median + n_std * sigma) |
        (highpass < median - n_std * sigma)
    )

    # Create a figure to show the results
    fig, ax = plt.subplots(figsize=(12, 4.5))

    # Plot the original weather data
    ax.plot(
        series.index,
        series.values,
        color="tab:blue",
        lw=0.7,
        label="Series"
    )

    # Plot the upper control limit
    ax.plot(
        series.index,
        upper,
        color="tab:green",
        lw=1.2,
        label=f"SPC limits (±{n_std:g}σ)"
    )

    # Plot the lower control limit
    ax.plot(
        series.index,
        lower,
        color="tab:green",
        lw=1.2
    )

    # Highlight observations detected as outliers
    ax.scatter(
        series.index[is_outlier],
        series.values[is_outlier],
        color="tab:red",
        s=14,
        label=f"Outliers ({is_outlier.sum()})"
    )

    # Labels and a legend to the figure
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper right")

    # Adjust the layout
    fig.tight_layout()

    # Save the observations detected as outliers
    outliers = pd.DataFrame({
        "value": series.values[is_outlier],
        "highpass": highpass[is_outlier]
    }, index=series.index[is_outlier])

    # Create a summary of the SPC results
    summary = {
        "n_points": len(series),
        "n_outliers": int(is_outlier.sum()),
        "share_outliers_%": round(100 * is_outlier.mean(), 2),
        "n_std": n_std,
        "cutoff_per_year": cutoff_per_year,
        "median": float(median),
        "robust_sigma": float(sigma),
        "n_above": int(
            (highpass > median + n_std * sigma).sum()
        ),
        "n_below": int(
            (highpass < median - n_std * sigma).sum()
        )
    }

    return fig, summary, outliers


# Detect unusual weather observations using LOF
def plot_lof_anomalies(series, contamination=0.01,
                       n_neighbors=15,
                       cutoff_per_year=8.0,
                       title="Average temperature",
                       ylabel="Temperature (°C)"):

    # Convert the time series to numerical values
    filtered_data = series.astype(float)

    # Focus on short-term variations using the DCT filter
    highpass, _ = dct_highpass(
        filtered_data,
        cutoff_per_year
    )

    # Create the LOF model
    lof_model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination
    )

    # Fit the model and classify the observations
    predictions = lof_model.fit_predict(
        highpass.reshape(-1, 1)
    )

    # Mark observations classified as anomalies
    is_anomaly = predictions == -1

    # Calculate the anomaly scores
    anomaly_scores = -lof_model.negative_outlier_factor_

    # Create a figure to show the results
    fig, axis = plt.subplots(figsize=(10, 5))

    # Plot the original time series
    axis.plot(
        filtered_data.index,
        filtered_data.values,
        color="tab:blue",
        lw=0.7,
        label="Series"
    )

    # Highlight the observations detected as anomalies
    axis.scatter(
        filtered_data.index[is_anomaly],
        filtered_data.values[is_anomaly],
        color="tab:red",
        s=6,
        label=f"Anomalies ({is_anomaly.sum()})"
    )

    # Add labels and a legend
    axis.set(title=title, ylabel=ylabel)
    axis.legend(loc="upper right")

    # Adjust the layout
    fig.tight_layout()

    # Store the detected anomalies and their scores
    detected_anomalies = pd.DataFrame({
        "value": filtered_data.values[is_anomaly],
        "highpass": highpass[is_anomaly],
        "anomaly_score": anomaly_scores[is_anomaly]
    }, index=filtered_data.index[is_anomaly])

    # Create a summary of the LOF results
    summary = {
        "n_points": len(filtered_data),
        "n_anomalies": int(is_anomaly.sum()),
        "share_anomalies_%": round(100 * is_anomaly.mean(), 2),
        "contamination": contamination,
        "n_neighbors": n_neighbors,
        "cutoff_per_year": cutoff_per_year,
        "max_anomaly_score": float(anomaly_scores.max())
    }

    return fig, summary, detected_anomalies


# Separate a weekly time series into different components using STL
def plot_stl(time_series, period=52, seasonal=13,
             trend=53, robust=True,
             title="STL decomposition – degree of filling"):

    # Check that the seasonal smoothing value is valid
    if seasonal < 3 or seasonal % 2 == 0:
        raise ValueError("seasonal must be an odd integer >= 3")

    # Check that the trend smoothing value is valid
    if trend <= period or trend % 2 == 0:
        raise ValueError("trend must be an odd integer > period")

    # Perform the STL decomposition
    stl_result = STL(
        time_series,
        period=period,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    ).fit()

    # Collect the four components from the decomposition
    decomposition_components = [
        ("Observed", stl_result.observed),
        ("Trend", stl_result.trend),
        ("Seasonal", stl_result.seasonal),
        ("Residual", stl_result.resid)
    ]

    # Create four plots with a shared time axis
    fig, plot_axes = plt.subplots(
        4, 1,
        figsize=(12, 9),
        sharex=True
    )

    # Plot each component separately
    for plot_axis, (component_name, component_values) in zip(
        plot_axes,
        decomposition_components
    ):
        plot_axis.plot(
            time_series.index,
            np.asarray(component_values),
            lw=0.9
        )

        # Add a label to each subplot
        plot_axis.set_ylabel(component_name)

    # Add a title with the selected settings
    plot_axes[0].set_title(
        f"{title}\n(period={period}, seasonal={seasonal}, "
        f"trend={trend}, robust={robust})"
    )

    # Adjust the layout
    fig.tight_layout()

    return fig


# Show how the frequency content changes over time
def plot_spectrogram(time_series, window_length=104,
                     overlap=78,
                     samples_per_year=52.18,
                     max_freq=6.0,
                     title="Spectrogram – degree of filling"):

    # Check that the overlap value is valid
    if not 0 <= overlap < window_length:
        raise ValueError(
            "overlap must be >= 0 and < window_length"
        )

    # Check that the selected window fits the time series
    if window_length > len(time_series):
        raise ValueError(
            "window_length is longer than the time series"
        )

    # Calculate the spectrogram
    frequencies, times, power = spectrogram(
        time_series.values.astype(float),
        fs=samples_per_year,
        window="hann",
        nperseg=window_length,
        noverlap=overlap,
        detrend="linear",
        scaling="density"
    )

    # Convert the calculated times into calendar dates
    dates = time_series.index[0] + pd.to_timedelta(
        times * 365.25,
        unit="D"
    )

    # Keep only the frequencies within the selected range
    keep = frequencies <= max_freq

    # Create a figure for the spectrogram
    fig, axis = plt.subplots(figsize=(12, 4.5))

    # Plot the power for each frequency over time
    mesh = axis.pcolormesh(
        dates,
        frequencies[keep],
        10 * np.log10(power[keep] + 1e-12),
        shading="auto"
    )

    # Add a colour bar to explain the power values
    fig.colorbar(mesh, ax=axis, label="Power (dB)")

    #Labels and a title
    axis.set_ylabel("Frequency (cycles per year)")
    axis.set_title(
        f"{title}\n(window={window_length}, overlap={overlap})"
    )

    # Adjusts the layout
    fig.tight_layout()
    return fig
