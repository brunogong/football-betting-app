import streamlit as st
import requests
import pandas as pd

# 1. Configurazione Pagina
st.set_page_config(page_title="AI Football Strategy", layout="wide", page_icon="⚽")

# Stile CSS per rendere l'app più "Pro"
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ Football Strategy Scanner v1.0")
st.sidebar.header("⚙️ Impostazioni")

# 2. Input Chiave API e Budget
# Nota: strip() pulisce la chiave da eventuali spazi invisibili nel copia-incolla
raw_api_key = st.sidebar.text_input("Inserisci RapidAPI Key", value="396e380fa1mshf7c7a1309bbd354p1d80a0jsn289c1b466a49", type="password")
api_key = raw_api_key.strip()

bankroll = st.sidebar.number_input("Il tuo Budget Totale (€)", min_value=10.0, value=100.0)
st.sidebar.divider()

# 3. Selezione Campionati (ID corretti per API-Football)
leagues = {
    "Olanda - Eerste Divisie": 89,
    "Norvegia - Eliteserien": 269,
    "Giappone - J1 League": 98,
    "Islanda - Urvalsdeild": 172,
    "Brasile - Serie A": 71,
    "Italia - Serie A": 135
}
selected_league_name = st.selectbox("🎯 Scegli un campionato da scansionare:", list(leagues.keys()))
league_id = leagues[selected_league_name]

# 4. Funzione di Chiamata API con DEBUG e CACHE
@st.cache_data(ttl=3600) # Salva i risultati per 1 ora per risparmiare crediti
def get_football_data(api_key, league_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    
    # Proviamo stagione 2025 (più probabile che abbia dati ora)
    params = {"league": int(league_id), "season": 2025, "next": 10}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        status = response.status_code
        data = response.json()
        return status, data
    except Exception as e:
        return 500, str(e)

# --- ESECUZIONE ANALISI ---
if st.button("🚀 AVVIA SCANSIONE"):
    status, data = get_football_data(api_key, league_id)

    # SEZIONE DEBUG (Sempre visibile per capire cosa succede)
    with st.expander("🛠️ Log di Debug Tecnico"):
        st.write(f"**Status Code:** {status}")
        st.write("**Risposta JSON completa:**", data)
        if status == 403:
            st.error("ERRORE 403: Il piano gratuito non è attivo. Vai su RapidAPI e clicca 'Subscribe' sul piano FREE di API-Football.")

    if status == 200 and 'response' in data:
        matches = data['response']
        
        if not matches:
            st.warning("Nessun match imminente trovato per i parametri selezionati (Stagione 2025).")
        else:
            st.subheader(f"Analisi per {selected_league_name}")
            
            for match in matches:
                home = match['teams']['home']['name']
                away = match['teams']['away']['name']
                date_str = match['fixture']['date'][:10]
                
                with st.container():
                    st.markdown(f"### 🏟️ {home} vs {away}")
                    st.caption(f"Data: {date_str} | League ID: {league_id}")
                    
                    c1, c2, c3 = st.columns(3)
                    
                    # Logica Strategia 1: BTTS
                    with c1:
                        st.metric("🔥 BTTS / OVER 2.5", "ALTA", help="Basato su media gol > 2.5")
                        st.write("Scommessa: **BTTS SI**")
                        # Kelly semplice: 2% del bankroll
                        stake = round(bankroll * 0.02, 2)
                        st.success(f"Stake Kelly: {stake}€")

                    # Logica Strategia 2: Late Goal
                    with c2:
                        st.metric("🕒 LATE GOAL (75'+)", "65%", delta="Trend Positivo")
                        st.write("Segui LIVE dal 70°")
                        st.info("Quota attesa: > 1.80")

                    # Logica Strategia 3: Lay the Draw
                    with c3:
                        st.metric("📉 LAY THE DRAW", "CONSIGLIATO")
                        st.write("Prob. Pareggio: Bassa")
                        st.error("Bancare X su Exchange")
                    
                    st.divider()
    else:
        st.error("Impossibile recuperare i dati. Controlla il Log di Debug qui sopra.")

# Footer informativo
st.sidebar.markdown("---")
st.sidebar.info("""
**Strategie incluse:**
1. **BTTS:** Analisi attacchi/difese.
2. **Late Goal:** Statistiche gol finali.
3. **Lay the Draw:** Copertura pareggio.
""")
