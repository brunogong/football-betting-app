import streamlit as st
import requests
import urllib.parse
from datetime import datetime

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="AI Pro Betfair Trader", layout="wide", page_icon="📈")
API_KEY = "27593156a4d63edc49b283e86937f0e9"

if 'remaining_requests' not in st.session_state:
    st.session_state['remaining_requests'] = "N/D"

# --- 2. HEADER E WATCHLIST ---
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🦅 Betfair Global Market Scanner")
with col_t2:
    st.metric("🕒 Ora Locale", datetime.now().strftime("%H:%M:%S"))

st.markdown("""
| **🎯 Mercato Target** | **🏆 Lega Consigliata** | **💡 Strategia** |
| :--- | :--- | :--- |
| **Over 2.5** | 🇳🇱 Eredivisie / 🇳🇴 Eliteserien | Punta se Quota Betfair > Broker |
| **Lay Draw** | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier / 🇮🇹 Serie A | Banca se Quota Betfair > Broker |
---
""")

# --- 3. SIDEBAR: CONTROLLI ---
st.sidebar.header("💰 Money Management")
bankroll = st.sidebar.number_input("Budget (€)", value=100.0)
stake_pct = st.sidebar.slider("Rischio (%)", 1.0, 5.0, 2.0)
user_stake = (bankroll * stake_pct) / 100

st.sidebar.divider()
st.sidebar.subheader("⚙️ Soglie di Valore")
val_diff_draw = st.sidebar.slider("Soglia Valore Pareggio", 0.10, 1.00, 0.30)
val_diff_over = st.sidebar.slider("Soglia Valore Over 2.5", 0.05, 0.50, 0.15)

st.sidebar.divider()
st.sidebar.write(f"💳 Crediti API: **{st.session_state['remaining_requests']}**")

# --- 4. FUNZIONI CORE ---
@st.cache_data(ttl=86400)
def get_leagues():
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return {s['title']: s['key'] for s in r.json() if s.get('group') == "Soccer"}
    except: return {}

@st.cache_data(ttl=300) # 5 Minuti Cache
def get_full_market_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    # Chiediamo sia H2H che TOTALS (Under/Over) in una sola chiamata (Risparmio Crediti!)
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        st.session_state['remaining_requests'] = r.headers.get('x-requests-remaining', "N/D")
        return r.status_code, r.json()
    except: return 500, []

# --- 5. LOGICA DI ANALISI ---
leagues_dict = get_leagues()
if leagues_dict:
    sel_name = st.selectbox("Seleziona Campionato:", list(leagues_dict.keys()))
    
    if st.button("🚀 AVVIA SCAN MULTI-MERCATO"):
        status, data = get_full_market_data(leagues_dict[sel_name])
        
        if status == 200 and data:
            found = 0
            for match in data:
                home, away = match.get('home_team'), match.get('away_team')
                bookies = match.get('bookmakers', [])
                if len(bookies) < 2: continue

                # Analisi H2H (Pareggio)
                b1_m = bookies[0]['markets']
                b2_m = bookies[1]['markets']
                
                # --- LOGICA DRAW ---
                q_d_m = next((o['price'] for m in b1_m if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_d_b = next((o['price'] for m in b2_m if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                
                # --- LOGICA OVER 2.5 ---
                q_o_m = next((o['price'] for m in b1_m if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                q_o_b = next((o['price'] for m in b2_m if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)

                draw_signal = (q_d_b - q_d_m) >= val_diff_draw
                over_signal = (q_o_b - q_o_m) >= val_diff_over

                if draw_signal or over_signal:
                    found += 1
                    with st.container(border=True):
                        st.subheader(f"🏟️ {home} vs {away}")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**📊 Quote Pareggio**")
                            st.write(f"Broker: {q_d_m} | Betfair: **{q_d_b}**")
                            if draw_signal:
                                st.error(f"📉 **LAY DRAW DETECTED**")
                                st.caption(f"Responsabilità: {(q_d_b-1)*user_stake:.2f}€")

                        with col2:
                            st.write("**⚽ Quote Over 2.5**")
                            st.write(f"Broker: {q_o_m} | Betfair: **{q_o_b}**")
                            if over_signal:
                                st.success(f"🔥 **VALUE OVER DETECTED**")
                                st.caption(f"Puntata: {user_stake:.2f}€")

                        with col3:
                            query = urllib.parse.quote(f"{home} {away}")
                            st.link_button("📲 APRI EXCHANGE", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={query}", use_container_width=True)
            
            if found == 0:
                st.info("Nessuna anomalia trovata. Prova a ridurre le soglie di valore in sidebar.")
