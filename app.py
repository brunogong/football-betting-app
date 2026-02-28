import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="ALPHA SCANNER PRO", layout="wide")

# CSS per un look Dark Mode Professionale
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2563eb; color: white; }
    .stContainer { border: 1px solid #374151; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. HEADER PROFESSIONALE ---
header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
with header_col1:
    st.title("🚀 ALPHA SCANNER PRO")
    st.caption("Professional Betting Exchange Analytics Hub | Real-Time Market Discrepancy")

with header_col2:
    st.metric("SERVER STATUS", "OPERATIONAL", delta="12ms")

with header_col3:
    st.metric("UTC TIME", datetime.now(timezone.utc).strftime("%H:%M:%S"))

# --- 3. SIDEBAR: TERMINALE DI CONTROLLO ---
st.sidebar.header("🕹️ TERMINALE DI CONTROLLO")
bankroll = st.sidebar.number_input("CAPITALE TOTALE (€)", value=500.0, step=50.0)
stake_pct = st.sidebar.slider("RISCHIO PER TRADE (%)", 0.5, 10.0, 2.0)
actual_stake = (bankroll * stake_pct) / 100

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 FILTRI STRATEGICI")
val_diff_draw = st.sidebar.slider("SOGLIA VALUE DRAW", 0.10, 1.00, 0.25)
val_diff_over = st.sidebar.slider("SOGLIA VALUE OVER", 0.05, 0.50, 0.10)
hours_filter = st.sidebar.number_input("ORIZZONTE TEMPORALE (ORE)", value=4, min_value=1)

if 'remaining_requests' not in st.session_state:
    st.session_state['remaining_requests'] = "500"

st.sidebar.info(f"API CREDITS REMAINING: {st.session_state['remaining_requests']}")

# --- 4. FUNZIONI CORE ---
@st.cache_data(ttl=3600)
def get_leagues():
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return {s['title']: s['key'] for s in r.json() if s.get('group') == "Soccer"}
    except: return {}

@st.cache_data(ttl=300)
def get_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        st.session_state['remaining_requests'] = r.headers.get('x-requests-remaining', "N/D")
        return r.status_code, r.json()
    except: return 500, []

# --- 5. LOGICA OPERATIVA ---
leagues_dict = get_leagues()
if leagues_dict:
    sel_league = st.selectbox("SELEZIONA MERCATO (ASSET CLASS)", list(leagues_dict.keys()))
    
    if st.button("ESEGUI SCANSIONE MERCATI"):
        status, data = get_data(leagues_dict[sel_league])
        
        if status == 200 and data:
            now_utc = datetime.now(timezone.utc)
            limit_time = now_utc + timedelta(hours=hours_filter)
            found = 0

            for match in data:
                commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                if commence_time > limit_time: continue

                home, away = match.get('home_team'), match.get('away_team')
                bookies = match.get('bookmakers', [])
                if len(bookies) < 2: continue

                # Estrazione Quote (Market vs Betfair)
                m1, m2 = bookies[0]['markets'], bookies[1]['markets']
                
                # Draw Logics
                q_d_m = next((o['price'] for m in m1 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                
                # Over Logics
                q_o_m = next((o['price'] for m in m1 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)

                draw_signal = (q_d_b - q_d_m) >= val_diff_draw
                over_signal = (q_o_b - q_o_m) >= val_diff_over

                if draw_signal or over_signal:
                    found += 1
                    with st.container():
                        c_head, c_btn = st.columns([3, 1])
                        c_head.subheader(f"🏟️ {home.upper()} vs {away.upper()}")
                        c_head.caption(f"KICK-OFF: {commence_time.strftime('%H:%M')} UTC | {sel_league}")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        # BOX LAY DRAW
                        with col1:
                            st.markdown("### 📉 LAY DRAW")
                            st.write(f"Broker: `{q_d_m}` | Betfair: **`{q_d_b}`**")
                            if draw_signal:
                                liability = (q_d_b - 1) * actual_stake
                                st.error(f"VALORE DETECTED")
                                st.write(f"💸 **RISCHIO (Responsabilità): {liability:.2f}€**")
                                st.write(f"💰 Vincita Netta: {actual_stake:.2f}€")
                            else: st.caption("No Gap detected")

                        # BOX OVER 2.5
                        with col2:
                            st.markdown("### ⚽ OVER 2.5")
                            st.write(f"Broker: `{q_o_m}` | Betfair: **`{q_o_b}`**")
                            if over_signal:
                                potential_win = (q_o_b * actual_stake) - actual_stake
                                st.success("VALUE DETECTED")
                                st.write(f"💸 **PUNTATA: {actual_stake:.2f}€**")
                                st.write(f"💰 Profitto Netto: {potential_win:.2f}€")
                            else: st.caption("No Gap detected")

                        # BOTTONE AZIONE
                        with col3:
                            st.write("") # Spacer
                            st.write("")
                            q_url = urllib.parse.quote(f"{home} {away}")
                            st.link_button("APRI MERCATO BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")

            if found == 0:
                st.warning("SCANSIONE COMPLETATA: Nessuna anomalia rilevata con i filtri attuali.")
