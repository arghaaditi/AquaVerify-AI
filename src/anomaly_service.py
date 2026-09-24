"""Dual-model novelty detection service for AquaVerify.

The two models were trained only on reference observations and calibrated using
normal validation observations. Larger transformed score = more unusual.
"""
from functools import lru_cache
import json
import joblib
import pandas as pd

from config import FEATURES, MODELS_DIR

CORE_MODELS = ["IsolationForest", "OneClassSVM"]


@lru_cache(maxsize=1)
def _assets():
    thresholds = json.loads((MODELS_DIR / "model_thresholds.json").read_text(encoding="utf-8"))
    models = {
        name: joblib.load(MODELS_DIR / f"{name}.joblib")
        for name in CORE_MODELS
    }
    return models, thresholds


def _score(name, pipeline, X):
    # Match the convention used during Phase 1 benchmark:
    # larger returned number = more unusual.
    if name == "IsolationForest":
        return float(-pipeline.score_samples(X)[0])
    return float(-pipeline.decision_function(X)[0])


def analyze_novelty(obs: dict) -> dict:
    models, thresholds = _assets()
    X = pd.DataFrame([{feature: obs[feature] for feature in FEATURES}])

    model_results = {}
    flags = 0
    for name in CORE_MODELS:
        score = _score(name, models[name], X)
        threshold = float(thresholds[name])
        flagged = score >= threshold
        if flagged:
            flags += 1
        model_results[name] = {
            "score": score,
            "threshold": threshold,
            "flagged": bool(flagged),
            "score_minus_threshold": score - threshold,
        }

    if flags == 2:
        strength = "strong"
        message = "Both novelty models found the 14-field observation pattern unusual relative to the reference data."
    elif flags == 1:
        strength = "moderate"
        message = "One of the two novelty models found the 14-field observation pattern unusual relative to the reference data."
    else:
        strength = "none"
        message = "Neither core novelty model crossed its operational review threshold for this observation."

    return {
        "signal_strength": strength,
        "models_flagged": flags,
        "models_total": len(CORE_MODELS),
        "model_results": model_results,
        "message": message,
        "interpretation": (
            "Novelty means unusual relative to the synthetic reference distribution; "
            "it does not mean the observation is false or environmentally unsafe."
        ),
    }
