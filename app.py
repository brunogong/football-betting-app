import streamlit as st
import requests

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Odds Strategy Scanner", layout="wide")
st.title("📊 Betting Value & Strategy Scanner")

# --- PARAMETRI ---
API_KEY = "27593156a4d63edc49b283e86937f0e9"
REGIONS = 'eu' # Mercati europei
MARKETS = 'h2h,totals' # h2h per Lay the Draw, totals per Over/Under
ODDS_FORMAT = 'decimal'

# --- SIDEBAR ---
st.sidebar.header("⚙️ Filtri Strategia")
bankroll = st.sidebar.number_input("Bankroll Totale (€)", value=100.0)
min_odds_draw = st.sidebar.slider("Quota minima Pareggio (Lay)", 3.0, 5.0, 3.4)

# Mappa campionati (The Odds API usa nomi specifici)
leagues = {
    "Olanda - Eredivisie": "soccer_netherlands_ereerste_divisie",
    "Norvegia - Eliteserien": "soccer_norway_eliteserien",
    "Italia - Serie A": "soccer_italy_serie_a",
    "Inghilterra - Premier League": "soccer_league_premier_league",
    "Brasile - Serie A": "soccer_brazil_campeonato",
    "Giappone - J1 League": "soccer_japan_j_league"
}
selected_league = st.selectbox("🎯 Scegli il campionato:", list(leagues.keys()))
sport_key = leagues[selected_league]

# --- FUNZIONE RECUPERO QUOTE ---
def get_odds(sport):
    url = f"https://api.the-odds-api.com/v1/sports/{sport}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT
    }
    response = requests.get(url, params=params)
    return response.status_code, response.json()

# --- ANALISI ---
if st.button("🔍 SCANSIONA MERCATI"):
    status, data = get_odds(sport_key)
    
    if status == 200:
        st.subheader(f"Analisi quote in tempo reale: {selected_league}")
        
        for match in data:
            home_team = match['home_team']
            away_team = match['away_team']
            
            # Estrazione quote (usiamo il primo bookmaker disponibile per semplicità)
            if not match['bookmakers']: continue
            
            bookie = match['bookmakers'][0] # Prende il primo bookie della lista
            h2h_market = next((m for m in bookie['markets'] if m['key'] == 'h2h'), None)
            totals_market = next((m for m in bookie['markets'] if m['key'] == 'totals'), None)
            
            with st.expander(f"🏟️ {home_team} vs {away_team}"):
                c1, c2, c3 = st.columns(3)
                
                # 1. LAY THE DRAW
                with c1:
                    st.markdown("### 📉 Lay the Draw")
                    if h2h_market:
                        draw_price = next((o['price'] for o in h2h_market['outcomes'] if o['name'] == 'Draw'), None)
                        st.write(f"Quota Pareggio: **{draw_price}**")
                        if draw_price and draw_price >= min_odds_draw:
                            st.success("✅ CONSIGLIATO: Quota ideale per bancare.")
                        else:
                            st.warning("⚠️ Quota troppo bassa per Lay.")

                # 2. OVER 2.5 / BTTS
                with c2:
                    st.markdown("### 🔥 Over 2.5 Strategy")
                    if totals_market:
                        over_25 = next((o['price'] for o in totals_market['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5), None)
                        st.write(f"Quota Over 2.5: **{over_25 if over_25 else 'N/A'}**")
                        if over_25 and over_25 < 1.80:
                            st.info("Trend Over confermato dai Bookie.")

                # 3. STAKE & VALUE (Kelly)
                with c3:
                    st.markdown("### 💰 Gestione Stake")
                    stake = round(bankroll * 0.02, 2)
                    st.write(f"Stake suggerito (2%): **{stake}€**")
                    st.write("Strategia: **Prudenziale**")
                    
    elif status == 401:
        st.error("Chiave API non valida. Verifica l'email di The Odds API.")
    else:
        st.error(f"Errore {status}: {data}")

st.sidebar.divider()
st.sidebar.write("📌 **Note Strategiche:**")
st.sidebar.caption("- Lay the Draw: Banca se la quota è > 3.40.")
st.sidebar.caption("- Late Goal: Se il match è 0-0 al 75', punta Over 0.5.")
