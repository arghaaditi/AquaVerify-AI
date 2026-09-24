"""Basic schema validation for a single AquaVerify citizen observation.

This layer asks only whether the submitted values are complete and belong to the
expected categorical vocabulary. It does not infer ecology and does not run ML.
"""
from functools import lru_cache
import pandas as pd

from config import DATA_DIR, FEATURES, QUALITY_FIELD, REQUIRED_FIELDS


def _slug(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    value = value.strip().lower()
    for token in ["-", "/", " "]:
        value = value.replace(token, "_")
    while "__" in value:
        value = value.replace("__", "_")
    return value


@lru_cache(maxsize=1)
def allowed_categories() -> dict[str, set[str]]:
    """Build the accepted vocabulary from the reference dataset.

    For the MVP this keeps the validator synchronized with the dataset used to
    train the novelty models. In a production app this would normally become an
    explicit versioned schema independent of the training sample.
    """
    df = pd.read_csv(DATA_DIR / "reference_train.csv")
    schema = {}
    for field in FEATURES + [QUALITY_FIELD]:
        schema[field] = {_slug(v) for v in df[field].dropna().astype(str).unique()}
    return schema


def normalize_observation(observation: dict) -> dict:
    normalized = {}
    for key, value in observation.items():
        if key in REQUIRED_FIELDS:
            normalized[key] = _slug(value)
        else:
            normalized[key] = value
    return normalized


def validate_observation(observation: dict) -> dict:
    if not isinstance(observation, dict):
        return {
            "is_valid": False,
            "errors": ["Observation must be supplied as a dictionary/object."],
            "warnings": [],
            "missing_fields": REQUIRED_FIELDS.copy(),
            "unknown_values": [],
        }

    obs = normalize_observation(observation)
    schema = allowed_categories()
    errors = []
    warnings = []
    missing = []
    unknown = []

    for field in REQUIRED_FIELDS:
        if field not in obs or obs[field] in (None, ""):
            missing.append(field)

    if missing:
        errors.append(
            "Required fields are missing: " + ", ".join(missing)
        )

    for field in REQUIRED_FIELDS:
        if field in obs and obs[field] not in (None, ""):
            if obs[field] not in schema[field]:
                unknown.append({
                    "field": field,
                    "value": obs[field],
                    "allowed_values": sorted(schema[field]),
                })

    if unknown:
        errors.append(
            "One or more fields contain values outside the prototype schema."
        )

    # Extra fields are allowed because site/date/user metadata may be added later.
    extras = sorted(set(obs) - set(REQUIRED_FIELDS))
    if extras:
        warnings.append(
            "Extra metadata fields were retained but are not used by the Phase 2 analysis engine: "
            + ", ".join(extras)
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "missing_fields": missing,
        "unknown_values": unknown,
    }
