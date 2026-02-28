import streamlit as st
import requests

st.set_page_config(page_title="AI Strategy Scanner v4", layout="wide")
st.title("⚽ Live Strategy Scanner (v4 Engine)")

# --- CHIAVE API ---
API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- SIDEBAR ---
st.sidebar.header("Impostazioni")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)

# --- 1. FUNZIONE PER TROVARE I CAMPIONATI (v4) ---
@st.cache_data(ttl=3600)
def get_active_leagues():
    # Nota l'aggiunta di /v4/ nell'URL
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            all_sports = response.json()
            # Filtriamo solo il calcio (soccer)
            soccer_leagues = {s['title']: s['key'] for s in all_sports if s.get('group') == "Soccer"}
            return soccer_leagues
        else:
            st.error(f"Errore v4: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Errore Connessione: {e}")
        return {}

# --- 2. FUNZIONE PER RECUPERARE LE QUOTE (v4) ---
def get_odds(sport_key):
    # Endpoint aggiornato alla v4
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
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
    st.warning("Nessun campionato trovato. Verifica se la tua chiave API v4 è attiva.")
else:
    selected_name = st.selectbox("🎯 Scegli un campionato attivo:", list(active_leagues.keys()))
    sport_key = active_leagues[selected_name]

    if st.button("🚀 SCANSIONA MATCH"):
        status, data = get_odds(sport_key)
        
        if status == 200:
            if not data:
                st.warning(f"Nessun match quotato per {selected_name}.")
            else:
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
                            st.write("Verifica quote su Exchange.")
        else:
            st.error(f"Errore {status}: {data}")

st.sidebar.divider()
st.sidebar.caption("L'app ora utilizza il motore v4 di The Odds API.")
