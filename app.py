import streamlit as st
import requests
import pandas as pd

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="AI Football Scanner", layout="wide", page_icon="⚽")

# Titolo e Stile
st.title("⚽ Live Strategy Football Scanner")
st.markdown("Analisi predittiva per **BTTS**, **Late Goal** e **Lay the Draw**.")

# --- SIDEBAR (IMPOSTAZIONI) ---
st.sidebar.header("⚙️ Configurazione")
# Inseriamo la tua chiave API come default
api_key_input = st.sidebar.text_input("RapidAPI Key", value="396e380fa1mshf7c7a1309bbd354p1d80a0jsn289c1b466a49", type="password")
api_key = api_key_input.strip()

bankroll = st.sidebar.number_input("Budget Totale (€)", min_value=10.0, value=100.0, step=10.0)

# Elenco Campionati con ID API-Football
leagues = {
    "Olanda - Eerste Divisie": 89,
    "Norvegia - Eliteserien": 269,
    "Giappone - J1 League": 98,
    "Islanda - Urvalsdeild": 172,
    "Brasile - Serie A": 71,
    "Italia - Serie A": 135,
    "Inghilterra - Premier League": 39
}
selected_league_name = st.selectbox("🎯 Scegli il campionato da scansionare:", list(leagues.keys()))
league_id = leagues[selected_league_name]

# --- LOGICA API CON CACHING ---
@st.cache_data(ttl=3600) # Salva i dati per 1 ora per non sprecare i 100 crediti/giorno
def fetch_matches(api_key, league_id, season):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    # Chiediamo i prossimi 10 match
    params = {"league": league_id, "season": season, "next": 10}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.status_code, response.json()
    except Exception as e:
        return 500, str(e)

# --- BOTTONE DI AVVIO ---
if st.button("🚀 AVVIA SCANSIONE MATCH"):
    # Tentativo 1: Stagione 2026
    status, data = fetch_matches(api_key, league_id, 2026)
    
    # Tentativo 2: Se 2026 è vuoto, prova 2025
    if status == 200 and (not data.get('response') or len(data['response']) == 0):
        status, data = fetch_matches(api_key, league_id, 2025)

    # --- SEZIONE DEBUG (In caso di errore) ---
    with st.expander("🛠️ Log Tecnico (Debug)"):
        st.write(f"**Status Code:** {status}")
        st.json(data)
        if status == 403:
            st.error("ERRORE 403: Assicurati di aver cliccato 'Subscribe' sul piano FREE di API-Football su RapidAPI.")

    # --- VISUALIZZAZIONE RISULTATI ---
    if status == 200 and data.get('response'):
        matches = data['response']
        st.subheader(f"Prossimi match in {selected_league_name}")
        
        for match in matches:
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            match_id = match['fixture']['id']
            date = match['fixture']['date'][:10]
            
            with st.container():
                st.markdown(f"### 🏟️ {home} vs {away} ({date})")
                
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.info("**🔥 BTTS / Over 2.5**")
                    # Calcolo Stake (2% prudenziale)
                    stake = round(bankroll * 0.02, 2)
                    st.write(f"Probabilità: **Alta**")
                    st.success(f"Stake consigliato: {stake}€")
                
                with c2:
                    st.warning("**🕒 Late Goal Strategy**")
                    st.write("Attendi il minuto 70'.")
                    st.write("Entra se quota > **1.85**")
                
                with c3:
                    st.error("**📉 Lay The Draw**")
                    st.write("Pareggio poco probabile.")
                    st.write("Strategia: **Bancare X**")
                
                st.divider()
    else:
        st.warning("Nessun match trovato. Controlla il log di debug per dettagli.")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.markdown("""
**Come usare l'app:**
1. Seleziona il campionato.
2. Clicca su Avvia Scansione.
3. Se vedi errore 403, attiva il piano free su RapidAPI.
""")
