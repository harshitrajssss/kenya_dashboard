# bar_click_demo.py
import streamlit as st
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.set_page_config(layout="centered")
st.title("Click a Bar – demo")

# -------- create an obvious bar chart --------
bins = ["0-20", "20-40", "40-60", "60-80", "80-100"]
values = [5, 12, 8, 6, 3]                 # dummy counts

fig = px.bar(x=bins, y=values,
             labels={"x": "AWS bin", "y": "Count"},
             text=values,
             height=400)
fig.update_traces(marker_color="#0081fa", textposition="outside")

# -------- capture click ----------------------
click = plotly_events(fig, click_event=True,
                      select_event=False, hover_event=False,
                      key="bar_click")

# -------- show the figure --------------------
st.plotly_chart(fig, use_container_width=True)

# -------- raw click payload ------------------
st.write("**Raw click list:**", click)
