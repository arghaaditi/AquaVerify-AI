# AquaVerify AI

**Human-in-the-Loop Quality Control for Citizen Stream Assessments**

AquaVerify is a lightweight Streamlit prototype that helps citizens and researchers review structured stream observations before those observations are used for research triage. It combines transparent consistency rules, reference-data rarity checks, two novelty-detection models, explainable evidence, human confirmation/correction, SQLite persistence, and a researcher dashboard.

> **Prototype boundary:** AquaVerify screens observation consistency, unusual patterns, and review priority. It does **not** diagnose pollution, drinking-water safety, pathogens, chemical concentrations, regulatory compliance, or laboratory water quality.

## The problem

Citizen-science observations can scale environmental monitoring, but structured submissions may contain missing values, internally inconsistent judgments, or unusual combinations that deserve another look. Manually reviewing every record does not scale well.

AquaVerify focuses on a narrower and defensible question:

> **Which citizen observations deserve another look, why, and who should review them?**

## Core workflow

```text
Citizen observation
        ↓
Basic schema validation
        ↓
Consistency rule engine
        ↓
Conditional rarity check
        ↓
Isolation Forest + One-Class SVM
        ↓
Evidence-based explanation
        ↓
Citizen: Edit or Keep Answers
        ↓
Final reviewed observation
        ↓
SQLite audit trail
        ↓
Researcher triage dashboard
```

## Important design distinction

AquaVerify separates two questions that should not be conflated:

1. **Citizen-data consistency:** Do the detailed fields and the citizen's overall assessment deserve review?
2. **Environmental concern triage:** Does the submitted observation contain pressure/context indicators worth surfacing to a researcher?

A concerning stream observation can still be **high-quality citizen data**. AquaVerify therefore does not force a citizen to change a consistent observation merely because it contains concerning environmental indicators.

## AI / ML approach

### 1. Transparent consistency rules
Known, explainable conflicts are handled explicitly. Example: a reported sewage discharge combined with an overall ecosystem assessment of `Good` is surfaced for review rather than silently corrected.

### 2. Conditional rarity
For each overall-assessment group, AquaVerify compares feature values with the reference dataset and surfaces unusually rare combinations. This supports evidence-based explanations such as “this field value is uncommon among reference observations with the same overall assessment.”

### 3. Novelty detection
The detailed observation fields are evaluated by two lightweight novelty detectors:

- **Isolation Forest**
- **One-Class SVM**

The citizen's `overall_ecosystem_quality` summary is intentionally **not** used as a novelty-model feature. It is checked separately by rules and conditional statistics so that the ML layer cannot simply learn the synthetic relationship between detailed observations and the summary label.

The model layer returns a **review signal**, not a truth label.

## Human-in-the-loop design

AquaVerify never changes a citizen answer automatically.

When data-quality or novelty evidence is found, the citizen can:

- **Edit Observation**, then re-run every check; or
- **Keep My Answers**, preserving the original human judgment.

The database records the original submission, AI-assisted evidence, human decision, final submission, final evidence, and researcher review state.

## Research dashboard

The dashboard provides:

- stored observation count;
- revised-after-review count;
- researcher-triage count;
- pending-review count;
- final assessment distribution;
- human decision distribution;
- filtered triage queue;
- original-vs-final audit trail;
- researcher status and notes;
- searchable observation history;
- CSV export.

A clearly labelled demo-data tool can reset the local SQLite database and seed three canonical demonstration records.

## Synthetic-data disclosure

The bundled reference/training data are synthetic prototype data designed to exercise the workflow. They are **not** a validated ecological ground-truth dataset and must not be used to claim real-world scientific accuracy.

Production deployment would require expert-reviewed real observations, calibration, field validation, governance, and appropriate data-access controls.

## Technology stack

- Python
- Streamlit
- pandas / NumPy
- scikit-learn
- joblib
- SQLite
- pytest

No GPU, TensorFlow, PyTorch, or local LLM is required.

## Run locally

Recommended: Python 3.10 or newer.

### Windows

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
python preflight.py
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Demo scenarios

The sidebar contains three reproducible scenarios:

- **Healthy / consistent** — no citizen review, no concern-based triage.
- **Concerning but consistent** — no citizen correction, researcher triage suggested.
- **Contradictory assessment** — citizen review requested; changing the overall assessment from `Good` to `Poor` clears the consistency conflict while preserving concern indicators.

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for the recommended hackathon walkthrough.

## Testing

Run:

```bat
python -m pytest -q
```

The test suite covers engine behavior, database persistence, duplicate protection, researcher review updates, canonical demo scenarios, demo seeding, and package integrity.

See [`docs/TESTING.md`](docs/TESTING.md).

## Project structure

```text
aquaverify-ai/
├── app.py
├── src/
│   ├── engine.py
│   ├── basic_validation.py
│   ├── consistency_rules.py
│   ├── rarity_service.py
│   ├── anomaly_service.py
│   ├── concern_indicators.py
│   ├── explanation_layer.py
│   ├── demo_presets.py
│   └── presentation.py
├── database/
│   ├── db.py
│   └── demo_data.py
├── data/
├── models/
├── tests/
├── docs/
├── .streamlit/
├── requirements.txt
└── README.md
```

## Responsible-AI principles

- AI signals trigger **review**, not automatic correction.
- Citizen and researcher roles are distinct.
- Environmental concern screening is **triage**, not diagnosis.
- Synthetic data are disclosed as synthetic.
- No scientific accuracy percentage is claimed from synthetic stress tests.
- No arbitrary “water-health score” is presented.
- Final scientific interpretation may require expert review, field verification, or laboratory measurements.

## Current limitations

- Reference data are synthetic.
- Rules and rarity thresholds require domain-expert calibration before real deployment.
- Novelty-model performance has not been validated on representative real-world observations.
- SQLite is suitable for the hackathon/local prototype, not a multi-user production deployment.
- Authentication, role-based access, privacy policy, retention controls, and managed backups are not implemented.

## Status

**Hackathon build:** the core workflow, human review, persistence, researcher dashboard, demo controls, documentation, and automated scenario testing are included.
