import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="ALPHA TERMINAL UNLOCKED", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #000000 !important; }
    div[data-baseweb="popover"] li { color: #000000 !important; background-color: #FFFFFF !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown p, h1, h2, h3, span {
        color: #FFD700 !important;
        font-weight: bold !important;
        text-shadow: 2px 2px 2px #000000;
    }
    [data-testid="stMetric"] { background-color: #000000 !important; border: 2px solid #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. SIDEBAR DINAMICA (SBLOCCO FILTRI) ---
st.sidebar.header("🕹️ CONTROLLO FILTRI")
bankroll = st.sidebar.number_input("BUDGET (€)", value=500.0)
target_stake = (bankroll * st.sidebar.slider("STAKE (%)", 0.5, 10.0, 2.0)) / 100

st.sidebar.divider()
st.sidebar.subheader("SOGLIE DI ACCETTAZIONE")
# Abbassiamo i default per vedere più partite
min_prob_over = st.sidebar.slider("Min. Probabilità Over (%)", 30, 80, 50) 
max_prob_draw = st.sidebar.slider("Max. Probabilità Pareggio (%)", 10, 50, 30)
hours_ahead = st.sidebar.number_input("FILTRO ORE", value=48)

# --- 3. FUNZIONI API ---
@st.cache_data(ttl=86400)
def get_all_leagues():
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return {s['title']: s['key'] for s in r.json() if s.get('group') == "Soccer"}
    except: return {}

@st.cache_data(ttl=300)
def get_match_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        return r.status_code, r.json()
    except: return 500, []

# --- 4. LOGICA ---
all_leagues = get_all_leagues()
if all_leagues:
    sel_league_name = st.selectbox("SCEGLI CAMPIONATO:", list(all_leagues.keys()))
    
    if st.button("ESEGUI SCANSIONE"):
        with st.spinner('Ricerca opportunità in corso...'):
            status, data = get_match_data(all_leagues[sel_league_name])
            
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
                    
                    q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                    q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                    
                    p_draw = round((1/q_d_b)*100, 1) if q_d_b > 0 else 100
                    p_over = round((1/q_o_b)*100, 1) if q_o_b > 0 else 0

                    # Applichiamo i nuovi filtri della sidebar
                    is_good_over = p_over >= min_prob_over
                    is_good_lay = p_draw <= max_prob_draw

                    if is_good_over or is_good_lay:
                        found += 1
                        with st.container():
                            st.write(f"### 🏟️ {match['home_team'].upper()} vs {match['away_team'].upper()}")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if is_good_lay:
                                    st.write("📉 LAY DRAW")
                                    lib = (q_d_b - 1) * target_stake
                                    st.metric("PERDITA", f"-{lib:.2f} €")
                                    st.metric("VINCITA NETTA", f"+{target_stake:.2f} €")
                                    st.write(f"📊 Prob: {p_draw}%")
                            with col2:
                                if is_good_over:
                                    st.write("⚽ OVER 2.5")
                                    prof = (q_o_b * target_stake) - target_stake
                                    st.metric("PERDITA", f"-{target_stake:.2f} €")
                                    st.metric("VINCITA NETTA", f"+{prof:.2f} €")
                                    st.write(f"📊 Prob: {p_over}%")
                            with col3:
                                st.write(f"⏰ {commence_time.strftime('%H:%M')} UTC")
                                q_url = urllib.parse.quote(f"{match['home_team']} {match['away_team']}")
                                st.link_button("APRI BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")
                
                if found == 0:
                    st.warning("Nessun match trovato. Prova ad abbassare la 'Min. Probabilità Over' nella sidebar.")
