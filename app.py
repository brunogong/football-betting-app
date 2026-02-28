import streamlit as st
import requests
import urllib.parse
from datetime import datetime
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Pro Scanner - FINAL", layout="wide", page_icon="🎯")

# --- HEADER CON OROLOGIO E WATCHLIST ---
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("⚽ Betting Intelligence Dashboard")
with col_t2:
    # Orologio Live aggiornato al caricamento
    now = datetime.now().strftime("%H:%M:%S")
    st.metric("🕒 Ora Locale (Live)", now)

st.markdown("""
### 🏆 Top Leagues Consigliate per Strategia:
| **🔥 Over 2.5 / BTTS** | **📉 Lay the Draw (Exchange)** | **🕒 Late Goal (Min. 75')** |
| :--- | :--- | :--- |
| 🇳🇱 Olanda (Eredivisie / Eerste) | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | 🇩🇪 Bundesliga (Germania) |
| 🇳🇴 Norvegia (Eliteserien) | 🇪🇸 La Liga (Spagna) | 🇮🇸 Islanda (Bestadeild) |
| 🇩🇪 Bundesliga 2 | 🇮🇹 Serie A (Italia) | 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scozia (Premiership) |
---
""")

# --- CONFIGURAZIONE API ---
API_KEY = "27593156a4d63edc49b283e86937f0e9"

# SIDEBAR: GESTIONE SOLDI
st.sidebar.header("💰 Gestione Fondi")
bankroll = st.sidebar.number_input("Budget Totale (€)", value=100.0)
stake_percent = st.sidebar.slider("Stake per operazione (%)", 1.0, 5.0, 2.0)
user_stake = (bankroll * stake_percent) / 100

st.sidebar.divider()
st.sidebar.subheader("Filtri Selettivi")
max_over_odds = st.sidebar.slider("Max Quota Over 2.5", 1.40, 2.00, 1.70)
min_draw_lay = st.sidebar.slider("Min Quota Lay Draw", 3.00, 4.00, 3.25)
max_draw_lay = st.sidebar.slider("Max Quota Lay Draw", 4.00, 6.00, 4.40)

# --- FUNZIONI CORE ---
@st.cache_data(ttl=3600)
def get_active_leagues():
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return {s['title']: s['key'] for s in response.json() if s.get('group') == "Soccer"}
        return {}
    except: return {}

def get_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        response = requests.get(url, params=params)
        return response.status_code, response.json()
    except: return 500, []

# --- INTERFACCIA OPERATIVA ---
leagues = get_active_leagues()

if leagues:
    selected_name = st.selectbox("🎯 Seleziona un campionato attivo:", list(leagues.keys()))
    sport_key = leagues[selected_name]

    if st.button("🚀 SCANSIONA OPPORTUNITÀ"):
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
                
                is_over = over_q <= max_over_odds
                is_lay = min_draw_lay <= draw_q <= max_draw_lay
                
                if is_over or is_lay:
                    found += 1
                    with st.container(border=True):
                        st.subheader(f"🏟️ {home} vs {away}")
                        c1, c2, c3 = st.columns([1, 1.2, 1])
                        
                        with c1:
                            if is_over:
                                st.success(f"🔥 **OVER 2.5**\n\nQuota: {over_q}")
                                st.caption(f"Stake: {user_stake:.2f}€")
                            else: st.write("Over: No Segnale")
                                
                        with c2:
                            if is_lay:
                                st.error(f"📉 **LAY DRAW**\n\nQuota: {draw_q}")
                                liability = (draw_q - 1) * user_stake
                                st.metric("Responsabilità", f"{liability:.2f}€")
                                st.caption(f"Vincita: {user_stake:.2f}€")
                            else: st.write("Lay: No Segnale")
                                
                        with c3:
                            search_term = urllib.parse.quote(f"{home} {away}")
                            # Link a Betfair con termine di ricerca
                            betfair_url = f"https://www.betfair.it/exchange/plus/football/search?searchTerm={search_term}"
                            st.link_button("📲 VAI SU BETFAIR", betfair_url, type="primary", use_container_width=True)
                            st.divider()
                            st.caption("Pianifica l'uscita o il Late Goal")
            
            if found == 0:
                st.info("Nessun segnale trovato con i filtri attuali. Prova un altro campionato.")
else:
    st.error("Errore API. Verifica la tua connessione o la chiave.")

st.sidebar.divider()
st.sidebar.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M')}")
