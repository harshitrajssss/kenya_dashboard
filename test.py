import streamlit as st
import pyodbc
import pandas as pd

# Title
st.title("SPC Dashboard")

# Database connection details
server = "10.200.202.124"
database = "SMARTMESBTP"
username = "jkuserBTP"
password = "jkBTP@474"

# Function to get data from SQL Server
@st.cache_data(show_spinner="Connecting to database...")
def load_data():
    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql("SELECT TOP 1000 * FROM paintingDatanew", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Database connection failed:\n{e}")
        return pd.DataFrame()

# Load the data
df = load_data()

# Show data
if not df.empty:
    st.success("✅ Data loaded successfully!")
    st.write(df.head())
else:
    st.warning("⚠ No data to display.")
