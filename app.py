import streamlit as st
import requests

st.set_page_config(page_title="AI Strategy Scanner - SOLO SEGNALI", layout="wide", page_icon="🎯")
st.title("🎯 Football Value Signals Only")

# --- CONFIGURAZIONE ---
API_KEY = "27593156a4d63edc49b283e86937f0e9"
bankroll = st.sidebar.number_input("Budget Totale (€)", value=100.0)

# Parametri di Filtro (Puoi regolarli dalla sidebar)
st.sidebar.divider()
st.sidebar.subheader("Filtri Strategia")
max_over_odds = st.sidebar.slider("Max Quota Over 2.5", 1.40, 2.00, 1.75)
min_draw_lay = st.sidebar.slider("Min Quota Lay Draw", 3.00, 4.00, 3.20)
max_draw_lay = st.sidebar.slider("Max Quota Lay Draw", 4.00, 6.00, 4.50)

# --- FUNZIONI API ---
@st.cache_data(ttl=3600)
def get_active_leagues():
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        return {s['title']: s['key'] for s in response.json() if s.get('group') == "Soccer"}
    except: return {}

def get_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        response = requests.get(url, params=params)
        return response.status_code, response.json()
    except: return 500, []

# --- LOGICA DI FILTRO E VISUALIZZAZIONE ---
leagues = get_active_leagues()

if leagues:
    selected_name = st.selectbox("🎯 Seleziona Campionato:", list(leagues.keys()))
    sport_key = leagues[selected_name]

    if st.button("🚀 CERCA SEGNALI"):
        status, data = get_odds(sport_key)
        
        if status == 200 and data:
            segnali_trovati = 0
            
            for match in data:
                home = match.get('home_team')
                away = match.get('away_team')
                
                # Estrazione quote
                if not match['bookmakers']: continue
                markets = match['bookmakers'][0]['markets']
                h2h = next((m for m in markets if m['key'] == 'h2h'), None)
                totals = next((m for m in markets if m['key'] == 'totals'), None)
                
                # Valori delle quote
                over_q = next((o['price'] for o in totals['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), 10.0) if totals else 10.0
                draw_q = next((o['price'] for o in h2h['outcomes'] if o['name'] == 'Draw'), 1.0) if h2h else 1.0
                
                # --- LOGICA DEI FILTRI (Solo se interessanti) ---
                is_over_signal = over_q <= max_over_odds
                is_lay_signal = min_draw_lay <= draw_q <= max_draw_lay
                
                if is_over_signal or is_lay_signal:
                    segnali_trovati += 1
                    with st.container():
                        st.markdown(f"### 🔥 SEGNALE: {home} vs {away}")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if is_over_signal:
                                st.success(f"**OVER 2.5 CONSIGLIATO**\n\nQuota: {over_q}")
                            else:
                                st.write("Over 2.5: No segnale")
                                
                        with col2:
                            if is_lay_signal:
                                st.success(f"**LAY THE DRAW IDEALE**\n\nQuota: {draw_q}")
                            else:
                                st.write("Lay Draw: No segnale")
                                
                        with col3:
                            search_query = f"{home} {away} live score".replace(" ", "+")
                            st.link_button("📺 MONITOR LIVE", f"https://www.google.com/search?q={search_query}")
                        
                        st.divider()
            
            if segnali_trovati == 0:
                st.info("Nessun match interessante trovato con i filtri attuali. Prova un altro campionato o allarga i parametri.")
        else:
            st.warning("Dati non disponibili.")
else:
    st.error("Errore API.")
