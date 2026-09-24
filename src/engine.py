"""Single orchestration entry point for the AquaVerify Phase 2 backend engine."""
from basic_validation import normalize_observation, validate_observation
from consistency_rules import evaluate_rules
from rarity_service import analyze_conditional_rarity
from anomaly_service import analyze_novelty
from concern_indicators import analyze_concern_indicators
from explanation_layer import build_explanation
from config import ENGINE_VERSION


def _review_reasons(rule_flags, rarity, novelty, concerns):
    reasons = []
    if rule_flags:
        reasons.append({
            "source": "consistency_rules",
            "message": f"{len(rule_flags)} consistency rule(s) requested review.",
        })
    if rarity["rare_field_count"]:
        reasons.append({
            "source": "reference_rarity",
            "message": f"{rarity['rare_field_count']} field value(s) were uncommon within the same overall-assessment reference group.",
        })
    if novelty["signal_strength"] != "none":
        reasons.append({
            "source": "ml_novelty",
            "message": novelty["message"],
        })
    if concerns["direct_pressure_count"]:
        reasons.append({
            "source": "concern_triage",
            "message": concerns["triage_note"],
        })
    return reasons


def analyze_observation(observation: dict) -> dict:
    """Analyze one observation and return a structured evidence object.

    Important: the function does not calculate a scientific reliability score,
    diagnose pollution, or alter the citizen's submitted answers.
    """
    validation = validate_observation(observation)
    normalized = normalize_observation(observation) if isinstance(observation, dict) else {}

    if not validation["is_valid"]:
        return {
            "engine_version": ENGINE_VERSION,
            "analysis_status": "invalid_input",
            "normalized_observation": normalized,
            "basic_validation": validation,
            "consistency": None,
            "ml_novelty": None,
            "concern_indicators": None,
            "review": {
                "any_follow_up_needed": True,
                "citizen_review_needed": False,
                "researcher_attention_suggested": False,
                "blocked_by_validation": True,
                "reasons": [],
                "citizen_next_action": "Complete or correct the required fields before AI-assisted review.",
                "researcher_next_action": "No researcher triage is performed until basic validation passes.",
            },
            "explanation": {
                "headline": "Observation is incomplete or outside the prototype schema",
                "summary": "AquaVerify did not run consistency or ML checks because basic validation failed.",
                "sections": [{"title": "Validation", "items": validation["errors"]}],
                "human_control_message": "No citizen answer was changed.",
            },
        }

    rule_flags = evaluate_rules(normalized)
    rarity = analyze_conditional_rarity(normalized)
    novelty = analyze_novelty(normalized)
    concerns = analyze_concern_indicators(normalized)
    reasons = _review_reasons(rule_flags, rarity, novelty, concerns)

    # Review is requested by data-quality/novelty signals. Direct concern indicators
    # also create a researcher-review reason, but they do not imply inconsistent data.
    quality_review = bool(rule_flags or rarity["rare_field_count"] or novelty["signal_strength"] != "none")
    researcher_attention = concerns["triage_label"] in {"direct_pressure_reported", "multiple_context_signals"}
    any_follow_up = quality_review or researcher_attention

    explanation = build_explanation(rule_flags, rarity, novelty, concerns)

    return {
        "engine_version": ENGINE_VERSION,
        "analysis_status": "complete",
        "normalized_observation": normalized,
        "basic_validation": validation,
        "consistency": {
            "rule_flag_count": len(rule_flags),
            "strong_rule_count": sum(f["severity"] == "strong_review" for f in rule_flags),
            "rule_flags": rule_flags,
            "conditional_rarity": rarity,
        },
        "ml_novelty": novelty,
        "concern_indicators": concerns,
        "review": {
            "any_follow_up_needed": any_follow_up,
            "citizen_review_needed": quality_review,
            "researcher_attention_suggested": researcher_attention,
            "blocked_by_validation": False,
            "reasons": reasons,
            "citizen_next_action": (
                "Show the highlighted consistency/novelty evidence and offer 'Edit Observation' or 'Keep My Answers'."
                if quality_review
                else "Accept the citizen submission without asking for a correction."
            ),
            "researcher_next_action": (
                "Surface this observation in the researcher triage queue."
                if researcher_attention
                else "No concern-based triage action is suggested by this prototype."
            ),
        },
        "explanation": explanation,
        "score_policy": {
            "observation_consistency_score": None,
            "reason": (
                "Phase 2 intentionally exposes component evidence before introducing a numeric consistency score. "
                "Numeric weights will be added only after the component signals and calibration policy are fixed."
            ),
        },
    }
