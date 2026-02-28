import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA (FORZATURA GIALLO/NERO) ---
st.set_page_config(page_title="ALPHA SCANNER ELITE", layout="wide")

st.markdown("""
    <style>
    /* Sfondo globale scuro */
    .stApp { background-color: #050505; }
    
    /* Forza il colore giallo acceso su tutte le metriche e testi importanti */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown p, h3 {
        color: #FFD700 !important; /* Giallo Oro */
        font-weight: bold !important;
    }
    
    /* Riquadri neri definiti */
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 3px solid #FFD700 !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    /* Stile per i pulsanti */
    .stButton>button {
        background-color: #FFD700 !important;
        color: black !important;
        font-weight: bold !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. LOGICA PROBABILITÀ (EURI-ALGORITHM) ---
def estimate_probability(odds):
    if odds <= 0: return 0
    # Probabilità implicita con aggiustamento per il margine (approx)
    return round((1 / odds) * 100, 1)

# --- 3. SIDEBAR E SETUP ---
st.sidebar.header("📊 TRADING TERMINAL")
bankroll = st.sidebar.number_input("BUDGET (€)", value=500.0)
target_stake = (bankroll * st.sidebar.slider("STAKE (%)", 0.5, 10.0, 2.0)) / 100
hours_filter = st.sidebar.number_input("FILTRO ORE", value=6)

# --- 4. FUNZIONI API ---
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

# --- 5. INTERFACCIA OPERATIVA ---
leagues_dict = get_leagues()
if leagues_dict:
    sel_league = st.selectbox("SCEGLI MERCATO:", list(leagues_dict.keys()))
    
    if st.button("ESEGUI ANALISI MULTI-STRATEGIA"):
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

                m1, m2 = bookies[0]['markets'], bookies[1]['markets']
                
                # Quote Draw & Over
                q_d_m = next((o['price'] for m in m1 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_o_m = next((o['price'] for m in m1 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)

                # Calcolo Probabilità
                prob_draw = estimate_probability(q_d_b)
                prob_over = estimate_probability(q_o_b)

                if (q_d_b - q_d_m) >= 0.20 or (q_o_b - q_o_m) >= 0.10:
                    found += 1
                    with st.container():
                        st.write(f"### ⚽ {home.upper()} vs {away.upper()}")
                        st.write(f"Inizio: {commence_time.strftime('%H:%M')} UTC")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        # --- STRATEGIA 1: LAY THE DRAW (Bancata) ---
                        with col1:
                            st.write("📉 **LAY THE DRAW**")
                            liability = (q_d_b - 1) * target_stake
                            st.metric("PERDITA (RISCHIO)", f"-{liability:.2f} €")
                            st.metric("PROFITTO NETTO", f"+{target_stake:.2f} €")
                            st.write(f"Probabilità Pareggio: {prob_draw}%")
                            st.caption("Consigliato se Prob. < 25%")

                        # --- STRATEGIA 2: OVER 2.5 (Puntata) ---
                        with col2:
                            st.write("⚽ **OVER 2.5 GOL**")
                            profit_net = (q_o_b * target_stake) - target_stake
                            st.metric("PERDITA (RISCHIO)", f"-{target_stake:.2f} €")
                            st.metric("PROFITTO NETTO", f"+{profit_net:.2f} €")
                            st.write(f"Probabilità Over: {prob_over}%")
                            st.caption("Consigliato se Prob. > 55%")

                        # --- STRATEGIA 3: TRADING INFO ---
                        with col3:
                            st.write("📋 **ANALISI TRADE**")
                            # Valutiamo se c'è un "Gap" di valore
                            gap_d = round(q_d_b - q_d_m, 2)
                            gap_o = round(q_o_b - q_o_m, 2)
                            st.write(f"Value Gap Draw: +{gap_d}")
                            st.write(f"Value Gap Over: +{gap_o}")
                            st.write("---")
                            q_url = urllib.parse.quote(f"{home} {away}")
                            st.link_button("ENTRA SU BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")

            if found == 0:
                st.info("Nessuna opportunità rilevata con i filtri correnti.")
