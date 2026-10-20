
# Imports the libraries needed
import pandas as pd
import streamlit as st
import requests


# Reads data directly from the NVE API
@st.cache_data(ttl=3600)
def load_data():

    # Retrieves reservoir statistics from NVE
    url = (
        "https://biapi.nve.no/magasinstatistikk/"
        "api/Magasinstatistikk/HentOffentligData"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Converts the API response into a Df
    data = pd.DataFrame(response.json())

    # Gives the columns English names for readability
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

    # Checks that the expected columns are available
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

    # Converts the date and numerical columns
    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    data["Fill_lvl"] = pd.to_numeric(
        data["Fill_lvl"],
        errors="coerce"
    )

    # Creates a column that identifies each area
    data["Area_type"] = data["Area_type"].astype(str)
    data["Area_number"] = data["Area_number"].astype(str)

    data["Area"] = (
        data["Area_type"] + data["Area_number"]
    )

    # Creates a column showing the month
    data["Month"] = data["Date"].dt.to_period("M").astype(str)

    # Sorts the data by area and date
    data = data.sort_values(["Area", "Date"])

    return data


# Reads data from the NVE API
st.title("Reservoir")

st.write(
    "Reservoir statistics retrieved directly from the NVE API."
)

try:
    data = load_data()

    # Checks if data was returned from the API
    if data.empty:
        st.warning("No reservoir data available.")
        st.stop()

    # Removes rows without a valid date or area type
    data = data.dropna(
        subset=["Date", "Area_type", "Area_number"]
    ).copy()

    # Lets the user select the type of area
    selected_area_type = st.radio(
        "Area type",
        ["EL", "NO", "VASS"],
        horizontal=True
    )

    # Keeps only data from the selected area type
    area_data = data[
        data["Area_type"] == selected_area_type
    ].copy()

    # Checks if data is available for the selected area type
    if area_data.empty:
        st.warning(
            f"No data available for area type {selected_area_type}."
        )
        st.stop()

    # Finds the available months for the selected area type
    available_months = sorted(
        area_data["Month"].dropna().unique()
    )

    if len(available_months) == 0:
        st.warning("No valid dates available.")
        st.stop()

    # Lets the user select the time interval
    start_month, end_month = st.select_slider(
        "Download interval",
        options=available_months,
        value=(available_months[0], available_months[-1])
    )

    # Keeps only data from the selected time interval
    mask = (
        (area_data["Month"] >= start_month)
        & (area_data["Month"] <= end_month)
    )

    month_data = area_data[mask].copy()

    # Checks if data is available for the selected interval
    if month_data.empty:
        st.warning("No data available for this time interval.")
        st.stop()

    # Finds the numerical columns that can be displayed
    numeric_columns = [
        column for column in [
            "Fill_lvl",
            "Capacity_TWh",
            "Fill_TWh",
            "Fill_lvl_Lstweek",
            "Diff_Fill_lvl"
        ]
        if column in month_data.columns
    ]

    # Creates a table with one row for each area
    table_data = []

    for area, area_month_data in month_data.groupby("Area"):

        # Sorts the observations by date
        area_month_data = area_month_data.sort_values("Date")

        # Creates a row with the area information
        row = {
            "Area": area,
            "Area_number": area_month_data["Area_number"].iloc[0],
            "Latest date": area_month_data["Date"].max().date()
        }

        # Adds the latest values and trends for numerical columns
        for column in numeric_columns:

            values = area_month_data[column].dropna().tolist()

            if values:
                row[column] = values[-1]
                row[f"{column} trend"] = values

        table_data.append(row)

    data_table = pd.DataFrame(table_data)

    # Displays the table with a small line chart for each area
    column_config = {}

    for column in numeric_columns:
        trend_column = f"{column} trend"

        if trend_column in data_table.columns:
            column_config[trend_column] = (
                st.column_config.LineChartColumn(
                    trend_column,
                    help=f"Development of {column} over the selected interval"
                )
            )

    st.subheader(
        f"Area data: {selected_area_type}"
    )

    st.write(
        f"Period: {start_month} to {end_month}"
    )

    st.dataframe(
        data_table,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )

    # Displays the data used for the selected interval
    with st.expander("View full data"):
        st.dataframe(
            month_data,
            use_container_width=True
        )

    # Links to the NVE data source
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
    st.error(f"Could not retrieve data from NVE: {error}")

except (ValueError, KeyError, TypeError) as error:
    st.error(f"Could not process the NVE data: {error}")
