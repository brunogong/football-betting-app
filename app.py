import streamlit as st
import requests
import urllib.parse
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Pro Scanner", layout="wide")

# --- HEADER ---
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("Betting Intelligence Dashboard")
with col_t2:
    now = datetime.now().strftime("%H:%M:%S")
    st.metric("Ora Locale", now)

st.markdown("""
### Campionati Consigliati:
- **Over 2.5:** Olanda, Norvegia, Germania 2
- **Lay Draw:** Premier League, Serie A, La Liga
- **Late Goal:** Bundesliga, Scozia, Islanda
---
""")

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# SIDEBAR
st.sidebar.header("Gestione Fondi")
bankroll = st.sidebar.number_input("Budget Totale", value=100.0)
stake_percent = st.sidebar.slider("Stake %", 1.0, 5.0, 2.0)
user_stake = (bankroll * stake_percent) / 100

st.sidebar.divider()
st.sidebar.subheader("Filtri")
max_over_odds = st.sidebar.slider("Max Quota Over 2.5", 1.40, 2.00, 1.70)
min_draw_lay = st.sidebar.slider("Min Quota Lay Draw", 3.00, 4.00, 3.25)
max_draw_lay = st.sidebar.slider("Max Quota Lay Draw", 4.00, 6.00, 4.40)

@st.cache_data(ttl=3600)
def get_active_leagues():
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            return {s['title']: s['key'] for s in r.json() if s.get('group') == "Soccer"}
        return {}
    except: return {}

def get_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        return r.status_code, r.json()
    except: return 500, []

leagues = get_active_leagues()

if leagues:
    selected_name = st.selectbox("Seleziona Campionato:", list(leagues.keys()))
    sport_key = leagues[selected_name]

    if st.button("SCANSIONA"):
        status, data = get_odds(sport_key)
        if status == 200 and data:
            found = 0
            for match in data:
                home, away = match.get('home_team'), match.get('away_team')
                if not match['bookmakers']: continue
                mkts = match['bookmakers'][0]['markets']
                h2h = next((m for m in mkts if m['key'] == 'h2h'), None)
                totals = next((m for m in mkts if m['key'] == 'totals'), None)
                
                over_q = next((o['price'] for o in totals['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 10.0) if totals else 10.0
                draw_q = next((o['price'] for o in h2h['outcomes'] if o['name'] == 'Draw'), 1.0) if h2h else 1.0
                
                if over_q <= max_over_odds or (min_draw_lay <= draw_q <= max_draw_lay):
                    found += 1
                    with st.container(border=True):
                        st.subheader(f"{home} vs {away}")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c1:
                            if over_q <= max_over_odds: 
                                st.success(f"OVER 2.5: {over_q}")
                                st.write(f"**Punta: {user_stake:.2f}€**")
                        with c2:
                            if min_draw_lay <= draw_q <= max_draw_lay:
                                st.error(f"LAY DRAW: {draw_q}")
                                liability = (draw_q - 1) * user_stake
                                st.metric("Resp. (Rischio)", f"{liability:.2f}€")
                                st.write(f"**Banca: {user_stake:.2f}€**")
                        with c3:
                            term = urllib.parse.quote(f"{home} {away}")
                            st.link_button("BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={term}")
            if found == 0: st.info("Nessun segnale.")
else:
    st.error("Errore API.")
