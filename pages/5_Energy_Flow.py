#Imports the libaries needed
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pymongo import MongoClient

#Titles of the page
st.title("Energy Flow in Norway")
st.write("Electricity transfers between Norway and neighbouring countries using ENTSO-E data.")
