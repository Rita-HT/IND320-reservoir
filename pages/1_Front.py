
# Imports the library needed
import streamlit as st

# Display the project titles
st.title("IND320")
st.write("Project Work, Part 2 – Data Sources and Project Work, Part 3 – Data Quality")

# Purpose of the third project
st.subheader("Project Work, Part 3 – Data Quality")

st.write("""
The third project focuses on weather data and data quality. Hourly weather
data from ERA5 is downloaded using the Open-Meteo API for randomly selected
locations within the NVE regions. The weather data is then used to identify
outliers and unusual values. Reservoir filling data from NVE is also analysed
using seasonal decomposition and a spectrogram.
""")

st.markdown("""
- Page 6 – STL and spectrogram: Shows the STL decomposition and spectrogram of weekly reservoir filling levels for a selected price area.
- Page 7 – Outliers and anomalies: Shows outliers detected using SPC and anomalies identified with Local Outlier Factor (LOF) in the weather data for a selected area and year.
""")

# Purpose of the second project
st.subheader("Project Work, Part 2 – Data Sources")

st.write("""
The second project in IND320 focuses on retrieving, processing and
visualising Norwegian reservoir statistics and cross-border electricity
transfers. Reservoir data is retrieved from the NVE Reservoir Statistics
API, while electricity transfer data is obtained through the ENTSO-E
Transparency Platform API. These data sources are used to explore
reservoir filling levels and electricity flows between Norway and
neighbouring countries.
""")

# Links to the data sources used in this project
st.subheader("Data Sources and Documentation")

st.markdown("""
- [NVE Reservoir Statistics API documentation](https://biapi.nve.no/magasinstatistikk/swagger/index.html)
- [NVE Reservoir Statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)
- [NVE Atlas](https://atlas.nve.no/)
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [ENTSO-E API Reference](https://documenter.getpostman.com/view/7009892/2s93JtP3F6)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
""")


