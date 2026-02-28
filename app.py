import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="ALPHA TERMINAL SMART", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    
    /* MENU A TENDINA: Forzatura Nero su Bianco */
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #000000 !important; }
    div[data-baseweb="popover"] li { color: #000000 !important; background-color: #FFFFFF !important; }

    /* TABELLE E TESTI: Giallo Oro */
    .stTable, table, th, td, tr, [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown p, h1, h2, h3, span {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    
    /* RIQUADRI */
    [data-testid="stMetric"] { background-color: #000000 !important; border: 2px solid #FFD700 !important; }
    .stExpander { border: 1px solid #FFD700 !important; background-color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. HEADER ---
st.title("🦅 ALPHA TERMINAL: FILTRO QUALITÀ")

with st.expander("📚 REQUISITI MINIMI PER IL TRADE", expanded=False):
    st.markdown("""
    | STRATEGIA | REQUISITO PROBABILITÀ | OBIETTIVO |
    | :--- | :--- | :--- |
    | **⚽ OVER 2.5** | **Maggiore del 55%** | Puntata su match ad alto numero di gol. |
    | **📉 LAY DRAW** | **Minore del 25%** | Bancata su pareggio poco probabile. |
    """)

# --- 3. SIDEBAR ---
st.sidebar.header("🕹️ DASHBOARD")
bankroll = st.sidebar.number_input("BUDGET (€)", value=500.0)
target_stake = (bankroll * st.sidebar.slider("STAKE (%)", 0.5, 10.0, 2.0)) / 100
hours_ahead = st.sidebar.number_input("FILTRO ORE", value=12)

# --- 4. FUNZIONI API ---
@st.cache_data(ttl=300)
def get_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        return r.status_code, r.json()
    except: return 500, []

# --- 5. LOGICA SMART FILTER ---
leagues = {"Serie A": "soccer_italy_serie_a", "Premier League": "soccer_epl", "La Liga": "soccer_spain_la_liga", "Bundesliga": "soccer_germany_bundesliga", "Eredivisie": "soccer_netherlands_eredivisie"}
sel_league = st.selectbox("SCEGLI CAMPIONATO:", list(leagues.keys()))

if st.button("ESEGUI SCANSIONE SMART"):
    status, data = get_data(leagues[sel_league])
    
    if status == 200:
        found = 0
        now_utc = datetime.now(timezone.utc)
        limit_time = now_utc + timedelta(hours=hours_ahead)

        for match in data:
            commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
            if commence_time > limit_time: continue

            bookies = match.get('bookmakers', [])
            if len(bookies) < 2: continue
            m2 = bookies[1]['markets']
            
            # Quote e Probabilità
            q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
            q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
            
            prob_draw = round((1/q_d_b)*100, 1) if q_d_b > 0 else 100
            prob_over = round((1/q_o_b)*100, 1) if q_o_b > 0 else 0

            # FILTRO SMART: Mostra solo se i requisiti sono soddisfatti
            is_good_over = prob_over >= 55
            is_good_lay = prob_draw <= 25

            if is_good_over or is_good_lay:
                found += 1
                with st.container():
                    st.write(f"### 🏟️ {match['home_team'].upper()} vs {match['away_team'].upper()}")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if is_good_lay:
                            st.error("📉 SEGNALE: LAY DRAW")
                            liability = (q_d_b - 1) * target_stake
                            st.metric("RISCHIO (PERDITA)", f"-{liability:.2f} €")
                            st.write(f"📊 Probabilità: {prob_draw}% (OTTIMA)")
                        else:
                            st.write("❌ Lay Draw non consigliato")

                    with col2:
                        if is_good_over:
                            st.success("⚽ SEGNALE: OVER 2.5")
                            profit_net = (q_o_b * target_stake) - target_stake
                            st.metric("RISCHIO (PERDITA)", f"-{target_stake:.2f} €")
                            st.write(f"📊 Probabilità: {prob_over}% (OTTIMA)")
                        else:
                            st.write("❌ Over 2.5 non consigliato")

                    with col3:
                        st.link_button("VAI SU BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={match['home_team']}")
                        st.caption(f"Inizio: {commence_time.strftime('%H:%M')} UTC")

        if found == 0:
            st.warning("Nessun match soddisfa i requisiti minimi (55% Over / 25% Lay Draw) in questo momento.")
