import streamlit as st
import requests

st.set_page_config(page_title="AI Strategy Scanner", layout="wide")
st.title("⚽ Live Strategy Scanner v2.0")

# --- CHIAVE API ---
API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- SIDEBAR ---
st.sidebar.header("Impostazioni")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)

# --- 1. FUNZIONE PER TROVARE I CAMPIONATI ATTIVI ---
@st.cache_data(ttl=3600)
def get_active_leagues():
    url = "https://api.the-odds-api.com/v1/sports"
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            all_sports = response.json()
            # Filtriamo solo il calcio (soccer)
            soccer_leagues = {s['title']: s['key'] for s in all_sports if "soccer" in s['group'].lower()}
            return soccer_leagues
        return {}
    except:
        return {}

# --- 2. FUNZIONE PER RECUPERARE LE QUOTE ---
def get_odds(sport_key):
    # Endpoint corretto senza slash finale per evitare il 404
    url = f"https://api.the-odds-api.com/v1/sports/{sport_key}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    try:
        response = requests.get(url, params=params)
        return response.status_code, response.json()
    except Exception as e:
        return 500, str(e)

# --- INTERFACCIA ---
active_leagues = get_active_leagues()

if not active_leagues:
    st.error("Errore nel caricamento dei campionati. Verifica la tua chiave API o la connessione.")
else:
    selected_name = st.selectbox("🎯 Scegli un campionato attivo OGGI:", list(active_leagues.keys()))
    sport_key = active_leagues[selected_name]

    if st.button("🚀 SCANSIONA MATCH"):
        status, data = get_odds(sport_key)
        
        if status == 200:
            if not data:
                st.warning(f"Nessun match quotato al momento per {selected_name}.")
            else:
                st.subheader(f"Analisi: {selected_name}")
                for match in data:
                    home = match.get('home_team')
                    away = match.get('away_team')
                    
                    with st.expander(f"🏟️ {home} vs {away}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.info("**Strategia: Over 2.5 / BTTS**")
                            st.write(f"Stake consigliato: **{(bankroll * 0.02):.2f}€**")
                        with c2:
                            st.warning("**Strategia: Lay the Draw**")
                            st.write("Verificare quote su Exchange.")
        else:
            st.error(f"Errore {status}: Impossibile recuperare i match.")
            st.json(data) # Mostra l'errore tecnico per il debug

st.sidebar.divider()
st.sidebar.caption("L'app mostra solo i campionati che hanno partite quotate nelle prossime 48 ore.")
