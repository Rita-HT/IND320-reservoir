import pandas as pd
import streamlit as st


# Leser inn data fra CSV
@st.cache_data
def load_data():
    data = pd.read_csv("reservoirs.csv")

    # Gir kolonnene engelske navn
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

    #Lager kolonne som viser området
    data["Area"] = (
        data["Area_type"] + data["Area_number"].astype(str)
    )

    #Omgjør datoen til datoformat
    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    #Kolonne som viser måned
    data["Month"] = data["Date"].dt.to_period("M")

    # Sorterer etter område og dato
    data = data.sort_values(["Area", "Date"])

    return data


# Leser data
data = load_data()

# Overskrift på siden
st.title("Reservoir")

# Gir valg om hvilket område som skal vises
selected_area = st.selectbox(
    "Area",
    sorted(data["Area"].unique()),
    index=0
)

 #Bare data fra området som ble valgt
area_data = data[data["Area"] == selected_area]

# Finner den første måneden i data
first_month = area_data["Month"].iloc[0]

#Kun dataene fra den første måneden
month_data = area_data[
    area_data["Month"] == first_month
]

# Finner kolonner som kun inneholder tall
numeric_columns = area_data.select_dtypes(
    include="number"
).columns

# Lager en rad for hver numeriske kolonne
data_table = {
    "Column": list(numeric_columns),
    f"First month ({first_month})": [
        month_data[column].tolist()
        for column in numeric_columns
    ],
}

# Viser tabellen med et lite linjediagram for hver rad
st.dataframe(
    data_table,
    column_config={
        f"First month ({first_month})":
            st.column_config.LineChartColumn(
                f"First month ({first_month})"
            )
    },
    hide_index=True,
    use_container_width=True,
)
