# AquaVerify AI — Latest Cumulative Build Validation

Validated on the packaged source tree:

- `python -m pytest -q` → **18 passed**
- `python preflight.py` → **AquaVerify preflight: PASS**
- `app.py`, `database/db.py`, and all `src/*.py` compile successfully.

This cumulative build includes:

- latest cleaned Streamlit UI
- full citizen observation workflow
- consistency rules and reference-rarity checks
- Isolation Forest + One-Class SVM novelty screening
- human-in-the-loop edit/keep flow
- SQLite persistence with Windows-safe connection handling
- researcher dashboard and triage queue
- full observation display for researcher review
- mandatory researcher review acknowledgement before saving review status
- models, data, tests, docs, and preflight validation

Runtime-generated SQLite database files are intentionally not packaged.
