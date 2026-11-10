# Page 6 - STL Spectrogram

#Import libraries needed 
import pandas as pd
import requests
import streamlit as st
from data_quality import plot_stl, plot_spectrogram

# Show the titles
st.title("STL spectrogram")
st.write("Shows weekly reservoir filling data from NVE")

# The address of the NVE reservoir API
API_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk"

# Download the reservoir data once and keep it in the cache
# Cache the result so we don't download it again every time
@st.cache_data(show_spinner="Downloading reservoir data ...")
def load_reservoirs():
    # Ask the NVE API for the public data
    response = requests.get(f"{API_URL}/HentOffentligData", timeout=60)
    # Stop with an error if the download failed
    response.raise_for_status()
    # Turn the answer into a table
    return pd.DataFrame(response.json())


# Get the data (from the cache if it's already there)
reservoirs = load_reservoirs()

# Area selector: electricity areas NO1-NO5, starting on NO3
area = st.selectbox(
    "Electricity area",
    # The five areas to choose from
    [1, 2, 3, 4, 5],
    # Start on the third one, NO3
    index=2,
    # Show the number as NO1, NO2 and so on
    format_func=lambda n: f"NO{n}"
)

# Weekly filling degree for the selected area, with the date as index
filling_data = (
    reservoirs[
        # Keep only electricity areas
        (reservoirs["omrType"] == "EL") &
        # Keep only the area the user picked
        (reservoirs["omrnr"] == area)
    ]
    # Turn the date text into real dates
    .assign(date=lambda d: pd.to_datetime(d["dato_Id"]))
    # Use the date as the index and keep the filling degree
    .set_index("date")["fyllingsgrad"]
    # Put the dates in order
    .sort_index()
)

# Make two tabs: one for STL and one for the spectrogram
tab_stl, tab_spec = st.tabs(["STL", "Spectrogram"])

# Tab 1: STL decomposition with adjustable smoothers
with tab_stl:
    # Slider for how fast the seasonal pattern may change
        seasonal = st.slider(
        "Seasonal smoother (odd)", 7, 77, 15, step=2
    )

    # Slider for how smooth the trend is
    trend = st.slider(
        "Trend smoother (odd, larger than 52)", 55, 253, 125, step=2
    )

    # Checkbox to switch robust mode on or off
    robust = st.checkbox("Robust", value=True)

    # Make the STL plot with the chosen settings
    figure = plot_stl(
        filling_data,
        # One year is 52 weeks
        period=52,
        seasonal=seasonal,
        trend=trend,
        robust=robust,
        title=f"Weekly reservoir filling in NO{area}"
    )

    # Show the plot on the page
    st.pyplot(figure)


# Tab 2: spectrogram with adjustable window length and overlap
with tab_spec:
    # Slider for how many weeks are in each window
    window_length = st.slider(
        "Window length (weeks)", 26, 260, 156, step=13
    )

    # Slider for how much the windows overlap
    overlap = st.slider(
        "Overlap (weeks)",
        # Smallest overlap is zero
        0,
        # Overlap must be shorter than the window
        window_length - 1,
        # Start value, but never longer than the window
        min(117, window_length - 1)
    )

    # Make the spectrogram with the chosen settings
    figure = plot_spectrogram(
        filling_data,
        window_length=window_length,
        overlap=overlap,
        # Only show up to 4 cycles per year
        max_freq=4.0,
        title=f"Weekly reservoir filling in NO{area}"
    )

    # Show the plot on the page
    st.pyplot(figure)
