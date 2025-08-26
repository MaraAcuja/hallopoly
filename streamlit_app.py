import streamlit as st
import pandas as pd
from importlib import import_module

st.set_page_config(page_title="Hallopoly", layout="wide")

# -- Daten: initial load function --
CSV_PATH_ROADS = 'strassen.csv'
CSV_PATH_GROUPS = 'gruppen.csv'

@st.cache_data(ttl=300)
def load_df(path):
    return pd.read_csv(path)

# load once and store in session_state
if "df_immobilien" not in st.session_state:
    st.session_state.df_immobilien = load_df(CSV_PATH_ROADS)
if "df_gruppen" not in st.session_state:
    st.session_state.df_gruppen = load_df(CSV_PATH_GROUPS)

# -- Session defaults --
if "page" not in st.session_state:
    st.session_state.page = "Karte"
if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0
if "df" not in st.session_state:
    st.session_state.df = st.session_state.df_immobilien.copy()
if "edited" not in st.session_state:
    st.session_state.edited = False

# Sidebar navigation (keeps UI consistent across pages)
st.sidebar.title("Navigation")
sel = st.sidebar.radio("Seite", ["Karte", "Details", "Tabelle"],
                       index=0 if st.session_state.page=="Karte" else (1 if st.session_state.page=="Details" else 2))
if sel != st.session_state.page:
    st.session_state.page = sel
    st.rerun()

# Simple page router: import the page modules and call their `app()` function
page_map = {
    "Karte": "karte",
    "Details": "details",
    "Tabelle": "tabelle"
}

module_name = page_map.get(st.session_state.page, "karte")
mod = import_module(module_name)
mod.app()
