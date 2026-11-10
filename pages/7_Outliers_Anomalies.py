# Page 7 - Outliers Anomalies

#Import libraries needed 
from pathlib import Path
import pandas as pd
import streamlit as st
from data_quality import download_weather, plot_spc_outliers, plot_lof_anomalies, HOURLY_VARS

# Show the Titles
st.title("Outliers anomalies")
st.write("This page displays hourly weather data from ERA5 and Open-Meteo for the selected area. It provides an overview of weather conditions and how they change throughout the day.")

# NVE-based region used for each electricity area. NO3 uses "Mid" (RM).
AREA_TO_REGION = {1: "East", 2: "East", 3: "Mid", 4: "North", 5: "West"}

# Sampled locations (50 per region) saved from the notebook
# Find the file with the saved locations
LOCATIONS_FILE = Path(__file__).resolve().parent.parent / "data" / "locations.json"

# Read the locations into a table
locations = pd.read_json(LOCATIONS_FILE)


# Download weather data directly from Open-Meteo, averaged per hour (cached)
# Cache the result so we don't download it again every time
@st.cache_data(show_spinner="Downloading weather data (this can take a minute) ...")
def get_weather(region, year, n_locations):
    # Download the weather for the whole year
    raw = download_weather(
        region,
        f"{year}-01-01",
        f"{year}-12-31",
        locations,
        n_locations=n_locations
    )

    # Take the average of all locations for each hour
    return raw.groupby("time")[HOURLY_VARS].mean()


# Let the user pick an electricity area (NO3 is the default)
area = st.selectbox(
    "Electricity area",
    # The five areas to choose from
    [1, 2, 3, 4, 5],
    # Start on the third one, NO3
    index=2,
    # Show the number as NO1, NO2 and so on
    format_func=lambda n: f"NO{n}"
)

# Let the user pick a year, starting with the newest (2024)
year = st.selectbox("Year", list(range(2024, 2018, -1)), index=0)

# Slider for how many locations to download
n_locations = st.slider("Number of locations to use", 5, 50, 25, step=5)

# Find the region that belongs to the chosen area
region = AREA_TO_REGION[area]

# Tell the user which region is used
st.caption(f"NO{area} is represented by the region '{region}'.")

# Get the weather data (from the cache if it's already there)
weather = get_weather(region, year, n_locations)

# Make two tabs: one for SPC outliers and one for LOF anomalies
tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

# Tab 1: SPC outliers in precipitation
with tab_spc:
    # Slider for the DCT cut-off (how much of the slow variation we remove)
    cutoff = st.slider(
        "DCT cut-off (cycles per year)", 2.0, 50.0, 10.0, step=1.0,
        key="spc_cutoff"
    )

    # Slider for how many standard deviations the limits are
    n_std = st.slider(
        "Number of standard deviations", 1.0, 6.0, 3.0, step=0.5
    )

    # Find the outliers and make the plot
    figure, summary, outliers = plot_spc_outliers(
        weather["precipitation"],
        cutoff_per_year=cutoff,
        n_std=n_std
    )

    # Show the plot on the page
    st.pyplot(figure)

    # Show the summary numbers
    st.json(summary)

    # Show the 20 biggest outliers in a table
    st.dataframe(outliers.sort_values("value", ascending=False).head(20))

# Tab 2: LOF anomalies in temperature
with tab_lof:
    # Slider for the share of points we expect to be anomalies
    contamination = st.slider(
        "Proportion of anomalies", 0.001, 0.05, 0.01, step=0.001,
        format="%.3f"
    )

    # Slider for how many neighbours LOF compares with
    n_neighbors = st.slider("Number of neighbours", 5, 100, 15, step=5)

    # Slider for the DCT cut-off
    cutoff_lof = st.slider(
        "DCT cut-off (cycles per year)", 2.0, 50.0, 8.0, step=1.0,
        key="lof_cutoff"
    )

    # Find the anomalies and make the plot
    figure, summary, anomalies = plot_lof_anomalies(
        weather["temperature_2m"],
        contamination=contamination,
        n_neighbors=n_neighbors,
        cutoff_per_year=cutoff_lof
    )

    # Show the plot on the page
    st.pyplot(figure) 

    # Show the summary numbers
    st.json(summary)

    # Show the 20 strongest anomalies in a table
    st.dataframe(anomalies.sort_values("anomaly_score", ascending=False).head(20))