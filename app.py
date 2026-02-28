import streamlit as st
import requests

st.set_page_config(page_title="AI Pro Scanner v4", layout="wide", page_icon="⚽")
st.title("⚽ Live Strategy & Odds Scanner")

# --- CONFIGURAZIONE ---
API_KEY = "27593156a4d63edc49b283e86937f0e9"
bankroll = st.sidebar.number_input("Budget Totale (€)", value=100.0)

# --- FUNZIONI API v4 ---
@st.cache_data(ttl=3600)
def get_active_leagues():
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            all_sports = response.json()
            return {s['title']: s['key'] for s in all_sports if s.get('group') == "Soccer"}
        return {}
    except: return {}

def get_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        response = requests.get(url, params=params)
        return response.status_code, response.json()
    except: return 500, []

# --- INTERFACCIA ---
leagues = get_active_leagues()

if leagues:
    selected_name = st.selectbox("🎯 Seleziona Campionato:", list(leagues.keys()))
    sport_key = leagues[selected_name]

    if st.button("🚀 ANALIZZA MATCH"):
        status, data = get_odds(sport_key)
        
        if status == 200 and data:
            for match in data:
                home = match.get('home_team')
                away = match.get('away_team')
                
                # Estrazione quote dal primo bookmaker
                if not match['bookmakers']: continue
                markets = match['bookmakers'][0]['markets']
                h2h = next((m for m in markets if m['key'] == 'h2h'), None)
                totals = next((m for m in markets if m['key'] == 'totals'), None)

                with st.expander(f"🏟️ {home} vs {away}"):
                    c1, c2, c3 = st.columns(3)
                    
                    # 1. OVER 2.5
                    with c1:
                        st.markdown("### 🔥 Over 2.5")
                        over_q = next((o['price'] for o in totals['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), None) if totals else "N/A"
                        st.write(f"Quota: **{over_q}**")
                        if isinstance(over_q, float) and over_q < 1.80:
                            st.success("✅ CONSIGLIATO")
                        else: st.info("Analisi Live richiesta")

                    # 2. LAY THE DRAW
                    with c2:
                        st.markdown("### 📉 Lay Draw")
                        draw_q = next((o['price'] for o in h2h['outcomes'] if o['name'] == 'Draw'), None) if h2h else "N/A"
                        st.write(f"Quota: **{draw_q}**")
                        if isinstance(draw_q, float) and 3.20 <= draw_q <= 4.20:
                            st.success("💎 IDEALE")
                        else: st.warning("Rischio Alto")

                    # 3. LIVE & LATE GOAL
                    with c3:
                        st.markdown("### 🕒 Live Tracker")
                        search_query = f"{home} {away} live score".replace(" ", "+")
                        link = f"https://www.google.com/search?q={search_query}"
                        st.link_button("👉 Vai al LIVE", link)
                        st.caption("Controlla al 75' per Late Goal")
                    
                    st.write(f"✍️ **Stake consigliato (2%): {bankroll * 0.02:.2f}€**")
        else:
            st.warning("Nessun dato disponibile per questo campionato al momento.")
else:
    st.error("Errore di connessione API. Controlla la chiave.")

st.sidebar.divider()
st.sidebar.info("Strategia v4: Dati aggiornati in tempo reale dai bookmaker europei.")
