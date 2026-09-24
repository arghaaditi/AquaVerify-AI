# AquaVerify Testing Guide

## Automated tests

Run:

```bat
python -m pytest -q
```

The suite tests:

- invalid input blocks ML;
- known consistency rule behavior;
- human-control explanation;
- concerning-but-consistent data does not force citizen correction;
- SQLite round-trip persistence;
- duplicate submission protection;
- researcher review updates;
- healthy canonical scenario;
- concerning-but-consistent canonical scenario;
- contradictory canonical scenario;
- contradictory Good → Poor revision behavior;
- human-readable presentation labels;
- seeded demo database contents;
- seed idempotency;
- database clear behavior;
- required submission-candidate files.

## Manual smoke test

1. `streamlit run app.py`
2. Load **Healthy / consistent** → review → accept.
3. Load **Concerning but consistent** → confirm no citizen correction is requested → accept.
4. Load **Contradictory assessment** → review → edit `Good` to `Poor` → review again → accept.
5. Open Research Dashboard.
6. Confirm revised/triage metrics and audit trail.
7. Update a researcher status and note.
8. Restart Streamlit and confirm SQLite persistence.
9. Download dashboard CSV.

## Clean demo-state test

On Research Dashboard, use the clearly labelled local demo tool:

**Reset & seed 3 canonical demo records**

Expected dashboard state:

- Stored observations: **3**
- Revised after review: **1**
- Researcher triage suggested: **2**
- Pending researcher review: **1**

The other triage record is intentionally seeded as **Follow-up recommended** to demonstrate researcher workflow state.
