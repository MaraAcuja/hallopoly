import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
import math

# helper: haversine
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def go_to_details(idx):
    st.session_state.selected_idx = int(idx)
    st.session_state.page = "Details"

def app():
    st.title("Karte — Sehenswürdigkeiten um den Marktplatz")

    # ensure df_gruppen in session
    if "df_gruppen" not in st.session_state:
        st.session_state.df_gruppen = st.session_state.get("df_gruppen", None)

    with st.form("pw_form", clear_on_submit=False):
        cols = st.columns([3,1,2])
        with cols[0]:
            pw_input = st.text_input("Passwort", value="", key="pw_input")
        with cols[1]:
            submit = st.form_submit_button("Senden")
        with cols[2]:
            if st.session_state.get("greeting"):
                st.info(st.session_state["greeting"])

        if submit:
            entered = (pw_input or "").strip()
            if entered.upper() == "BERLIN":
                st.session_state.page = "Tabelle"
                st.rerun()
            else:
                match = None
                try:
                    groups = st.session_state.get("df_gruppen", None)
                    matched_rows = groups[groups["token"].astype(str) == str(entered)] if groups is not None else None
                    if matched_rows is not None and not matched_rows.empty:
                        match = matched_rows.iloc[0]
                except Exception as e:
                    st.error(f"Fehler beim Prüfen der Gruppe: {e}")
                    match = None

                if match is not None:
                    grp = {
                        "name": match["name"],
                        "token": match["token"],
                        "vermoegen": match.get("vermoegen", ""),
                        "immobilien_list": match.get("immobilien_list", ""),
                        "anzahl_immobilien": match.get("anzahl_immobilien", "")
                    }
                    st.session_state["current_group"] = grp
                    st.session_state.greeting = f"Hallo {grp['name']}"
                    st.success(st.session_state.greeting)
                    st.write(f"Vermögen: {grp['vermoegen']}")
                    imm_raw = grp["immobilien_list"]
                    if isinstance(imm_raw, str):
                        imm_list = [s.strip() for s in imm_raw.split(",") if s.strip()]
                    else:
                        try:
                            imm_list = list(imm_raw)
                        except Exception:
                            imm_list = [str(imm_raw)]
                    if imm_list:
                        st.write("Immobilien:")
                        for it in imm_list:
                            st.write(f"- {it}")
                    else:
                        st.write("Keine Immobilien gelistet.")
                else:
                    if entered == "abcde":
                        st.session_state.greeting = "Hallo Gruppe1"
                        st.info(st.session_state.greeting)
                        st.session_state.current_group = {"name": "Gruppe1"}
                    else:
                        st.session_state.greeting = None
                        st.session_state.current_group = None
                        st.warning("Falsches Passwort / Token nicht gefunden.")

    if st.session_state.get("current_group"):
        cg = st.session_state["current_group"]
        st.markdown("---")
        st.write(f"Angemeldet: **{cg.get('name','-')}** — Vermögen: {cg.get('vermoegen','-')}")
        st.markdown("---")

    df = st.session_state.get("df", None)
    if df is None or df.empty:
        st.info("Keine Daten vorhanden.")
        return

    center_lat = df.loc[0, "Latitude"]
    center_lon = df.loc[0, "Longitude"]
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    for i, row in df.iterrows():
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            tooltip=f"{i}. {row['Straße']}",
            popup=f"{i}. {row['Straße']}",
            icon=folium.Icon(color="red")
        ).add_to(m)

    for i, row in df.iterrows():
        folium.map.Marker(
            [row["Latitude"], row["Longitude"]],
            icon=DivIcon(
                icon_size=(20,20),
                icon_anchor=(10,10),
                html=f'<div style="font-size:10px;color:black;background:white;border-radius:10px;padding:2px 5px;">{i}</div>'
            )
        ).add_to(m)

    map_data = st_folium(m, width="100%", height=650)

    if map_data:
        clicked = map_data.get("last_object_clicked") or map_data.get("last_clicked")
        if clicked and isinstance(clicked, dict):
            lat = clicked.get("lat")
            lng = clicked.get("lng")
            if lat is not None and lng is not None:
                dists = df.apply(lambda r: haversine_km(lat, lng, r["Latitude"], r["Longitude"]), axis=1)
                idx = int(dists.idxmin())
                if dists.iloc[idx] < 0.15:
                    go_to_details(idx)
                    st.rerun()

