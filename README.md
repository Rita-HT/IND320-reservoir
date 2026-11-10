# IND320 – Reservoir and electricity Data

This repository contains the Streamlit app developed for the IND320 course at NMBU.

**App:** https://ind320reservoir.streamlit.app/

## Project files

* `app.py` – Starts the Streamlit app.
* `pages/` – Contains the different pages where users can explore the data and results, including reservoir data, visualisations, energy flow, STL, spectrograms and weather anomalies.
* `nve_data.py` – Handles the downloading of reservoir data from NVE.
* `data_quality.py` – Contains the code used for analysing data quality, including outliers, anomalies, STL and spectrograms.
* `data/locations.json` – Contains the coordinates used when collecting weather data.
* `notebooks/` – Contains the notebooks used during the project.
* `screencasts/` – Contains recordings showing the project.
* `archive/` – Stores files from earlier work.

## Data sources

The project uses data from the following sources:

* NVE Reservoir Statistics API for reservoir filling data.
* ENTSO-E Transparency Platform for electricity transfer data.
* Open-Meteo Historical Weather API (ERA5) for weather data.
* NVE Atlas for the region shapefiles.
