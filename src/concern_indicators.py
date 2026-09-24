"""Transparent observed-concern indicator extraction.

This is deliberately NOT a pollution classifier and NOT a water-safety score.
It merely surfaces reported observations that may deserve researcher attention.
"""


def analyze_concern_indicators(obs: dict) -> dict:
    direct = []
    contextual = []

    def add(target, indicator_id, label, fields, rationale):
        target.append({
            "indicator_id": indicator_id,
            "label": label,
            "evidence_fields": fields,
            "rationale": rationale,
        })

    if obs.get("sewage_discharge") == "yes":
        add(
            direct,
            "C01_SEWAGE_REPORTED",
            "Sewage discharge reported",
            ["sewage_discharge"],
            "A direct discharge report is useful for review prioritization, but citizen observation alone is not a laboratory diagnosis.",
        )

    if obs.get("draining_pipes") == "yes":
        add(
            direct,
            "C02_DRAINING_PIPE_REPORTED",
            "Draining pipe reported",
            ["draining_pipes"],
            "A reported drainage input is a direct human-pressure observation worth surfacing to reviewers.",
        )

    if obs.get("construction_in_stream") == "yes":
        add(
            direct,
            "C03_CONSTRUCTION_REPORTED",
            "Construction in/near stream reported",
            ["construction_in_stream"],
            "Construction is a reported pressure indicator; the prototype does not infer its legal or ecological impact.",
        )

    if obs.get("water_aspect") in {"altered_color", "has_foam", "muddy_turbid"}:
        add(
            contextual,
            "C04_WATER_APPEARANCE",
            f"Water appearance reported as {obs.get('water_aspect')}",
            ["water_aspect"],
            "Visual appearance can motivate review, but it cannot establish chemical or microbiological water quality.",
        )

    if obs.get("barriers_present") == "yes":
        add(
            contextual,
            "C05_BARRIER_REPORTED",
            "Barrier reported",
            ["barriers_present"],
            "A barrier is a channel-pressure/context indicator and may be relevant to ecological assessment.",
        )

    if obs.get("impervious_area") == "both_sides":
        add(
            contextual,
            "C06_IMPERVIOUS_BOTH_SIDES",
            "Impervious area reported on both sides",
            ["impervious_area"],
            "This is a surrounding-land-pressure observation used only for triage/context.",
        )

    if obs.get("riparian_vegetation") == "none":
        add(
            contextual,
            "C07_NO_RIPARIAN_VEGETATION",
            "No riparian vegetation reported",
            ["riparian_vegetation"],
            "Absence of reported riparian vegetation is surfaced as contextual evidence, not a standalone health diagnosis.",
        )

    if obs.get("habitats_present") == "no":
        add(
            contextual,
            "C08_NO_VISIBLE_HABITATS",
            "No visible habitats reported",
            ["habitats_present"],
            "This is a citizen-observed habitat context signal and may deserve expert interpretation.",
        )

    if obs.get("vegetation_cuts") == "yes":
        add(
            contextual,
            "C09_VEGETATION_CUTS",
            "Vegetation cuts reported",
            ["vegetation_cuts"],
            "Vegetation management/cutting is surfaced as a contextual human-pressure observation.",
        )

    if direct:
        triage = "direct_pressure_reported"
        triage_note = "At least one direct human-pressure indicator was reported; consider prioritizing the observation for researcher review."
    elif len(contextual) >= 3:
        triage = "multiple_context_signals"
        triage_note = "Multiple contextual concern indicators were reported; researcher review may be useful."
    elif contextual:
        triage = "context_signal_present"
        triage_note = "One or more contextual indicators were reported; no ecological diagnosis is made."
    else:
        triage = "no_prototype_concern_indicator"
        triage_note = "No concern indicator defined by this prototype was triggered. This does not prove the stream is healthy or safe."

    return {
        "direct_pressure_indicators": direct,
        "contextual_indicators": contextual,
        "direct_pressure_count": len(direct),
        "contextual_count": len(contextual),
        "triage_label": triage,
        "triage_note": triage_note,
        "interpretation": (
            "Concern indicators support triage only. AquaVerify does not diagnose pollution, "
            "drinking-water safety, pathogens, nutrients, or regulatory compliance."
        ),
    }
