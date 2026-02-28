import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="AI Football Strategy", layout="wide")
st.title("⚽ Football Strategy Scanner")

# Sidebar
api_key = st.sidebar.text_input("RapidAPI Key", value="396e380fa1mshf7c7a1309bbd354p1d80a0jsn289c1b466a49", type="password")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)

leagues = {
    "Olanda - Eerste Divisie": 89,
    "Norvegia - Eliteserien": 269,
    "Giappone - J1 League": 98,
    "Islanda - Urvalsdeild": 172,
    "Brasile - Serie A": 71
}
selected_league_name = st.selectbox("Scegli un campionato:", list(leagues.keys()))
league_id = leagues[selected_league_name]

# --- FUNZIONE API REALE ---
def get_real_data(league_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    # Prendiamo i prossimi 10 match del campionato scelto
    params = {"league": league_id, "season": 2026, "next": 10}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['response']
    else:
        st.error("Errore API: Controlla la chiave o i crediti.")
        return []

# --- LOGICA DI VISUALIZZAZIONE ---
matches = get_real_data(league_id)

if matches:
    st.subheader(f"Prossimi Match: {selected_league_name}")
    
    # Creiamo una riga per ogni match trovato
    for match in matches:
        home = match['teams']['home']['name']
        away = match['teams']['away']['name']
        date = match['fixture']['date'][:10] # Prende solo la data YYYY-MM-DD
        
        with st.expander(f"🏟️ {home} vs {away} ({date})"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Strategia BTTS**")
                st.info("Analisi trend in corso...") # Qui in futuro metteremo la logica statistica
            with c2:
                st.write("**Late Goal**")
                st.warning("Verifica quote live al 75'")
            with c3:
                st.write("**Stake Consigliato**")
                st.success(f"{(bankroll * 0.02):.2f}€ (2%)") # Stake prudenziale fisso
else:
    st.write("Nessun match trovato per questa selezione.")
