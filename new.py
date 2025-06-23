import streamlit as st
import pandas as pd
 
data = pd.DataFrame({"lat":[28.6139,19.0760,13.0827],
                     "lon":[77.2090,72.8777,80.2707]})
 
 
 
# Dummy wrapper *before* the map
st.markdown('<div class="map-container"></div>', unsafe_allow_html=True)
 
# The actual map
st.map(data, use_container_width=True)
 
# Style "the div that follows .map-container"
st.markdown("""
<style>
.map-container + div [data-testid="stDeckGlJsonChart"] {
    padding:60px;
    background:#f9f9f9;
    border:2px solid #000;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)