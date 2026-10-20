#Import needed libraries 
import pandas as pd
import requests
import streamlit as st
 
# Web address of the NVE reservoir API
NVE_URL = (
    "https://biapi.nve.no/magasinstatistikk/"
    "api/Magasinstatistikk/HentOffentligData"
)
 
#  Norwegian column names to English names
RENAME_MAP = {
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
    "endring_fyllingsgrad": "Diff_Fill_lvl",
}
 
# The columns that contain numbers (numeric columns)
NUMERIC_COLUMNS = [
    "Fill_lvl", "Capacity_TWh", "Fill_TWh", "Fill_lvl_Lstweek", "Diff_Fill_lvl",
]
 
 
def month_options():
    # Makes a list of all months from 1995-01 until this month
    return [str(p) for p in pd.period_range(
        "1995-01", pd.Timestamp.today().to_period("M"), freq="M")]
 
 
def interval_slider():
    # Slider where the user picks the download interval (start and end month)
    options = month_options()
    # Use the earlier choice if there is one, otherwise the last 5 years
    default = st.session_state.get("nve_interval", (options[-60], options[-1]))
    start, end = st.select_slider(
        "Download interval", options=options, value=default)
    # Remember the choice, so page 2 and page 3 use the same interval
    st.session_state["nve_interval"] = (start, end)
    return start, end
 
 
@st.cache_data(ttl=3600)  # keep the result for 1 hour, so we do not download again
def load_data(start_month, end_month):

    # Download the data from the NVE AP, we download everything and only the months the user picked.
    response = requests.get(NVE_URL, timeout=30)
    response.raise_for_status()
    data = pd.DataFrame(response.json()).rename(columns=RENAME_MAP)
 
    # Check columns exist
    required = ["Date", "Area_type", "Area_number", "Fill_lvl"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError("Missing expected NVE columns: " + ", ".join(missing))
 
    # Time columns, missing values are turned into NaT (missing date).
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    if "Nxt_pubDate" in data.columns:
        data["Nxt_pubDate"] = pd.to_datetime(data["Nxt_pubDate"], errors="coerce")
 
    # Make sure the number columns really are numeric
    for column in NUMERIC_COLUMNS:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
 
    # Remove rows with missing values 
    # (after that, a missing value would become the text "nan")
    data = data.dropna(subset=["Date", "Area_type", "Area_number"]).copy()
 
    # Make text columns, and one column that names each area (for example EL1)
    data["Area_type"] = data["Area_type"].astype(str).str.strip()
    data["Area_number"] = data["Area_number"].astype(str)
    data["Area"] = data["Area_type"] + data["Area_number"]
    data["Month"] = data["Date"].dt.to_period("M").astype(str)
 
    # Keep only the months the user picked
    data = data[(data["Month"] >= start_month) & (data["Month"] <= end_month)]
    return data.sort_values(["Area", "Date"])
 
