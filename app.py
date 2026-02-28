import streamlit as st
import requests
import pandas as pd

# Configurazione Pagina
st.set_page_config(page_title="AI Football Strategy", layout="wide")

st.title("⚽ Football Strategy Scanner")
st.sidebar.header("Impostazioni")

# Inserimento Chiave API
api_key = st.sidebar.text_input("Inserisci RapidAPI Key", value="396e380fa1mshf7c7a1309bbd354p1d80a0jsn289c1b466a49", type="password")

# Selezione Campionato
leagues = {
    "Olanda - Eerste Divisie (Top Over)": 89,
    "Norvegia - Eliteserien": 269,
    "Giappone - J1 League": 98,
    "Islanda - Urvalsdeild": 172,
    "Brasile - Serie A": 71
}
selected_league = st.selectbox("Scegli un campionato da analizzare:", list(leagues.keys()))
bankroll = st.sidebar.number_input("Il tuo Budget (€)", value=100.0)

def get_data(league_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    # Simulazione chiamata per i prossimi match (Next 10)
    params = {"league": league_id, "season": 2026, "next": 10}
    # response = requests.get(url, headers=headers, params=params)
    # return response.json()
    return None # Placeholder per test

# Layout a colonne
col1, col2, col3 = st.columns(3)

with col1:
    st.header("🔥 BTTS & Over")
    st.info("Cerca: Squadre con difese aperte e attacchi costanti.")
    # Esempio di visualizzazione
    st.write("**Match:** Ajax vs PSV")
    st.write("Probabilità BTTS: 72%")
    st.success("Consiglio: Puntare 4.50€ (Kelly)")

with col2:
    st.header("🕒 Late Goal (75'+)")
    st.info("Match ideali per il 'Live Betting'.")
    st.write("**Match:** Molde vs Bodo/Glimt")
    st.warning("Trend: 40% dei gol segnati nel finale.")

with col3:
    st.header("📉 Lay the Draw")
    st.info("Pochi pareggi storici tra queste squadre.")
    st.write("**Match:** Kawasaki Frontale vs Urawa")
    st.error("Prob. Pareggio: 12% - Strategia Valida")

# Grafico delle Statistiche (Esempio visivo)
st.divider()
st.subheader("Analisi Statistica Temporale")
chart_data = pd.DataFrame({
    'Minuti': ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'],
    'Frequenza Gol': [10, 15, 20, 18, 25, 42] # Tipico dei campionati esotici
})
st.bar_chart(chart_data.set_index('Minuti'))
