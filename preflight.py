"""Fast local pre-demo validation for AquaVerify.

Run after installing requirements:
    python preflight.py
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from database.db import fetch_observations
from database.demo_data import seed_demo_database
from demo_presets import PRESETS
from engine import analyze_observation


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)
    print(f"PASS  {message}")


def main():
    print("AquaVerify preflight\n")
    for rel in [
        "models/IsolationForest.joblib",
        "models/OneClassSVM.joblib",
        "models/model_thresholds.json",
        "data/reference_train.csv",
        "data/conditional_rarity_table.csv",
    ]:
        require((ROOT / rel).exists(), f"required artifact exists: {rel}")

    healthy = analyze_observation(PRESETS["Healthy / consistent"])
    require(not healthy["review"]["citizen_review_needed"], "healthy case does not request citizen correction")
    require(not healthy["review"]["researcher_attention_suggested"], "healthy case does not request researcher triage")

    concern = analyze_observation(PRESETS["Concerning but consistent"])
    require(not concern["review"]["citizen_review_needed"], "concerning-consistent case keeps citizen data accepted")
    require(concern["review"]["researcher_attention_suggested"], "concerning-consistent case requests researcher triage")

    contradiction = analyze_observation(PRESETS["Contradictory assessment"])
    require(contradiction["review"]["citizen_review_needed"], "contradictory case requests citizen review")

    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / "preflight.db"
        seed_demo_database(db, reset_first=True)
        rows = fetch_observations(db)
        require(len(rows) == 3, "demo database seeds exactly three canonical records")
        require(sum(bool(r["had_revision"]) for r in rows) == 1, "demo database contains one revised workflow")

    print("\nAquaVerify preflight: PASS")


if __name__ == "__main__":
    main()
