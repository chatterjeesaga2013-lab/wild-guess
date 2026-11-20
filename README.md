# Wild Guess 🐾

A small Streamlit animal guessing game for the Vips task. One of 30 animals is selected secretly. The player asks yes/no questions, uses up to 12 turns, and tries to name it. The **Play** page uses Streamlit's chat components; **Stats** shows completed rounds and how informative each turn was.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

It also works **without an API key** in offline mode, with a smaller set of recognized phrasings. For full natural-language processing, request a key at https://ai-keys.uni-osnabrueck.de and check the portal for the exact API base URL and currently available model ID. The university uses an OpenAI-compatible API; the correct model/base URL are **not hardcoded** because they may change.

Create `.streamlit/secrets.toml` using `.streamlit/secrets.toml.example` as a guide:

```toml
UOS_API_KEY = "your-key"
UOS_BASE_URL = "base-url-from-portal"
UOS_MODEL = "model-id-from-portal"
```

Alternative: set the three corresponding environment variables. Do not include the real key in GitHub or the submission ZIP.

**Design:** The LLM interprets what a question means. The answer itself is computed from a local animal fact bank. This prevents the language model from giving conflicting answers about the same animal. Questions the fact bank does not support get a helpful prompt to rephrase; unknown inputs do not spend a turn. If the model service is down, the app falls back to simple keyword rules so it remains playable. If the game is restarted mid-round after at least one turn, the unfinished game is recorded as given up. Games in progress are excluded from the stats.

## Score explanation

The game tracks a candidate list that is consistent with every answered question. For each valid turn:

`quality (%) = 100 × (number of candidates eliminated on this turn / candidates before this turn)`

For example, if 24 animals remain and your question reduces that to 12, the quality is 50%. A repeated question eliminates zero and scores 0%. A correct animal guess narrows the list to the correct answer. This is a simple measure of **information gained**, not a subjective LLM score. Stats includes the average quality and a chart plus audit table for each turn.

Stats use Streamlit session state: they are private to the browser session, but may disappear on refresh/reconnection/server restart. It is not a persistent database.

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

To test the full AI mode, configure a valid university key/base URL/model and manually try: "Does it usually hunt at night?", "Could this animal survive in the ocean?", "Is it a mammal?", and "I think the answer is a polar bear." AI mode requires external network connectivity and cannot be fully tested without valid credentials.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and upload the files in this folder. Keep `app.py` in the repository root.
2. At https://share.streamlit.io/ sign in, choose **Create app**, connect your repository, and select `app.py` as the main file.
3. Add your three `UOS_*` settings in your app's **Secrets** settings (using the TOML lines above). Do not commit the secret file.
4. Deploy, open the URL you receive, play a game, and check Stats. If your university API is inaccessible from the cloud, check the key/network policies and keep using the offline fallback until access is arranged.
5. Hand in: **this source ZIP or GitHub URL**, **your actual public Streamlit app URL**, and the **Who did what?** section in `CONTRIBUTIONS.md` filled out honestly.

## Project files

- `app.py`: Streamlit navigation and common sidebar
- `pages/play.py`: chat interface and round controls
- `pages/stats.py`: summary, graphs, and explanation
- `game.py`: animal facts, scoring, and session-independent game rules
- `llm.py`: LLM interpreter with an offline fallback
- `tests/test_game.py`: unit tests

This project started from the minimal course template supplied with the assignment.
