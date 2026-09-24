from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from database.db import (  # noqa: E402
    fetch_observation,
    fetch_observations,
    save_completed_review,
    update_researcher_review,
)
from engine import analyze_observation  # noqa: E402


OBS = {
    "channel_form": "flat",
    "bottom_type": "artificial",
    "bank_type": "artificial",
    "habitats_present": "no",
    "natural_debris_present": "no",
    "water_flow": "stagnant_intermittent",
    "water_aspect": "altered_color",
    "barriers_present": "yes",
    "draining_pipes": "yes",
    "sewage_discharge": "yes",
    "construction_in_stream": "yes",
    "impervious_area": "both_sides",
    "riparian_vegetation": "none",
    "vegetation_cuts": "yes",
    "overall_ecosystem_quality": "poor",
    "site_name": "Database Test Stream",
    "observer_note": "test",
}


def test_database_roundtrip_and_duplicate_protection(tmp_path):
    db = tmp_path / "test.db"
    analysis = analyze_observation(OBS)
    first_id = save_completed_review(
        submission_uuid="test-uuid-1",
        original_observation=OBS,
        final_observation=OBS,
        original_analysis=analysis,
        final_analysis=analysis,
        user_decision="accepted_without_correction",
        db_path=db,
    )
    second_id = save_completed_review(
        submission_uuid="test-uuid-1",
        original_observation=OBS,
        final_observation=OBS,
        original_analysis=analysis,
        final_analysis=analysis,
        user_decision="accepted_without_correction",
        db_path=db,
    )
    assert first_id == second_id
    rows = fetch_observations(db)
    assert len(rows) == 1
    assert rows[0]["site_name"] == "Database Test Stream"
    assert rows[0]["researcher_attention_suggested"] == 1
    assert rows[0]["researcher_review_status"] == "pending"


def test_researcher_review_update(tmp_path):
    db = tmp_path / "test.db"
    analysis = analyze_observation(OBS)
    obs_id = save_completed_review(
        submission_uuid="test-uuid-2",
        original_observation=OBS,
        final_observation=OBS,
        original_analysis=analysis,
        final_analysis=analysis,
        user_decision="accepted_without_correction",
        db_path=db,
    )
    update_researcher_review(obs_id, "follow_up_recommended", "Visit site", db)
    row = fetch_observation(obs_id, db)
    assert row["researcher_review_status"] == "follow_up_recommended"
    assert row["researcher_note"] == "Visit site"
    assert row["researcher_reviewed_at"]
