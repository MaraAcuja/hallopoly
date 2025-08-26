import streamlit as st
import pandas as pd

# CSV paths
CSV_PATH = 'strassen.csv'
GROUPS_CSV_PATH = 'gruppen.csv'

def go_to_map():
    st.session_state.page = "Karte"

def load_df_wrapper(path):
    # wrapper to match hallopoly main loader behavior if not imported
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def app():
    st.title("Tabelle — Bearbeiten")

    # lade df und df_gruppen in session_state, falls nicht vorhanden
    if "df" not in st.session_state:
        try:
            st.session_state.df = load_df_wrapper(CSV_PATH)
        except Exception:
            st.session_state.df = pd.DataFrame()
    if "df_gruppen" not in st.session_state:
        try:
            st.session_state.df_gruppen = pd.read_csv(GROUPS_CSV_PATH)
        except Exception:
            st.session_state.df_gruppen = pd.DataFrame(columns=['name', 'token', 'vermoegen', 'immobilien_list', 'anzahl_immobilien'])

    st.markdown("Die Tabellen sind editierbar. Änderungen mit 'Speichern' dauerhaft in CSV schreiben.")

    # --- df_gruppen Editor ---
    st.subheader("Gruppen (df_gruppen)")
    groups_df = st.session_state.df_gruppen

    try:
        edited_groups = st.data_editor(groups_df, num_rows="dynamic", key="editor_groups")
        if not edited_groups.equals(groups_df):
            st.session_state.df_gruppen = edited_groups.copy()
            st.session_state.groups_edited = True
    except Exception:
        st.warning("st.data_editor für Gruppen nicht verfügbar — zeige Tabelle read-only.")
        st.dataframe(groups_df)

    gcol1, gcol2, gcol3 = st.columns([1,1,1])
    with gcol1:
        if st.button("Gruppen speichern", key="save_groups"):
            try:
                st.session_state.df_gruppen.to_csv(GROUPS_CSV_PATH, index=False)
                st.success(f"Gruppen gespeichert nach {GROUPS_CSV_PATH}")
                st.session_state.groups_edited = False
            except Exception as e:
                st.error(f"Fehler beim Speichern der Gruppen: {e}")
    with gcol2:
        if st.button("Gruppen zurücksetzen", key="reset_groups"):
            try:
                st.session_state.df_gruppen = pd.read_csv(GROUPS_CSV_PATH)
                st.session_state.groups_edited = False
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Zurücksetzen der Gruppen: {e}")
    with gcol3:
        if st.button("Zur Karte (von Gruppen)", key="groups_to_map"):
            go_to_map()
            st.rerun()

    if st.session_state.get("groups_edited"):
        st.info("Ungespeicherte Änderungen in Gruppen vorhanden.")
    else:
        st.success("Keine ungespeicherten Änderungen in Gruppen.")

    st.markdown("---")

    # --- Haupt-DF Editor (dein ursprünglicher df) ---
    st.subheader("Orte (df)")

    df = st.session_state.df

    try:
        edited = st.data_editor(df, num_rows="dynamic", key="editor_places")
        # mark edited
        if not edited.equals(df):
            st.session_state.edited = True
            st.session_state.df = edited.copy()
    except Exception:
        st.warning("st.data_editor nicht verfügbar — Fallback: geeignete Änderungen nicht vollständig unterstützt.")
        st.dataframe(df)
        st.markdown("Fallback-Modus: Lade die CSV extern, bearbeite und lade neu.")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("Speichern", key="save_places"):
            try:
                st.session_state.df.to_csv(CSV_PATH, index=False)
                st.success(f"Gespeichert nach {CSV_PATH}")
                # if there's a cached loader in main app, it should be cleared there;
                # here we just mark edited False
                st.session_state.edited = False
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")

    with col2:
        if st.button("Zurücksetzen", key="reset_places"):
            try:
                st.session_state.df = load_df_wrapper(CSV_PATH)
                st.session_state.edited = False
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Zurücksetzen: {e}")

    with col3:
        if st.button("Zur Karte", key="places_to_map"):
            go_to_map()
            st.rerun()

    # show a small status
    if st.session_state.get("edited"):
        st.info("Es gibt ungespeicherte Änderungen.")
    else:
        st.success("Alle Änderungen gespeichert oder keine Änderungen vorhanden.")

