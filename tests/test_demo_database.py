from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from database.db import fetch_observations, delete_all_observations
from database.demo_data import seed_demo_database


def test_seed_demo_database_creates_canonical_three_records(tmp_path):
    db = tmp_path / "demo.db"
    ids = seed_demo_database(db, reset_first=True)
    rows = fetch_observations(db)
    assert len(ids) == 3
    assert len(rows) == 3
    assert sum(bool(r["had_revision"]) for r in rows) == 1
    assert sum(bool(r["researcher_attention_suggested"]) for r in rows) == 2
    assert sum(r["researcher_review_status"] == "pending" for r in rows) == 1
    assert sum(r["researcher_review_status"] == "follow_up_recommended" for r in rows) == 1


def test_seed_demo_database_is_idempotent(tmp_path):
    db = tmp_path / "demo.db"
    seed_demo_database(db, reset_first=True)
    seed_demo_database(db, reset_first=False)
    assert len(fetch_observations(db)) == 3


def test_delete_all_observations_clears_database(tmp_path):
    db = tmp_path / "demo.db"
    seed_demo_database(db, reset_first=True)
    delete_all_observations(db)
    assert fetch_observations(db) == []
