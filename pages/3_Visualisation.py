# Imports the libraries needed
import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
 
from nve_data import NUMERIC_COLUMNS, interval_slider, load_data
 
st.title("Visualisation of the reservoir")
 
try:
    # Radio buttons: choose the type of area (one line per area number)
    selected_area_type = st.radio("Area type", ["EL", "NO", "VASS"], horizontal=True)
 
    # Slider: same download interval as on page 2
    start_month, end_month = interval_slider()
    data = load_data(start_month, end_month)
 
    # Keep only the chosen area type
    plot_data = data[data["Area_type"] == selected_area_type].copy()
    if plot_data.empty:
        st.warning("No data for this choice.")
        st.stop()
 
    # Find the columns that have values we can plot
    numeric_columns = [c for c in NUMERIC_COLUMNS
                       if c in plot_data.columns and plot_data[c].notna().any()]
    selected_column = st.selectbox("Column", numeric_columns + ["All columns"])
 
    fig, ax = plt.subplots(figsize=(10, 5))
 
    if selected_column == "All columns":
        # Scale every column to 0-1, so they fit on the same axis
        values = plot_data[numeric_columns].copy()
        for column in numeric_columns:
            low, high = values[column].min(), values[column].max()
            values[column] = (values[column] - low) / (high - low) if high > low else 0
        # Draw one line for each area and column
        for area, rows in plot_data.groupby("Area"):
            rows = rows.sort_values("Date")
            for column in numeric_columns:
                ax.plot(rows["Date"], values.loc[rows.index, column],
                        linewidth=0.8, label=f"{area} - {column}")
        ax.set_ylabel("Scaled value (0-1)")
    else:
        # Draw one line for each area number
        for area, rows in plot_data.groupby("Area"):
            rows = rows.sort_values("Date")
            ax.plot(rows["Date"], rows[selected_column], linewidth=1.0, label=area)
        ax.set_ylabel(selected_column)
 
    # Title, labels and legend
    ax.set_title(f"{selected_column} - {selected_area_type} ({start_month} to {end_month})")
    ax.set_xlabel("Date")
    ax.legend(fontsize=7, ncol=2)
    fig.autofmt_xdate()
    plt.tight_layout()
 
    # Show the plot in Streamlit
    st.pyplot(fig)
    plt.close(fig)
 
    # Extra information the user can open
    with st.expander("View data"):
        st.dataframe(plot_data, width="stretch")
 
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
