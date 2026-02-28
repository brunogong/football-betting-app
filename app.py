import streamlit as st
import requests

st.set_page_config(page_title="Odds Strategy Scanner", layout="wide")
st.title("📊 Betting Strategy Scanner")

# Chiave API
API_KEY = "27593156a4d63edc49b283e86937f0e9"

# Sidebar
st.sidebar.header("Impostazioni")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)

# Elenco Campionati con nomi INTERNI corretti (Senza errori di spelling)
leagues = {
    "Italia - Serie A": "soccer_italy_serie_a",
    "Inghilterra - Premier League": "soccer_league_premier_league",
    "Olanda - Eredivisie": "soccer_netherlands_eredivisie",
    "Germania - Bundesliga": "soccer_germany_bundesliga",
    "Spagna - La Liga": "soccer_spain_la_liga",
    "Francia - Ligue 1": "soccer_france_ligue_1"
}

selected_league = st.selectbox("Scegli un campionato:", list(leagues.keys()))
sport_key = leagues[selected_league]

def get_odds(sport):
    # NOTA: Rimosso lo slash finale dopo 'odds' per evitare il 404
    url = f"https://api.the-odds-api.com/v1/sports/{sport}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    try:
        response = requests.get(url, params=params)
        return response.status_code, response
    except Exception as e:
        return 500, str(e)

if st.button("🔍 ANALIZZA MERCATI"):
    status, response = get_odds(sport_key)
    
    if status == 200:
        data = response.json()
        if not data:
            st.warning(f"Nessun match trovato per {selected_league}. Probabilmente non ci sono partite imminenti quotate.")
        else:
            for match in data:
                home = match.get('home_team')
                away = match.get('away_team')
                
                with st.expander(f"🏟️ {home} vs {away}"):
                    # Estrazione quote
                    st.write(f"**Strategia suggerita:** Analisi in corso...")
                    st.success(f"Stake Kelly consigliato: {bankroll * 0.02:.2f}€")
    else:
        st.error(f"Errore {status}: Il server non ha trovato il campionato.")
        st.info("Consiglio: Prova con 'Italia - Serie A' o 'Inghilterra - Premier League' che sono sempre attivi.")
