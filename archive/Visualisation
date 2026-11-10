import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Leser inn CSV-filen
@st.cache_data
def load_data():
    data = pd.read_csv("reservoirs.csv")

    # Endrer til engelske navn
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

    # Kun kolonne som viser området
    data["Area"] = (
        data["Area_type"] + data["Area_number"].astype(str)
    )

    # Omgjør datoen til datoformat
    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    # Kolonne som viser måned
    data["Month"] = data["Date"].dt.to_period("M")

    # Sorterer etter område og dato
    data = data.sort_values(["Area", "Date"])

    return data


# Leser inn data
data = load_data()

# Overskrift på siden
st.title("Visualisation of the reservoir")

# Gir valg om hvilket område som skal vises
selected_area = st.selectbox(
    "Area",
    sorted(data["Area"].unique()),
    index=0
)

# Bare data fra området som ble valgt
area_data = data[data["Area"] == selected_area]

# Finner kolonner som kun inneholder tall
numeric_columns = [
    "Fill_lvl",
    "Capacity_TWh",
    "Fill_TWh",
    "Fill_lvl_Lstweek",
    "Diff_Fill_lvl"
]

# Gir valg om hvilken kolonne som skal vises
selected_column = st.selectbox(
    "Column",
    numeric_columns + ["All columns"]
)

#finner ledige måneder
months = sorted(
    area_data["Month"].dropna().unique()
)

#velger hvilke måneder som skal vises
start_month, end_month = st.select_slider(
    "Months",
    options=months,
    value=(months[0], months[0])
)

#velger data fra de valgte månedene
mask = (
    (area_data["Month"] >= start_month)
    & (area_data["Month"] <= end_month)
)

#skalerer verdiene dersom alle kolonner skal vises
if selected_column == "All columns":
    plot_data = (
        (area_data[numeric_columns] - area_data[numeric_columns].min())
        / (
            area_data[numeric_columns].max()
            - area_data[numeric_columns].min()
        )
    )

    columns_to_plot = numeric_columns
    y_label = "Normalised value (0-1)"

else:
    plot_data = area_data[[selected_column]]
    columns_to_plot = [selected_column]
    y_label = selected_column


# Plot
fig, ax = plt.subplots(figsize=(10, 5))

# Plotter valgt kolonne eller alle kolonner
for column in columns_to_plot:
    ax.plot(
        area_data.loc[mask, "Date"],
        plot_data.loc[mask, column],
        marker="o",
        label=column
    )

# lager overskrift og aksetitler
ax.set_title(
    f"{selected_column} - {selected_area} "
    f"({start_month} to {end_month})"
)
ax.set_xlabel("Date")
ax.set_ylabel(y_label)

# forklaring hvis flere kolonner er valgt
if len(columns_to_plot) > 1:
    ax.legend(fontsize=8)

# Justerer datoene
fig.autofmt_xdate()

#Fikser på layout
plt.tight_layout()

# Viser ploten
st.pyplot(fig)
