"""Stats screen: cumulative completed-round statistics and turn quality."""

import pandas as pd
import streamlit as st

from game import game_summary

st.title("📊 Your stats")
st.caption("Only completed rounds appear here. Stats belong to your current browser session.")
history = st.session_state.history
stats = game_summary(history)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Games played", stats["games"])
c2.metric("Games won", stats["wins"])
c3.metric("Avg. guesses / game", f"{stats['avg_guesses']:.1f}")
c4.metric("Win rate", f"{stats['win_rate']:.0f}%")

if not history:
    st.info("No completed games yet. Play a round, win, run out of turns, or reveal the answer to see your results.")
    st.stop()

st.subheader("Guesses by game")
chart = pd.DataFrame({
    "Game": [f"Game {i}" for i in range(1, len(history) + 1)],
    "Guesses": [game["guesses"] for game in history],
})
st.bar_chart(chart, x="Game", y="Guesses", x_label="Finished game", y_label="Number of guesses")

st.subheader("How informative were your questions?")
st.metric("Average turn quality", f"{stats['avg_quality']:.1f}%")
st.write(
    "**Quality = (candidates eliminated ÷ candidates remaining before the turn) × 100.** "
    "It measures how much that question or animal guess narrowed the list. "
    "For example, ruling out 10 of 20 remaining animals scores 50%. "
    "Repeated questions and incorrect guesses already eliminated score 0%. "
    "A correct final guess can score highly. This is a transparent heuristic, not an LLM opinion."
)

rows = [
    {"Game": f"Game {i}", "Outcome": game["outcome"], "Animal": game["animal"],
     "Guesses": game["guesses"], "Average quality (%)": game["avg_quality"]}
    for i, game in enumerate(history, 1)
]
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# The detailed per-turn chart makes the score auditable rather than mysterious.
selected = st.selectbox("Inspect a game", list(range(1, len(history) + 1)),
                        format_func=lambda i: f"Game {i} · {history[i-1]['outcome']}",
                        index=len(history) - 1)
turns = history[selected - 1]["turns"]
if turns:
    detail = pd.DataFrame([
        {"Turn": f"{i}", "Reduction (%)": t["quality"]}
        for i, t in enumerate(turns, 1)
    ])
    st.bar_chart(detail, x="Turn", y="Reduction (%)", y_label="Candidates eliminated (%)")
    st.dataframe(pd.DataFrame([
        {"Turn": i, "Your message": t["text"], "Answer": t["answer"],
         "Before": t["before"], "After": t["after"],
         "Eliminated": t["removed"], "Quality (%)": t["quality"]}
        for i, t in enumerate(turns, 1)
    ]), hide_index=True, use_container_width=True)
else:
    st.info("This round was revealed before any guesses were made.")

if st.button("Clear session stats"):
    st.session_state.history = []
    st.rerun()
