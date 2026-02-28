import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ESTETICA (GIALLO SU NERO FORZATO) ---
st.set_page_config(page_title="ALPHA TERMINAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown p, h1, h2, h3, li {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 2px solid #FFD700 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    .stButton>button {
        background-color: #FFD700 !important;
        color: black !important;
        font-weight: bold !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. TABELLA STRATEGIE (MASTER LIST) ---
st.title("🦅 ALPHA TERMINAL: STRATEGIE E FILTRI")

with st.expander("📚 GUIDA AI CAMPIONATI E STRATEGIE (CLICCA PER APRIRE)", expanded=True):
    st.markdown("""
    | STRATEGIA | CAMPIONATI IDEALI | LOGICA DI PROFITTO |
    | :--- | :--- | :--- |
    | **⚽ OVER 2.5** | Olanda (Eredivisie), Norvegia, Germania, Islanda | Partite con alta frequenza di tiri e difese larghe. |
    | **📉 LAY THE DRAW** | Inghilterra (Premier), Italia (Serie A), Spagna | Mercati liquidi per uscire (Cash Out) dopo il primo gol. |
    | **🔥 VALUE BACK** | Portogallo, Turchia, Brasile | Discrepanze massime tra Broker locali e Exchange. |
    """)

# --- 3. SIDEBAR: FILTRI E MONEY MANAGEMENT ---
st.sidebar.header("🕹️ FILTRI OPERATIVI")

# Money Management
bankroll = st.sidebar.number_input("BUDGET (€)", value=500.0)
target_stake = (bankroll * st.sidebar.slider("STAKE TARGET (%)", 0.5, 10.0, 2.0)) / 100

st.sidebar.divider()

# Filtri di Visualizzazione
show_draw = st.sidebar.checkbox("Mostra segnali LAY DRAW", value=True)
show_over = st.sidebar.checkbox("Mostra segnali OVER 2.5", value=True)
hours_ahead = st.sidebar.number_input("Orizzonte temporale (Ore)", value=6, min_value=1)

# Filtro Qualità (Value Gap)
min_gap_draw = st.sidebar.slider("Min. Gap Valore Draw", 0.10, 1.00, 0.20)
min_gap_over = st.sidebar.slider("Min. Gap Valore Over", 0.05, 0.50, 0.10)

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

# --- 5. LOGICA DI ANALISI ---
leagues_dict = get_leagues()
if leagues_dict:
    sel_league = st.selectbox("SELEZIONA CAMPIONATO DA ANALIZZARE:", list(leagues_dict.keys()))
    
    if st.button("ESEGUI SCANSIONE CON FILTRI"):
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

                m1, m2 = bookies[0]['markets'], bookies[1]['markets']
                
                # Estrazione Quote
                q_d_m = next((o['price'] for m in m1 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_o_m = next((o['price'] for m in m1 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)

                # Calcolo Segnali in base ai filtri
                draw_signal = show_draw and (q_d_b - q_d_m) >= min_gap_draw
                over_signal = show_over and (q_o_b - q_o_m) >= min_gap_over

                if draw_signal or over_signal:
                    found += 1
                    with st.container():
                        st.write(f"### 🏟️ {home.upper()} vs {away.upper()}")
                        st.caption(f"KICK-OFF: {commence_time.strftime('%H:%M')} UTC")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if draw_signal:
                                st.write("📉 **LAY DRAW (BANCA)**")
                                liability = (q_d_b - 1) * target_stake
                                st.metric("SE PERDI (PERDITA)", f"-{liability:.2f} €")
                                st.metric("SE VINCI (PROFITTO)", f"+{target_stake:.2f} €")
                                st.write(f"Prob. Draw: {round((1/q_d_b)*100, 1)}%")
                            else: st.write("---")

                        with col2:
                            if over_signal:
                                st.write("⚽ **OVER 2.5 (PUNTA)**")
                                profit_net = (q_o_b * target_stake) - target_stake
                                st.metric("SE PERDI (PERDITA)", f"-{target_stake:.2f} €")
                                st.metric("SE VINCI (PROFITTO)", f"+{profit_net:.2f} €")
                                st.write(f"Prob. Over: {round((1/q_o_b)*100, 1)}%")
                            else: st.write("---")

                        with col3:
                            st.write("📋 **STATUS TRADE**")
                            if draw_signal: st.warning(f"Gap Draw: +{round(q_d_b-q_d_m, 2)}")
                            if over_signal: st.success(f"Gap Over: +{round(q_o_b-q_o_m, 2)}")
                            q_url = urllib.parse.quote(f"{home} {away}")
                            st.link_button("VAI SU BETFAIR", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")

            if found == 0:
                st.info("Nessuna partita trovata con i filtri attuali. Prova ad aumentare le 'Ore' o ridurre il 'Min Gap'.")
