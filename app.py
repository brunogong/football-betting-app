import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA (CSS MIRATO) ---
st.set_page_config(page_title="ALPHA TERMINAL PRO", layout="wide")

st.markdown("""
    <style>
    /* Sfondo globale nero */
    .stApp { background-color: #000000; }
    
    /* MENU A TENDINA: Testo Nero su Sfondo Bianco */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    div[data-baseweb="popover"] li {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }

    /* TABELLE: Testo Giallo su Sfondo Nero */
    .stTable, table, th, td, tr {
        color: #FFD700 !important;
        background-color: #000000 !important;
        border: 1px solid #FFD700 !important;
    }

    /* TESTI E METRICHE: Giallo Oro */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown p, h1, h2, h3, span {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    
    /* RIQUADRI PARTITE */
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 2px solid #FFD700 !important;
        padding: 10px !important;
    }

    /* EXPANDER (Guida) */
    .stExpander {
        border: 1px solid #FFD700 !important;
        background-color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. HEADER E TABELLA GUIDA ---
st.title("🦅 ALPHA TERMINAL: LIVE SCANNER")

with st.expander("📚 GUIDA AI CAMPIONATI STRATEGICI", expanded=True):
    st.markdown("""
    | STRATEGIA | CAMPIONATI IDEALI | LOGICA DI PROFITTO |
    | :--- | :--- | :--- |
    | **⚽ OVER 2.5** | Olanda, Norvegia, Germania, Islanda | Alta frequenza di gol e tiri. |
    | **📉 LAY DRAW** | Inghilterra, Italia, Spagna | Alta liquidita per Cash Out rapido. |
    | **🔥 VALUE** | Portogallo, Turchia, Brasile | Massime discrepanze Broker/Exchange. |
    """)

# --- 3. SIDEBAR: MONEY MANAGEMENT ---
st.sidebar.header("🕹️ DASHBOARD")
bankroll = st.sidebar.number_input("BUDGET (€)", value=500.0)
target_stake = (bankroll * st.sidebar.slider("STAKE (%)", 0.5, 10.0, 2.0)) / 100
hours_ahead = st.sidebar.number_input("FILTRO ORE", value=6)

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
        return r.status_code, r.json()
    except: return 500, []

# --- 5. LOGICA OPERATIVA ---
leagues_dict = get_leagues()
if leagues_dict:
    sel_league = st.selectbox("SCEGLI CAMPIONATO (Menu Bianco/Nero):", list(leagues_dict.keys()))
    
    if st.button("ESEGUI ANALISI MERCATI"):
        status, data = get_data(leagues_dict[sel_league])
        
        if status == 200 and data:
            now_utc = datetime.now(timezone.utc)
            limit_time = now_utc + timedelta(hours=hours_ahead)
            found = 0

            for match in data:
                commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                if commence_time > limit_time: continue

                home, away = match.get('home_team'), match.get('away_team')
                bookies = match.get('bookmakers', [])
                if len(bookies) < 2: continue

                # Estrazione Quote (M1=Broker, M2=Betfair)
                m1, m2 = bookies[0]['markets'], bookies[1]['markets']
                q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                
                # Calcolo Probabilità Implicita (Suggerita dagli scommettitori)
                prob_draw = round((1/q_d_b)*100, 1) if q_d_b > 0 else 0
                prob_over = round((1/q_o_b)*100, 1) if q_o_b > 0 else 0

                # Mostriamo il match se ci sono quote valide
                if q_d_b > 0 or q_o_b > 0:
                    found += 1
                    with st.container():
                        st.write(f"### 🏟️ {home.upper()} vs {away.upper()}")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("📉 **LAY THE DRAW**")
                            liability = (q_d_b - 1) * target_stake
                            st.metric("PERDITA (SE PAREGGIO)", f"-{liability:.2f} €")
                            st.metric("PROFITTO (SE NON PAREGGIO)", f"+{target_stake:.2f} €")
                            st.write(f"📊 Probabilità: {prob_draw}%")
                            st.caption("Consigliato se < 25%")

                        with col2:
                            st.write("⚽ **OVER 2.5 GOL**")
                            profit_net = (q_o_b * target_stake) - target_stake
                            st.metric("PERDITA (SE UNDER)", f"-{target_stake:.2f} €")
                            st.metric("PROFITTO (SE OVER)", f"+{profit_net:.2f} €")
                            st.write(f"📊 Probabilità: {prob_over}%")
                            st.caption("Consigliato se > 55%")

                        with col3:
                            st.write("📋 **AZIONI**")
                            q_url = urllib.parse.quote(f"{home} {away}")
                            st.link_button("VAI SU BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")
                            st.write("---")
                            st.write(f"Kick-off: {commence_time.strftime('%H:%M')} UTC")

            if found == 0:
                st.info("Nessuna partita trovata per l'orizzonte temporale scelto.")
