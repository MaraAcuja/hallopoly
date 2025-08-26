import streamlit as st
import pandas as pd
from datetime import datetime
import io

CSV_PATH_TRANSACTIONS = "transaktionen.csv"

def _ensure_transactions_df():
    if "df_transaktionen" not in st.session_state:
        try:
            df = pd.read_csv(CSV_PATH_TRANSACTIONS)
            # ensure expected columns
            expected = ["Gruppenname", "Betrag", "Verwendungszweck", "Zeitpunkt"]
            for c in expected:
                if c not in df.columns:
                    df[c] = ""
            st.session_state.df_transaktionen = df[expected].copy()
        except Exception:
            st.session_state.df_transaktionen = pd.DataFrame(columns=["Gruppenname", "Betrag", "Verwendungszweck", "Zeitpunkt"])

def _save_transactions():
    try:
        st.session_state.df_transaktionen.to_csv(CSV_PATH_TRANSACTIONS, index=False)
        return True, None
    except Exception as e:
        return False, str(e)

def record_transaction(gruppenname: str, betrag: float, verwendungszweck: str):
    _ensure_transactions_df()
    ts = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    new = {
        "Gruppenname": str(gruppenname),
        "Betrag": float(betrag),
        "Verwendungszweck": str(verwendungszweck),
        "Zeitpunkt": ts
    }
    st.session_state.df_transaktionen = pd.concat([st.session_state.df_transaktionen, pd.DataFrame([new])], ignore_index=True)
    ok, err = _save_transactions()
    return ok, err

def app():
    st.title("Transaktionen")

    _ensure_transactions_df()
    df = st.session_state.df_transaktionen

    st.markdown("Alle durchgeführten Transaktionen werden hier gelistet und in transaktionen.csv gespeichert.")

    # quick form to add a manual transaction (optional)
    with st.form("tx_form", clear_on_submit=True):
        cols = st.columns([2,1,2])
        with cols[0]:
            name = st.text_input("Gruppenname", value="", key="tx_name")
        with cols[1]:
            amount = st.number_input("Betrag (positiv=Eingang, negativ=Ausgang)", value=0.0, format="%.2f", key="tx_amount")
        with cols[2]:
            purpose = st.text_input("Verwendungszweck", value="", key="tx_purpose")
        submitted = st.form_submit_button("Transaktion hinzufügen")
        if submitted:
            if not name:
                st.error("Bitte Gruppenname angeben.")
            else:
                ok, err = record_transaction(name, amount, purpose)
                if ok:
                    st.success("Transaktion protokolliert.")
                else:
                    st.warning(f"Transaktion protokolliert, aber Fehler beim Speichern: {err}")

    st.markdown("---")
    st.subheader("Transaktionsliste")
    st.dataframe(df)

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("CSV herunterladen"):
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            st.download_button("Download CSV", data=buffer.getvalue().encode("utf-8"), file_name=CSV_PATH_TRANSACTIONS, mime="text/csv")
    with col2:
        if st.button("Export & Neu Laden"):
            ok, err = _save_transactions()
            if ok:
                st.success("Gespeichert.")
            else:
                st.error(f"Fehler beim Speichern: {err}")
            # reload from disk to reflect externally made changes
            try:
                st.session_state.df_transaktionen = pd.read_csv(CSV_PATH_TRANSACTIONS)
            except Exception:
                pass

