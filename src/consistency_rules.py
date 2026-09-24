"""Transparent assessment-consistency review rules for AquaVerify.

These rules do NOT diagnose stream health and do NOT overwrite citizen answers.
They only identify combinations that deserve review, especially when a user's
summary assessment seems difficult to reconcile with their own detailed observations.
"""


def evaluate_rules(obs: dict) -> list[dict]:
    flags = []

    def add(rule_id, severity, message, fields):
        flags.append({
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "evidence_fields": fields,
        })

    quality = obs.get("overall_ecosystem_quality")

    if obs.get("sewage_discharge") == "yes" and quality == "good":
        add(
            "R01_SEWAGE_GOOD",
            "strong_review",
            "Sewage discharge was reported while the overall ecosystem was rated 'good'. Please review the overall assessment.",
            ["sewage_discharge", "overall_ecosystem_quality"],
        )

    if obs.get("draining_pipes") == "yes" and quality == "good":
        add(
            "R02_DRAINING_PIPE_GOOD",
            "strong_review",
            "A draining pipe was reported while the overall ecosystem was rated 'good'. Please review whether the summary rating matches the detailed observation.",
            ["draining_pipes", "overall_ecosystem_quality"],
        )

    if obs.get("water_aspect") in {"has_foam", "altered_color"} and quality == "good":
        add(
            "R03_VISUAL_WATER_GOOD",
            "review",
            "Foam or altered water colour was reported together with a 'good' overall rating. This can be valid, but the combination deserves another look.",
            ["water_aspect", "overall_ecosystem_quality"],
        )

    if obs.get("habitats_present") == "no" and obs.get("riparian_vegetation") == "none" and quality == "good":
        add(
            "R04_HABITAT_RIPARIAN_GOOD",
            "review",
            "No visible habitats and no riparian vegetation were reported, while the overall rating was 'good'. Please review the summary assessment.",
            ["habitats_present", "riparian_vegetation", "overall_ecosystem_quality"],
        )

    if obs.get("bottom_type") == "artificial" and obs.get("bank_type") == "artificial" and quality == "good":
        add(
            "R05_ARTIFICIAL_CHANNEL_GOOD",
            "review",
            "Both the channel bottom and banks were reported as artificial while the overall rating was 'good'. This is not automatically wrong, but it is worth reviewing.",
            ["bottom_type", "bank_type", "overall_ecosystem_quality"],
        )

    pressure_fields = [
        obs.get("barriers_present") == "yes",
        obs.get("draining_pipes") == "yes",
        obs.get("sewage_discharge") == "yes",
        obs.get("construction_in_stream") == "yes",
        obs.get("impervious_area") == "both_sides",
        obs.get("vegetation_cuts") == "yes",
    ]
    pressure_count = sum(pressure_fields)
    if pressure_count >= 3 and quality == "good":
        add(
            "R06_MULTIPLE_PRESSURES_GOOD",
            "strong_review",
            f"{pressure_count} pressure indicators were reported together with a 'good' overall rating. Please review the summary assessment.",
            ["barriers_present", "draining_pipes", "sewage_discharge", "construction_in_stream", "impervious_area", "vegetation_cuts", "overall_ecosystem_quality"],
        )

    positive_natural = sum([
        obs.get("bottom_type") == "natural",
        obs.get("bank_type") == "natural",
        obs.get("habitats_present") == "yes",
        obs.get("water_aspect") == "clear_transparent",
        obs.get("riparian_vegetation") == "both_sides",
        obs.get("draining_pipes") == "no",
        obs.get("sewage_discharge") == "no",
    ])
    if positive_natural >= 6 and quality == "poor":
        add(
            "R07_NATURAL_PATTERN_POOR",
            "review",
            "Most detailed observations appear relatively natural/low-pressure, but the overall rating is 'poor'. There may be context not captured by the form, so please review rather than automatically changing the answer.",
            ["bottom_type", "bank_type", "habitats_present", "water_aspect", "riparian_vegetation", "draining_pipes", "sewage_discharge", "overall_ecosystem_quality"],
        )

    return flags
