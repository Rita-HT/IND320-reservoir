import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import requests


# Loads data from the NVE API
@st.cache_data(ttl=3600)
def load_data():

    # URL for the NVE API
    url = (
        "https://biapi.nve.no/magasinstatistikk/"
        "api/Magasinstatistikk/HentOffentligData"
    )

    # Sends a request and checks for errors
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Converts the API response into a Df
    data = pd.DataFrame(response.json())

    # Renames columns to English
    data = data.rename(columns={
        "dato_Id": "Date",
        "omrType": "Area_type",
        "omrnr": "Area_number",
        "iso_aar": "Iso_yr",
        "iso_uke": "Iso_week",
        "fyllingsgrad": "Fill_lvl",
        "kapasitet_TWh": "Capacity_TWh",
        "fylling_TWh": "Fill_TWh",
        "neste_Publiseringsdato": "Nxt_pubDate",
        "fyllingsgrad_forrige_uke": "Fill_lvl_Lstweek",
        "endring_fyllingsgrad": "Diff_Fill_lvl"
    })

    # Checks that the required columns are available
    required_columns = [
        "Date",
        "Area_type",
        "Area_number",
        "Fill_lvl"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing expected NVE columns: "
            + ", ".join(missing_columns)
        )

    # Converts the dates to date format
    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    # Converts the measurement columns to numbers
    numeric_columns = [
        "Fill_lvl",
        "Capacity_TWh",
        "Fill_TWh",
        "Fill_lvl_Lstweek",
        "Diff_Fill_lvl"
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    # area types and numbers use text format
    data["Area_type"] = (
        data["Area_type"].astype(str).str.strip()
    )
    data["Area_number"] = data["Area_number"].astype(str)

    # Combines the area type and number into one column
    data["Area"] = (
        data["Area_type"] + data["Area_number"]
    )

    # Creates a column showing the month of each observation
    data["Month"] = data["Date"].dt.to_period("M").astype(str)

    # Sorts by area and date
    data = data.sort_values(["Area", "Date"])

    return data


# Shows the page title
st.title("Visualisation of the reservoir")

try:
    # Loads data from the NVE API
    data = load_data()

    # Checks if the API returned any data
    if data.empty:
        st.warning("No reservoir data available.")
        st.stop()

    # Removes rows without a valid date or area
    data = data.dropna(
        subset=["Date", "Area_type", "Area_number"]
    ).copy()

    # Finds the area types available in the data
    available_types = sorted(data["Area_type"].unique())

    # Uses the area types listed in the assignment
    preferred_types = ["EL", "NO", "VASS"]
    area_types = [
        area_type for area_type in preferred_types
        if area_type in available_types
    ]

    # Uses the available types if the expected types are missing
    if not area_types:
        area_types = available_types

    # Lets the user choose an area type
    selected_area_type = st.radio(
        "Area type",
        area_types,
        horizontal=True
    )

    # Keeps only data for the selected area type
    area_data = data[
        data["Area_type"] == selected_area_type
    ].copy()

    # Finds the months available for the selected area type
    available_months = sorted(
        area_data["Month"].dropna().unique()
    )

    # Stops if there are no valid months
    if not available_months:
        st.warning("No valid dates available.")
        st.stop()

    # Lets the user choose the time interval
    start_month, end_month = st.select_slider(
        "Time interval",
        options=available_months,
        value=(available_months[0], available_months[-1])
    )

    # Keeps only data within the selected time interval
    mask = (
        (area_data["Month"] >= start_month)
        & (area_data["Month"] <= end_month)
    )

    plot_data = area_data[mask].copy()

    # Checks if data is available for the selected interval
    if plot_data.empty:
        st.warning("No data available for this time interval.")
        st.stop()

    # Finds the numerical columns that can be plotted
    numeric_columns = [
        column for column in [
            "Fill_lvl",
            "Capacity_TWh",
            "Fill_TWh",
            "Fill_lvl_Lstweek",
            "Diff_Fill_lvl"
        ]
        if column in plot_data.columns
        and plot_data[column].notna().any()
    ]

    # Stops if there are no numerical values to plot
    if not numeric_columns:
        st.warning("No numerical data available to plot.")
        st.stop()

    # Lets the user choose which value to display
    selected_column = st.selectbox(
        "Column",
        numeric_columns + ["All columns"]
    )

    # Creates the plot
    fig, ax = plt.subplots(figsize=(10, 5))

    if selected_column == "All columns":

        # Copies the values before normalising them
        plot_values = plot_data[numeric_columns].copy()

        # Scales the values between 0 and 1
        for column in numeric_columns:
            minimum = plot_values[column].min()
            maximum = plot_values[column].max()

            if maximum > minimum:
                plot_values[column] = (
                    (plot_values[column] - minimum)
                    / (maximum - minimum)
                )
            else:
                plot_values[column] = 0

        # Draws a separate line for each area and column
        for area, area_rows in plot_data.groupby("Area"):
            area_rows = area_rows.sort_values("Date")

            for column in numeric_columns:
                ax.plot(
                    area_rows["Date"],
                    plot_values.loc[area_rows.index, column],
                    marker="o",
                    label=f"{area} - {column}"
                )

        # Labels the axis for normalised values
        ax.set_ylabel("Normalised value (0-1)")

    else:

        # Draws a separate line for each area number
        for area, area_rows in plot_data.groupby("Area"):
            area_rows = area_rows.sort_values("Date")

            ax.plot(
                area_rows["Date"],
                area_rows[selected_column],
                marker="o",
                label=area
            )

        # Labels the axis with the selected column
        ax.set_ylabel(selected_column)

    # Adds the chart title and axis labels
    ax.set_title(
        f"{selected_column} - {selected_area_type} "
        f"({start_month} to {end_month})"
    )
    ax.set_xlabel("Date")

    # Shows a legend for the different lines
    ax.legend(fontsize=8)

    # Adjusts the date labels and chart layout
    fig.autofmt_xdate()
    plt.tight_layout()

    # Displays the plot in Streamlit
    st.pyplot(fig)
    plt.close(fig)

    # Shows the data used in the plot
    with st.expander("View data"):
        st.dataframe(plot_data, use_container_width=True)

    # Shows links to the data sources
    with st.expander("Data source"):
        st.markdown(
            "[NVE Reservoir Statistics API]"
            "(https://biapi.nve.no/magasinstatistikk/swagger/index.html)"
        )

        st.markdown(
            "[NVE Reservoir Statistics]"
            "(https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)"
        )

except requests.RequestException as error:
    # Shows an error if the API request fails
    st.error(f"Could not retrieve data from NVE: {error}")

except (ValueError, KeyError, TypeError) as error:
    # Shows an error if the data cannot be processed
    st.error(f"Could not process the NVE data: {error}")
