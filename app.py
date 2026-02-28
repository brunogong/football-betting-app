import streamlit as st
import requests
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Betfair Exclusive Trader", layout="wide")
API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- SIDEBAR ---
st.sidebar.header("📈 Betfair Trading")
bankroll = st.sidebar.number_input("Budget Betfair (€)", value=100.0)
stake_pct = st.sidebar.slider("Rischio Operazione (%)", 1.0, 5.0, 2.0)
trade_stake = (bankroll * stake_pct) / 100

# --- LOGICA DI CONFRONTO ---
def get_betfair_signals(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h'}
    r = requests.get(url, params=params)
    if r.status_code != 200: return []
    
    data = r.json()
    signals = []
    for match in data:
        bookies = match.get('bookmakers', [])
        if len(bookies) < 2: continue
        
        # Simuliamo: Bookie 0 = Broker Tradizionale, Bookie 1 = Betfair Exchange
        q_broker = next((o['price'] for m in bookies[0]['markets'] for o in m['outcomes'] if o['name'] == 'Draw'), 0)
        q_exchange = next((o['price'] for m in bookies[1]['markets'] for o in m['outcomes'] if o['name'] == 'Draw'), 0)
        
        diff = q_exchange - q_broker
        
        # SEGNALE 1: VALUE LAY (Betfair quota troppo alta)
        if diff > 0.40:
            signals.append({'match': f"{match['home_team']} vs {match['away_team']}", 'type': 'LAY', 'q': q_exchange, 'diff': diff})
        
        # SEGNALE 2: PRE-MATCH BACK (Betfair deve ancora allinearsi al ribasso)
        elif diff < -0.30:
            signals.append({'match': f"{match['home_team']} vs {match['away_team']}", 'type': 'BACK', 'q': q_exchange, 'diff': diff})
            
    return signals

# --- INTERFACCIA ---
st.title("🦅 Betfair Radar: Trading & Value")

league = st.selectbox("Campionato:", ["soccer_italy_serie_a", "soccer_epl", "soccer_spain_la_liga"])
if st.button("SCANSIONA BETFAIR"):
    results = get_betfair_signals(league)
    if results:
        for s in results:
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                if s['type'] == 'LAY':
                    col1.error(f"📉 **LAY THE DRAW** (Banca): {s['match']}")
                    col1.write(f"Quota Betfair ({s['q']}) è superiore al mercato. Valore nel Bancare.")
                    col2.metric("Responsabilità", f"{(s['q']-1)*trade_stake:.2f}€")
                else:
                    col1.success(f"🔥 **PRE-MATCH BACK** (Punta): {s['match']}")
                    col1.write(f"Quota Betfair ({s['q']}) è troppo bassa. Possibile calo live: Punta e fai Cash Out.")
                    col2.metric("Puntata Suggerita", f"{trade_stake:.2f}€")
                
                query = urllib.parse.quote(s['match'])
                st.link_button("VAI AL MERCATO", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={query}")
    else:
        st.info("Nessuna anomalia rilevata su Betfair al momento.")
