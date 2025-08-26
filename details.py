import streamlit as st
import pandas as pd
import transaktion


# Paths used for saving
CSV_PATH_ROADS = 'strassen.csv'
CSV_PATH_GROUPS = 'gruppen.csv'

def go_to_map():
    st.session_state.page = "Karte"

def go_to_table():
    st.session_state.page = "Tabelle"

def find_group_index_by_token(groups_df, token):
    if groups_df is None:
        return None
    mask = groups_df["token"].astype(str) == str(token)
    if mask.any():
        return groups_df.loc[mask].index[0]
    return None

def to_float_safe(x, default=0.0):
    try:
        return float(x or 0.0)
    except Exception:
        return default

def app():
    # Basic checks
    if "df" not in st.session_state or st.session_state["df"] is None or st.session_state["df"].empty:
        st.info("Keine Daten vorhanden.")
        return

    df = st.session_state.df
    idx = st.session_state.get("selected_idx", 0)
    try:
        idx = int(idx)
    except Exception:
        idx = 0
    if idx < 0 or idx >= len(df):
        idx = 0

    place = df.loc[idx]
    st.header(f"{idx}. {place.get('Straße', '-')}")
    file_name = f"{idx%3}.png"
    try:
        st.image(file_name, caption="Sunrise by the mountains")
    except Exception:
        st.info(f"Kein Bild: {file_name}")

    st.write(f"Kaufpreis: {place.get('Kaufpreis', 0)} Hall€")
    st.write(f"Mietpreis: {place.get('Mietpreis', 0)} Hall€")

    # current group and groups dataframe
    current = st.session_state.get("current_group")
    gruppen_angemeldet = current is not None
    groups_df = st.session_state.get("df_gruppen")

    # Token input (same field used for actions)
    token_key = f"token_{idx}"
    entered_token = (st.text_input("Token eingeben (für Details / Kauf / Miete)", key=token_key) or "").strip()
    expected_token = str(place.get("token", "")).strip()

    if expected_token == "":
        st.warning("Für diese Immobilie ist kein Token hinterlegt — manche Funktionen sind deaktiviert.")

    token_ok = (entered_token != "" and entered_token == expected_token)

    # ---- Verkaufsstatus nur sichtbar, wenn Gruppe angemeldet UND Token korrekt eingegeben ----
    verkauft_flag = bool(place.get("Verkauft", False))
    if not gruppen_angemeldet:
        st.info("Du bist nicht als Gruppe angemeldet — Details (inkl. Verkaufsstatus) nach Anmeldung sichtbar.")
    else:
        if not token_ok:
            st.info("Token nicht korrekt eingegeben — Verkaufsstatus erst nach korrekter Token-Eingabe sichtbar.")
        else:
            # token korrekt und gruppe angemeldet -> Verkaufsstatus anzeigen
            if not verkauft_flag:
                st.success("Diese Immobilie steht zum Verkauf.")
            else:
                st.error("Diese Immobilie wurde verkauft.")
                st.write(f"Aktuelle Besitzende Gruppe: {place.get('besitzt_von','Unbekannt')}")

    # Wenn Token korrekt und angemeldet, Aktionen erlauben.
    # Zusätzlich: ist Immobilie verkauft -> Miete wird AUTOMATISCH beim Betreten (nach Token-Eingabe) abgebucht.
    if token_ok and gruppen_angemeldet:
        # determine payer (angemeldete gruppe) index
        payer_token = current.get("token") if current else None
        payer_idx = find_group_index_by_token(groups_df, payer_token) if groups_df is not None else None

        # determine owner index
        owner_idx = None
        if str(place.get("token_owner","")).strip() != "" and groups_df is not None:
            owner_idx = find_group_index_by_token(groups_df, place.get("token_owner"))
        if owner_idx is None and str(place.get("besitzt_von","")).strip() != "" and groups_df is not None:
            mask_name = groups_df["name"].astype(str) == str(place.get("besitzt_von",""))
            if mask_name.any():
                owner_idx = groups_df.loc[mask_name].index[0]

        # --- Automatische Mietzahlung, wenn verkauft ---
        if verkauft_flag:
            if payer_idx is None:
                st.error("Angemeldete Gruppe nicht in Gruppenliste gefunden — Miete nicht möglich.")
            elif owner_idx is None:
                st.error("Besitzende Gruppe nicht in Gruppenliste gefunden — Miete nicht möglich.")
            else:
                mietpreis = to_float_safe(place.get("Mietpreis", 0))
                try:
                    payer_verm = to_float_safe(groups_df.at[payer_idx, "vermoegen"], to_float_safe(current.get("vermoegen",0)))
                except Exception:
                    payer_verm = to_float_safe(current.get("vermoegen",0))
                try:
                    owner_verm = to_float_safe(groups_df.at[owner_idx, "vermoegen"], 0.0)
                except Exception:
                    owner_verm = 0.0

                # Prüfe, ob bereits in dieser Session die Miete für genau diese Immobilie abgebucht wurde,
                # um Doppelabbuchungen beim Rerun zu vermeiden.
                paid_key = f"paid_rent_{idx}_{payer_idx}"
                already_paid = st.session_state.get(paid_key, False)

                st.write(f"Dein Vermögen: {payer_verm} Hall€ — Vermögen des Besitzers: {owner_verm} Hall€")
                if already_paid:
                    st.info("Miete für diese Immobilie wurde in dieser Sitzung bereits abgebucht.")
                else:
                    if payer_verm < mietpreis:
                        st.error("Unzureichendes Vermögen zum Bezahlen der Miete. Zahlung nicht durchgeführt.")
                    else:
                        # führe Zahlung durch (Session + DataFrame) und versuche zu speichern
                        groups_df.at[payer_idx, "vermoegen"] = payer_verm - mietpreis
                        groups_df.at[owner_idx, "vermoegen"] = owner_verm + mietpreis
                        st.session_state["df_gruppen"] = groups_df
                        if "current_group" in st.session_state:
                            st.session_state["current_group"]["vermoegen"] = groups_df.at[payer_idx, "vermoegen"]
                        # mark as paid in this session to avoid duplicates
                        # existing updates...
                        st.session_state[paid_key] = True
                        try:
                            groups_df.to_csv(CSV_PATH_GROUPS, index=False)
                        except Exception as e:
                            st.warning(f"Zahlung durchgeführt, aber Fehler beim Speichern der Gruppen: {e}")
                        # new: record transaction
                        transaktion.record_transaction(
                            gruppenname=groups_df.at[payer_idx, "name"],
                            betrag=-mietpreis,
                            verwendungszweck=f"Miete für {place.get('Straße','')}"
                        )
                        st.success(f"Miete von {mietpreis} Hall€ automatisch bezahlt an {groups_df.at[owner_idx,'name']}.")

        # --- Kaufmöglichkeit (nur sichtbar wenn Immobilie noch frei) ---
        if not verkauft_flag:
            if expected_token == "":
                st.info("Diese Immobilie hat keinen Token hinterlegt — Kauf nicht möglich.")
            else:
                if st.button("Immobilie kaufen"):
                    if not token_ok:
                        st.error("Falscher oder leerer Token — Kauf abgebrochen.")
                    else:
                        groups_df = st.session_state.get("df_gruppen")
                        places_df = st.session_state.get("df")
                        gruppen_info = current
                        group_token = gruppen_info.get("token") if gruppen_info else None
                        if group_token is None:
                            st.error("Angemeldete Gruppe hat kein Token — Kauf abgebrochen.")
                        else:
                            mask = groups_df["token"].astype(str) == str(group_token)
                            if not mask.any():
                                st.error("Angemeldete Gruppe nicht in df_gruppen gefunden. Kauf abgebrochen.")
                            else:
                                gi = groups_df.loc[mask].index[0]
                                cur_verm = to_float_safe(groups_df.at[gi, "vermoegen"], to_float_safe(gruppen_info.get("vermoegen",0)))
                                kaufpreis = to_float_safe(place.get("Kaufpreis", 0))
                                if cur_verm < kaufpreis:
                                    st.error("Unzureichendes Vermögen zum Kauf dieser Immobilie.")
                                else:
                                    try:
                                        imm_raw = groups_df.at[gi, "immobilien_list"]
                                        if pd.isna(imm_raw) or imm_raw == "":
                                            imm_list = []
                                        elif isinstance(imm_raw, str) and imm_raw.strip().startswith("["):
                                            import json
                                            try:
                                                imm_list = json.loads(imm_raw)
                                            except Exception:
                                                imm_list = [s.strip() for s in imm_raw.split(",") if s.strip()]
                                        elif isinstance(imm_raw, str):
                                            imm_list = [s.strip() for s in imm_raw.split(",") if s.strip()]
                                        else:
                                            try:
                                                imm_list = list(imm_raw)
                                            except Exception:
                                                imm_list = [str(imm_raw)]

                                        neue_strasse = str(place["Straße"])
                                        imm_list.append(neue_strasse)
                                        groups_df.at[gi, "immobilien_list"] = ", ".join(imm_list)
                                        if "anzahl_immobilien" in groups_df.columns:
                                            try:
                                                groups_df.at[gi, "anzahl_immobilien"] = int(groups_df.at[gi, "anzahl_immobilien"]) + 1
                                            except Exception:
                                                groups_df.at[gi, "anzahl_immobilien"] = len(imm_list)

                                        groups_df.at[gi, "vermoegen"] = cur_verm - kaufpreis
                                        places_df.at[idx, "Verkauft"] = True
                                        if "besitzt_von" not in places_df.columns:
                                            places_df["besitzt_von"] = ""
                                        group_name = gruppen_info.get("name", "")
                                        places_df.at[idx, "besitzt_von"] = group_name

                                        st.session_state["df_gruppen"] = groups_df
                                        st.session_state["df"] = places_df
                                        if "current_group" in st.session_state:
                                            st.session_state["current_group"]["vermoegen"] = groups_df.at[gi, "vermoegen"]
                                            st.session_state["current_group"]["immobilien_list"] = groups_df.at[gi, "immobilien_list"]

                                        try:
                                            groups_df.to_csv(CSV_PATH_GROUPS, index=False)
                                            places_df.to_csv(CSV_PATH_ROADS, index=False)
                                            st.success(f"Immobilie '{neue_strasse}' erfolgreich gekauft von Gruppe '{group_name}'. Änderungen gespeichert.")
                                            # after successful purchase persistence:
                                            transaktion.record_transaction(
                                                gruppenname=groups_df.at[gi, "name"],   # Käufer
                                                betrag=-kaufpreis,
                                                verwendungszweck=f"Kauf: {place.get('Straße','')}"
                                            )
                                            # optional: record seller income if seller known
                                            if owner_idx is not None:
                                                transaktion.record_transaction(
                                                    gruppenname=groups_df.at[owner_idx, "name"],
                                                    betrag=+kaufpreis,
                                                    verwendungszweck=f"Verkaufserlös: {place.get('Straße','')}"
                                                )

                                        except Exception as e:
                                            st.warning(f"Kauf durchgeführt, aber Fehler beim Speichern: {e}")
                                            st.success(f"Immobilie '{neue_strasse}' erfolgreich gekauft von Gruppe '{group_name}'.")
                                    except Exception as e:
                                        st.error(f"Fehler beim Durchführen des Kaufs: {e}")

    st.markdown("---")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Zurück zur Karte"):
            go_to_map()
            st.experimental_rerun()
    with col2:
        if st.button("Zur Tabelle"):
            go_to_table()
            st.experimental_rerun()

