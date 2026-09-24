from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from demo_presets import PRESETS
from engine import analyze_observation
from presentation import decision_label, researcher_status_label


def test_healthy_demo_has_no_review_or_triage_signal():
    result = analyze_observation(PRESETS["Healthy / consistent"])
    assert result["analysis_status"] == "complete"
    assert result["consistency"]["rule_flag_count"] == 0
    assert result["consistency"]["conditional_rarity"]["rare_field_count"] == 0
    assert result["concern_indicators"]["direct_pressure_count"] == 0
    assert result["concern_indicators"]["contextual_count"] == 0
    assert result["review"]["citizen_review_needed"] is False
    assert result["review"]["researcher_attention_suggested"] is False


def test_concerning_consistent_demo_triages_without_forcing_correction():
    result = analyze_observation(PRESETS["Concerning but consistent"])
    assert result["consistency"]["rule_flag_count"] == 0
    assert result["consistency"]["conditional_rarity"]["rare_field_count"] == 0
    assert result["review"]["citizen_review_needed"] is False
    assert result["review"]["researcher_attention_suggested"] is True
    total_concerns = (
        result["concern_indicators"]["direct_pressure_count"]
        + result["concern_indicators"]["contextual_count"]
    )
    assert total_concerns == 9


def test_contradictory_demo_requests_citizen_review():
    result = analyze_observation(PRESETS["Contradictory assessment"])
    assert result["consistency"]["rule_flag_count"] >= 1
    assert result["consistency"]["conditional_rarity"]["rare_field_count"] >= 1
    assert result["review"]["citizen_review_needed"] is True
    assert result["review"]["researcher_attention_suggested"] is True


def test_revising_contradictory_overall_assessment_clears_data_quality_review():
    original = PRESETS["Contradictory assessment"].copy()
    final = original.copy()
    final["overall_ecosystem_quality"] = "poor"
    before = analyze_observation(original)
    after = analyze_observation(final)
    assert before["review"]["citizen_review_needed"] is True
    assert after["review"]["citizen_review_needed"] is False
    assert after["review"]["researcher_attention_suggested"] is True
    assert after["consistency"]["rule_flag_count"] == 0
    assert after["consistency"]["conditional_rarity"]["rare_field_count"] == 0


def test_human_readable_internal_labels():
    assert decision_label("revised_and_accepted") == "Revised and accepted"
    assert researcher_status_label("follow_up_recommended") == "Follow-up recommended"
