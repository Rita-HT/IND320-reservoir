# Imports the libraries needed
import pandas as pd
import requests
import streamlit as st
 
from nve_data import NUMERIC_COLUMNS, interval_slider, load_data
 
st.title("Data table")
st.write("Reservoir statistics retrieved directly from the NVE API.")
 
try:
    # Radio buttons: choose the type of area
    selected_area_type = st.radio("Area type", ["EL", "NO", "VASS"], horizontal=True)
 
    # Slider: choose which months to download
    start_month, end_month = interval_slider()
    data = load_data(start_month, end_month)
 
    if data.empty:
        st.warning("No data for this time interval.")
        st.stop()
 
    # Keep only the chosen area type
    area_data = data[data["Area_type"] == selected_area_type]
    if area_data.empty:
        st.warning(f"No data for area type {selected_area_type}.")
        st.stop()
 
    numeric_columns = [c for c in NUMERIC_COLUMNS if c in area_data.columns]
 
    # Make one table row for each area number
    # Each row has the latest value and the full list of values (for the chart)
    table_data = []
    for area, rows in area_data.groupby("Area"):
        rows = rows.sort_values("Date")
        row = {
            "Area": area,
            "Area_number": rows["Area_number"].iloc[0],
            "Latest date": rows["Date"].max().date(),
        }
        for column in numeric_columns:
            values = rows[column].dropna().tolist()
            if values:
                row[column] = values[-1]           # latest value
                row[f"{column} trend"] = values    # all values
        table_data.append(row)
    data_table = pd.DataFrame(table_data)
 
    # LineChartColumn shows a small line chart inside each table row
    column_config = {
        f"{c} trend": st.column_config.LineChartColumn(
            f"{c} trend", help=f"{c} over the chosen months")
        for c in numeric_columns if f"{c} trend" in data_table.columns
    }
 
    st.subheader(f"Area data: {selected_area_type}")
    st.write(f"Period: {start_month} to {end_month}")
    st.dataframe(data_table, column_config=column_config,
                 hide_index=True, width="stretch")
 
    # Extra information the user can open
    with st.expander("View full data"):
        st.dataframe(area_data, width="stretch")
 
    with st.expander("Data source"):
        st.markdown("[NVE Reservoir Statistics API]"
                    "(https://biapi.nve.no/magasinstatistikk/swagger/index.html)")
        st.markdown("[NVE Reservoir Statistics]"
                    "(https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)")
 
# Warning if something goes wrong
except requests.RequestException as error:
    st.error(f"Could not get data from NVE: {error}")
except (ValueError, KeyError, TypeError) as error:
    st.error(f"Could not process the NVE data: {error}")
 
