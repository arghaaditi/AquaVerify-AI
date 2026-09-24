"""Reference-conditional rarity analysis.

This layer asks: given the citizen's own overall assessment, how common are the
individual detailed field values among reference observations with that same
assessment? It is an explainability/review signal, not a probability the citizen
is wrong.
"""
from functools import lru_cache
import math
import pandas as pd

from config import DATA_DIR, FEATURES, QUALITY_FIELD, RARITY_THRESHOLD


@lru_cache(maxsize=1)
def _lookup():
    table = pd.read_csv(DATA_DIR / "conditional_rarity_table.csv")
    return {
        (str(r.overall_quality), str(r.feature), str(r.value)): float(r.smoothed_probability)
        for r in table.itertuples(index=False)
    }


def analyze_conditional_rarity(obs: dict) -> dict:
    quality = obs[QUALITY_FIELD]
    lookup = _lookup()
    rare_fields = []
    surprisal = 0.0

    for feature in FEATURES:
        value = str(obs[feature])
        p = float(lookup.get((quality, feature, value), 1e-9))
        surprisal += -math.log(max(p, 1e-9))
        if p < RARITY_THRESHOLD:
            rare_fields.append({
                "feature": feature,
                "value": value,
                "smoothed_probability": p,
                "approx_percent_within_quality_group": round(p * 100, 2),
                "message": (
                    f"'{feature}={value}' is uncommon among reference observations "
                    f"rated '{quality}' (smoothed frequency ≈ {p*100:.1f}%)."
                ),
            })

    return {
        "quality_group": quality,
        "rarity_threshold": RARITY_THRESHOLD,
        "rare_field_count": len(rare_fields),
        "rare_fields": rare_fields,
        "conditional_surprisal": float(surprisal),
        "interpretation": (
            "Reference-conditional rarity is a review/explanation signal. It is not "
            "a scientific probability that the citizen is wrong."
        ),
    }
