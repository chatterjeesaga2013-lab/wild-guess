"""Play screen: a chat interface for the guessing game."""

import streamlit as st

from game import ANIMALS, FEATURES, MAX_TURNS, finish_game, new_game, play_turn
from llm import config, interpret, llm_enabled


def start_another():
    game = st.session_state.game
    # Starting over during a round records a forfeit rather than erasing turns.
    record = finish_game(game, "Given up") if not game["finished"] and game["turns"] else None
    if record:
        st.session_state.history.append(record)
    st.session_state.game = new_game()
    st.session_state.last_parser = None


st.title("🐾 Wild Guess")
st.write("Find the hidden animal. Every useful yes/no question narrows the field.")

settings = config()
game = st.session_state.game
left, middle, right = st.columns(3)
left.metric("Turns left", MAX_TURNS - len(game["turns"]))
middle.metric("Possible animals", len(game["candidates"]))
right.metric("Rounds finished", len(st.session_state.history))

if llm_enabled(settings):
    st.caption("🟢 AI interpreter configured · answers checked against fixed animal facts")
else:
    st.caption("🟡 Offline mode · common questions work without an API key; configure university credentials for AI understanding")
if st.session_state.get("last_parser"):
    st.caption(f"Last message interpreted by: **{st.session_state.last_parser}**" +
               (" (check your model, key and base URL if AI should be active)"
                if llm_enabled(settings) and st.session_state.last_parser == "offline" else ""))

with st.container(border=True):
    for message in game["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if game["finished"]:
    if game["won"]:
        st.success(f"Round complete! You found the {game['target']} in {len(game['turns'])} turns.")
    else:
        st.info(f"Round over. The animal was **{game['target']}**.")
    if st.button("Play another round", type="primary", use_container_width=True):
        start_another()
        st.rerun()
else:
    prompt = st.chat_input("Ask: 'Does it fly?' or 'Is it a tiger?'", max_chars=240)
    if prompt:
        action, parser_source = interpret(prompt, settings)
        st.session_state.last_parser = parser_source
        accepted, response, record = play_turn(game, prompt, action)
        # Keep feedback for malformed or off-topic inputs, but do not spend a turn.
        game["messages"].extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
        ])
        if record:
            st.session_state.history.append(record)
        st.rerun()

col_new, col_end = st.columns(2)
with col_new:
    if st.button("🔄 New animal", use_container_width=True):
        start_another()
        st.rerun()
with col_end:
    if not game["finished"] and st.button("🏳️ Reveal and end", use_container_width=True):
        record = finish_game(game, "Given up")
        if record:
            st.session_state.history.append(record)
        game["messages"].append({"role": "assistant", "content": f"The animal was **{game['target']}**."})
        st.rerun()

with st.expander(f"See the {len(ANIMALS)} possible animals and supported topics"):
    st.write("**Possible animals:** " + ", ".join(sorted(ANIMALS)) + ".")
    st.write("**Supported question examples:**")
    st.write(" · ".join(FEATURES.values()))
    st.caption("The app recognizes different phrasings for supported facts. Unrecognized questions do not cost a turn.")
