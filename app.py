import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="ALPHA SCANNER - RISK CONTROL", layout="wide")

# CSS per evidenziare il Rischio
st.markdown("""
    <style>
    .stMetric { background-color: #111827; border: 1px solid #374151; padding: 15px; border-radius: 10px; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "27593156a4d63edc49b283e86937f0e9"

# --- 2. HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🛡️ Risk-Control Trader")
    st.caption("Focus esclusivo sulla Responsabilità (Liability) e capitale impegnato.")
with c2:
    st.metric("UTC TIME", datetime.now(timezone.utc).strftime("%H:%M"))

# --- 3. SIDEBAR: MONEY MANAGEMENT ---
st.sidebar.header("🕹️ SETTINGS")
bankroll = st.sidebar.number_input("CAPITALE DISPONIBILE (€)", value=500.0, step=50.0)
stake_pct = st.sidebar.slider("STAKE TARGET (%)", 0.5, 5.0, 2.0)
# Questo è l'importo base che vuoi vincere (o puntare)
target_stake = (bankroll * stake_pct) / 100

st.sidebar.divider()
val_diff_draw = st.sidebar.slider("Soglia Valore Pareggio", 0.10, 1.00, 0.25)
val_diff_over = st.sidebar.slider("Soglia Valore Over 2.5", 0.05, 0.50, 0.10)
hours_filter = st.sidebar.number_input("Orizzonte Ore", value=4)

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

# --- 5. LOGICA OPERATIVA ---
leagues_dict = get_leagues()
if leagues_dict:
    sel_league = st.selectbox("Seleziona Campionato:", list(leagues_dict.keys()))
    
    if st.button("ANALIZZA RISCHIO MERCATI"):
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
                
                # Quote Draw
                q_d_m = next((o['price'] for m in m1 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                q_d_b = next((o['price'] for m in m2 if m['key'] == 'h2h' for o in m['outcomes'] if o['name'] == 'Draw'), 0)
                
                # Quote Over 2.5
                q_o_m = next((o['price'] for m in m1 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)
                q_o_b = next((o['price'] for m in m2 if m['key'] == 'totals' for o in m['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 0)

                if (q_d_b - q_d_m) >= val_diff_draw or (q_o_b - q_o_m) >= val_diff_over:
                    found += 1
                    with st.container():
                        st.subheader(f"{home} vs {away}")
                        col1, col2, col3 = st.columns(3)
                        
                        # --- COLONNA LAY (BANCA) ---
                        with col1:
                            st.markdown("### 📉 BANCA PAREGGIO")
                            if (q_d_b - q_d_m) >= val_diff_draw:
                                # CALCOLO RISCHIO VERO (Responsabilità)
                                liability = (q_d_b - 1) * target_stake
                                st.error("⚠️ AZIONE: BANCA (Rosa)")
                                st.metric("RISCHIO EFFETTIVO", f"{liability:.2f} €")
                                st.caption(f"Quota: {q_d_b} | Se vinci: +{target_stake:.2f}€")
                            else:
                                st.info("Nessun Gap di valore")

                        # --- COLONNA BACK (PUNTA) ---
                        with col2:
                            st.markdown("### ⚽ PUNTA OVER 2.5")
                            if (q_o_b - q_o_m) >= val_diff_over:
                                # CALCOLO RISCHIO VERO (Lo Stake stesso)
                                st.success("✅ AZIONE: PUNTA (Blu)")
                                st.metric("RISCHIO EFFETTIVO", f"{target_stake:.2f} €")
                                potential = (q_o_b * target_stake) - target_stake
                                st.caption(f"Quota: {q_o_b} | Se vinci: +{potential:.2f}€")
                            else:
                                st.info("Nessun Gap di valore")

                        # --- AZIONE ---
                        with col3:
                            st.write("")
                            q_url = urllib.parse.quote(f"{home} {away}")
                            st.link_button("VAI AL MERCATO", f"https://www.betfair.it/exchange/plus/football/search?searchTerm={q_url}")

            if found == 0:
                st.warning("Nessun match trovato con i criteri di rischio impostati.")
