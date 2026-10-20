#Imports the libaries needed
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pymongo import MongoClient

#Titles of the page, displays a short introduction 
st.title("Energy Flow in Norway")
st.write("Electricity transfers between Norway and neighbouring countries using ENTSO-E data.")

# Connects to my MongoDB from database and collection containing the ENTSO-E data
client = MongoClient(st.secrets["MONGODB_URI"])
collection = client["ind320"]["entsoe_hourly"]

# Loads the data from MongoDB, except  MongoDB _id 
data = list(collection.find({}, {"_id": 0}))
df = pd.DataFrame(data)

# Prepares records into dataframe  (to filter, group and visualise the data)
#Converts time to a datetimeformat to show year and month
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["year"] = df["timestamp"].dt.year
df["month"] = df["timestamp"].dt.month
