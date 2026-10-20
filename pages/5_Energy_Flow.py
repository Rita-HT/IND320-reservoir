#Libraries needed 
import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError
 
st.title("Energy Flow in Norway")
st.write("Electricity transfers between Norway and neighbouring areas (ENTSO-E data).")
 
# Connect to MongoDB (the password is kept in Streamlit Secrets)
try:
    mongo_uri = st.secrets["MONGODB_URI"]
except (KeyError, FileNotFoundError):
    st.error("The secret MONGODB_URI is missing. Add it in the Streamlit secrets.")
    st.stop()
 
 
@st.cache_resource  # one connection that is reused every time the page reruns
def get_collection(uri):
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    return client["ind320"]["entsoe_hourly"]
 
 
collection = get_collection(mongo_uri)
 
 
# Functions that read from MongoDB
@st.cache_data(ttl=3600)
def load_options():
    # Which connections and years are in the database?
    return sorted(collection.distinct("connection")), sorted(collection.distinct("year"))
 
 
@st.cache_data(ttl=3600)
def load_months(year):
    # Which months have data in this year?
    return sorted(collection.distinct("month", {"year": year}))
 
 
@st.cache_data(ttl=3600)
def load_totals(connection, year):
    # Add up the energy (MWh) for "out" and "in". MongoDB does the sum,
    # so we only get two numbers back.
    pipeline = [
        {"$match": {"connection": connection, "year": year}},
        {"$group": {"_id": "$direction", "total_mwh": {"$sum": "$mwh"}}},
    ]
    return {row["_id"]: row["total_mwh"] for row in collection.aggregate(pipeline)}
 
 
@st.cache_data(ttl=3600)
def load_hourly(year, months):
    # Get the hourly values for the chosen months
    cursor = collection.find(
        {"year": year, "month": {"$in": list(months)}},
        {"_id": 0, "connection": 1, "direction": 1, "timestamp_utc": 1, "mwh": 1},
    )
    df = pd.DataFrame(list(cursor))
    if df.empty:
        return df
    # Times are saved in UTC. Change them to Norwegian time for the plot.
    local = pd.to_datetime(df["timestamp_utc"], utc=True).dt.tz_convert("Europe/Oslo")
    df["time_local"] = local.dt.tz_localize(None)
    return df.sort_values(["connection", "direction", "time_local"])
 
 
# Find out what is in the database
try:
    connections, years = load_options()
except PyMongoError as error:
    st.error(f"Could not read from MongoDB: {error}")
    st.stop()
 
if not connections or not years:
    st.warning("The MongoDB collection is empty.")
    st.stop()
 
# Nice names for the plots
direction_names = {"out": "Out of Norway", "in": "Into Norway"}
month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
 
# Two columns: pie chart on the left, line plot on the right
left, right = st.columns(2)
 
# Left column: pie chart
with left:
    st.subheader("Total exchange in one year")
 
    # Radio buttons: choose the connection
    selected_connection = st.radio("Connection", connections)
 
    # Select box: choose the year (2025 is the default, it is a full year)
    default_index = years.index(2025) if 2025 in years else len(years) - 1
    selected_year = st.selectbox("Year", years, index=default_index)
 
    try:
        available_months = load_months(selected_year)
        totals = load_totals(selected_connection, selected_year)
    except PyMongoError as error:
        st.error(f"Could not read from MongoDB: {error}")
        st.stop()
 
    st.caption(f"{len(available_months)} of 12 months have data in {selected_year}.")
 
    if not totals:
        st.warning("No data for this connection and year.")
    else:
        # Change MWh to TWh (divide by 1,000,000)
        pie_data = pd.DataFrame({
            "Direction": [direction_names["out"], direction_names["in"]],
            "TWh": [totals.get("out", 0) / 1e6, totals.get("in", 0) / 1e6],
        })
        fig_pie = px.pie(
            pie_data, names="Direction", values="TWh", color="Direction",
            color_discrete_map={direction_names["out"]: "#ff7f0e",
                                direction_names["in"]: "#1f77b4"},
            title=f"{selected_connection}: total exchange in {selected_year}",
        )
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie)
 
# Right column: line plot
with right:
    st.subheader("Hourly exchange")
 
    if not available_months:
        st.warning("No months available.")
        st.stop()
 
    # Pills: choose one or more months
    # The key includes the year, so the choice resets when the year changes
    selected_months = st.pills(
        "Months",
        options=available_months,
        format_func=lambda month: month_names[month],
        selection_mode="multi",
        default=[available_months[0]],
        key=f"months_{selected_year}",
    )
 
    if not selected_months:
        st.info("Choose at least one month.")
    else:
        try:
            hourly = load_hourly(selected_year, tuple(sorted(selected_months)))
        except PyMongoError as error:
            st.error(f"Could not read from MongoDB: {error}")
            st.stop()
 
        if hourly.empty:
            st.warning("No data for these months.")
        else:
            month_text = ", ".join(month_names[m] for m in sorted(selected_months))
            # One line for each connection and direction
            # (solid line = out of Norway, dashed line = into Norway)
            fig_line = px.line(
                hourly, x="time_local", y="mwh",
                color="connection", line_dash="direction",
                line_dash_map={"out": "solid", "in": "dash"},
                labels={"time_local": "Time (Norwegian time)",
                        "mwh": "Energy per hour (MWh)",
                        "connection": "Connection",
                        "direction": "Direction"},
                title=f"Hourly exchange: {month_text} {selected_year}",
            )
            st.plotly_chart(fig_line)
            st.caption("Tip: choose fewer months to make the plot faster.")
 
# Data source

with st.expander("Data source"):
    st.markdown(
        "Data from the [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/): "
        "cross-border flows between Norway and its neighbours. "
        "The data was saved in Cassandra, averaged per hour with Spark, "
        "and stored in MongoDB."
    )
