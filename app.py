import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA (CONTRASTO ESTREMO) ---
st.set_page_config(page_title="ALPHA TERMINAL FULL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    
    /* MENU A TENDINA: Nero su Bianco per massima leggibilità */
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #000000 !important; }
    div[data-baseweb="popover"] li { color: #000000 !important; background-color: #FFFFFF !important; }

    /* TESTI E METRICHE: Giallo Oro con Ombra Nera per leggere anche su bianco */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown p, h1, h2, h3, span {
        color: #FFD700 !important;
        font-weight: bold !important;
        text-shadow: 2px 2px 2px #000000; /* Ombra di sicurezza */
    }
    
    /* RIQUADRI */
    [data-testid="stMetric"] { 
        background-color: #000000 !important; 
        border: 2px solid #FFD700 !important; 
    }
    .stExpander { border: 1px solid #FFD700 !important; background-color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. FUNZIONI API ---
@st.cache_data(ttl=86400)
def get_all_leagues():
    """Recupera TUTTI i campionati di calcio disponibili"""
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return {s['title']: s['key'] for s in r.json() if s.get('group') == "Soccer"}
    except:
        return {}

@st.cache_data(ttl=300)
def get_match_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        return r.status_code, r.json()
    except:
        return 500, []

# --- 3. HEADER E GUIDA ---
st.title("🦅 ALPHA TERMINAL: FULL SCANNER")

with st.expander("📚 TABELLA STRATEGICA", expanded=False):
    st.write("Over 2.5: Requisito Probabilità > 55%")
    st.write("Lay Draw: Requisito Probabilità < 25%")

# --- 4. SIDEBAR ---
st.sidebar.header("🕹️ CONTROLLO RISK/REWARD")
bankroll = st.sidebar.number_input("BUDGET (€)", value=500.0)
target_stake = (bankroll * st.sidebar.slider("STAKE (%)", 0.5, 10.0, 2.0)) / 100
hours_ahead = st.sidebar.number_input("FILTRO ORE (Inizio Match)", value=24)

# --- 5. LOGICA PRINCIPALE ---
all_leagues = get_all_leagues()

if all_leagues:
    sel_league_name = st.selectbox("SELEZIONA IL CAMPIONATO:", list(all_leagues.keys()))
    sel_league_key = all_leagues[sel_league_name]

    if st.button("ESEGUI SCANSIONE SMART"):
        status, data = get_match_data(sel_league_key)
        
        if status == 200:
            found = 0
            now_utc = datetime.now(timezone.utc)
            limit_time = now_utc + timedelta(hours=hours_ahead)

            for match in data:
                commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                if commence_time > limit_time: continue

                bookies = match.get('bookmakers', [])
                if len(bookies) < 2: continue
                
                m2 = next((b['markets'] for b in bookies if b['key'].lower() in ['betfair', 'betfair_ex', 'pinnacle']), bookies[1]['markets'])
                
                q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                
                prob_draw = round((1/q_d_b)*100, 1) if q_d_b > 0 else 100
                prob_over = round((1/q_o_b)*100, 1) if q_o_b > 0 else 0

                is_good_over = prob_over >= 55
                is_good_lay = prob_draw <= 25

                if is_good_over or is_good_lay:
                    found += 1
                    with st.container():
                        st.write(f"### 🏟️ {match['home_team'].upper()} vs {match['away_team'].upper()}")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if is_good_lay:
                                st.write("📉 LAY DRAW")
                                liability = (q_d_b - 1) * target_stake
                                st.metric("PERDITA (RISCHIO)", f"-{liability:.2f} €")
                                st.metric("VINCITA NETTA", f"+{target_stake:.2f} €")
                                st.write(f"📊 Probabilità: {prob_draw}%")
                            else:
                                st.write("❌ Lay Draw: Sotto requisito")

                        with col2:
                            if is_good_over:
                                st.write("⚽ OVER 2.5")
                                profit_net = (q_o_b * target_stake) - target_stake
                                st.metric("PERDITA (RISCHIO)", f"-{target_stake:.2f} €")
                                st.metric("VINCITA NETTA", f"+{profit_net:.2f} €")
                                st.write(f"📊 Probabilità: {prob_over}%")
                            else:
                                st.write("❌ Over 2.5: Sotto requisito")

                        with col3:
                            st.write(f"⏰ {commence_time.strftime('%H:%M')} UTC")
                            st.write(f"Quota D: {q_d_b} | Quota O: {q_o_b}")
                            q_url = urllib.parse.quote(f"{match['home_team']} {match['away_team']}")
                            st.link_button("APRI BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")

            if found == 0:
                st.warning("Nessun match con probabilità sufficiente trovato.")
        else:
            st.error("Errore nel recupero dati.")
else:
    st.error("Impossibile caricare i campionati.")
