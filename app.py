import streamlit as st
import requests
import urllib.parse
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AI Value Scanner - 5min Cache", layout="wide")
API_KEY = "27593156a4d63edc49b283e86937f0e9"

if 'remaining_requests' not in st.session_state:
    st.session_state['remaining_requests'] = "N/D"

# --- FUNZIONI CON CACHE A 5 MINUTI (300 SECONDI) ---
@st.cache_data(ttl=86400)
def get_leagues_optimized():
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return {s['title']: s['key'] for s in r.json() if s.get('group') == "Soccer"}
    except: return {}

@st.cache_data(ttl=300) # Ridotto a 5 minuti per maggiore precisione
def get_odds_multi_provider(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    try:
        r = requests.get(url, params=params)
        st.session_state['remaining_requests'] = r.headers.get('x-requests-remaining', "N/D")
        return r.status_code, r.json()
    except: return 500, []

# --- INTERFACCIA ---
st.title("🎯 Value & Strategy Scanner (v5.0)")

# Header Crediti
c_met1, c_met2 = st.columns(2)
with c_met1:
    st.metric("Richieste Rimanenti", st.session_state['remaining_requests'])
with c_met2:
    st.info("⏱️ Cache: 5 Minuti | 📉 Strategia: Value Bet & Lay Draw")

st.divider()

# Sidebar
st.sidebar.header("💰 Money Management")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)
stake_pct = st.sidebar.slider("Stake (%)", 1.0, 5.0, 2.0)
current_stake = (bankroll * stake_pct) / 100

# Parametri Value Bet
st.sidebar.divider()
st.sidebar.subheader("🔍 Parametri Value")
value_threshold = st.sidebar.slider("Soglia Valore (%)", 2, 10, 5)

# --- LOGICA OPERATIVA ---
leagues = get_leagues_optimized()
if leagues:
    selected_league = st.selectbox("Scegli Campionato:", list(leagues.keys()))
    
    if st.button("🚀 SCANSIONA MERCATI"):
        status, data = get_odds_multi_provider(leagues[selected_league])
        if status == 200:
            st.session_state['last_data'] = data
            st.session_state['last_update'] = datetime.now().strftime("%H:%M:%S")

    if 'last_data' in st.session_state:
        st.caption(f"Ultimo agg: {st.session_state['last_update']} (Dati più precisi)")
        
        found = 0
        for match in st.session_state['last_data']:
            home, away = match.get('home_team'), match.get('away_team')
            bookies = match.get('bookmakers', [])
            
            if len(bookies) < 2: continue # Servono almeno 2 broker per scovare value bet
            
            # Prendiamo il primo e il secondo bookmaker per confronto
            b1, b2 = bookies[0], bookies[1]
            h2h_1 = next((m for m in b1['markets'] if m['key'] == 'h2h'), None)
            h2h_2 = next((m for m in b2['markets'] if m['key'] == 'h2h'), None)
            
            if h2h_1 and h2h_2:
                # Esempio: Cerchiamo una Value Bet sul Pareggio (X)
                draw_q1 = next((o['price'] for o in h2h_1['outcomes'] if o['name'] == 'Draw'), 0)
                draw_q2 = next((o['price'] for o in h2h_2['outcomes'] if o['name'] == 'Draw'), 0)
                
                # Calcolo della differenza percentuale (Value)
                diff = abs(draw_q1 - draw_q2) / min(draw_q1, draw_q2) * 100
                is_value = diff >= value_threshold

                if is_value or (3.20 <= draw_q1 <= 4.50): # Mostra se c'è valore o se è un buon Lay Draw
                    found += 1
                    with st.container(border=True):
                        st.subheader(f"{home} vs {away}")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**{b1['title']}**: {draw_q1}")
                            st.write(f"**{b2['title']}**: {draw_q2}")
                        
                        with col2:
                            if is_value:
                                st.success(f"💎 VALUE BET RILEVATA!\nDiff: {diff:.1f}%")
                            st.error(f"📉 Lay Draw: {draw_q1}")
                            st.metric("Responsabilità", f"{(draw_q1-1)*current_stake:.2f}€")
                        
                        with col3:
                            query = urllib.parse.quote(f"{home} {away}")
                            st.link_button("ANALIZZA SU BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={query}")

        if found == 0:
            st.info("Nessuna anomalia o segnale trovato. Prova un altro mercato.")
