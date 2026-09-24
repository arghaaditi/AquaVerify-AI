from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from engine import analyze_observation


BASE_OBS = {
    "channel_form": "v_shape",
    "bottom_type": "natural",
    "bank_type": "natural",
    "habitats_present": "yes",
    "natural_debris_present": "yes",
    "water_flow": "fast",
    "water_aspect": "clear_transparent",
    "barriers_present": "no",
    "draining_pipes": "no",
    "sewage_discharge": "no",
    "construction_in_stream": "no",
    "impervious_area": "none",
    "riparian_vegetation": "both_sides",
    "vegetation_cuts": "no",
    "overall_ecosystem_quality": "good",
}


def test_invalid_input_blocks_ml():
    result = analyze_observation({"overall_ecosystem_quality": "good"})
    assert result["analysis_status"] == "invalid_input"
    assert result["ml_novelty"] is None


def test_sewage_good_rule_fires():
    obs = BASE_OBS.copy()
    obs["sewage_discharge"] = "yes"
    result = analyze_observation(obs)
    ids = {x["rule_id"] for x in result["consistency"]["rule_flags"]}
    assert "R01_SEWAGE_GOOD" in ids


def test_engine_never_returns_numeric_consistency_score_yet():
    result = analyze_observation(BASE_OBS)
    assert result["score_policy"]["observation_consistency_score"] is None


def test_human_control_message_present():
    result = analyze_observation(BASE_OBS)
    assert "never changes" in result["explanation"]["human_control_message"].lower()


def test_consistent_concerning_observation_does_not_force_citizen_correction():
    obs = BASE_OBS.copy()
    obs.update({
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
    })
    result = analyze_observation(obs)
    assert result["review"]["citizen_review_needed"] is False
    assert result["review"]["researcher_attention_suggested"] is True
