import streamlit as st
import requests

st.set_page_config(page_title="Odds Strategy Scanner", layout="wide")
st.title("📊 Betting Strategy Scanner")

# Chiave API
API_KEY = "27593156a4d63edc49b283e86937f0e9"

# Sidebar
st.sidebar.header("Impostazioni")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)

# Elenco Campionati AGGIORNATO (Nomi tecnici corretti per The Odds API)
leagues = {
    "Italia - Serie A": "soccer_italy_serie_a",
    "Inghilterra - Premier League": "soccer_league_premier_league",
    "Olanda - Eredivisie": "soccer_netherlands_eredivisie",
    "Norvegia - Eliteserien": "soccer_norway_eliteserien",
    "Brasile - Serie A": "soccer_brazil_campeonato",
    "Giappone - J1 League": "soccer_japan_j_league"
}

selected_league = st.selectbox("Scegli un campionato:", list(leagues.keys()))
sport_key = leagues[selected_league]

def get_odds(sport):
    url = f"https://api.the-odds-api.com/v1/sports/{sport}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    try:
        response = requests.get(url, params=params)
        # Se la risposta non è OK (200), restituiamo l'errore senza crashare
        if response.status_code != 200:
            return response.status_code, {"error": response.text}
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}

if st.button("🔍 ANALIZZA MERCATI"):
    status, data = get_odds(sport_key)
    
    if status == 200:
        if not data:
            st.warning("Nessuna partita trovata al momento per questo campionato.")
        else:
            for match in data:
                home = match.get('home_team')
                away = match.get('away_team')
                
                with st.expander(f"🏟️ {home} vs {away}"):
                    c1, c2 = st.columns(2)
                    
                    # Logica Strategie
                    with c1:
                        st.write("**Strategia: Lay the Draw**")
                        # Cerchiamo la quota del pareggio (Draw)
                        st.info("Controlla quote su Exchange")
                    
                    with c2:
                        st.write("**Strategia: Over 2.5**")
                        st.success(f"Stake consigliato: {bankroll * 0.02:.2f}€")
    else:
        st.error(f"Errore {status}: Il server ha risposto in modo inatteso. Verifica se il campionato è attivo.")
        with st.expander("Dettagli Errore"):
            st.write(data)
