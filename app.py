"""Entrypoint for the Wild Guess Streamlit app."""

import streamlit as st

from game import new_game

st.set_page_config(page_title="Wild Guess", page_icon="🐾", layout="wide")

if "game" not in st.session_state:
    st.session_state.game = new_game()
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.markdown("## 🐾 Wild Guess")
    st.caption("Twenty questions meets wildlife trivia")
    st.markdown("Ask yes/no questions, narrow the possibilities, and guess the secret animal before 12 turns run out.")
    st.divider()
    st.caption("Stats are saved for this browser session. Refreshing or restarting the app can reset them.")

page = st.navigation([
    st.Page("pages/play.py", title="Play", icon="🎮", default=True),
    st.Page("pages/stats.py", title="Stats", icon="📊"),
])
page.run()
