import streamlit as st
import pandas as pd

# statische Importe der Seitenmodule
import karte
import details
import tabelle

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
sel = st.sidebar.radio(
    "Seite",
    ["Karte", "Details", "Tabelle"],
    index=0 if st.session_state.page == "Karte" else (1 if st.session_state.page == "Details" else 2)
)
if sel != st.session_state.page:
    st.session_state.page = sel
    st.rerun()

# Mapping auf die app()-Funktionen der importierten Module
page_map = {
    "Karte": karte.app,
    "Details": details.app,
    "Tabelle": tabelle.app
}

# Aufruf der passenden Seite
# Fallback auf karte.app falls key fehlt
page_map.get(st.session_state.page, karte.app)()
