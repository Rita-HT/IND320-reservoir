
#Imports the library needed
import streamlit as st

# Display the project titles
st.title("IND320")
st.write("Project Work, Part 2 – Data Sources")

#Explain the purpose of the second project
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
- [ENTSO-E API Reference](https://documenter.getpostman.com/view/7009892/2s93JtP3F6)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
""")


