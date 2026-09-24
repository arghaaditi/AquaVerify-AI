"""Evidence-based explanation assembly for AquaVerify.

No LLM is required here. The explanation is generated from structured evidence
returned by rules, conditional rarity, novelty models, and concern indicators.
A future LLM may paraphrase this evidence but should not invent new evidence.
"""


def build_explanation(rule_flags, rarity, novelty, concerns) -> dict:
    sections = []
    quality_signal = bool(rule_flags or rarity["rare_fields"] or novelty["signal_strength"] != "none")
    concern_signal = bool(concerns["direct_pressure_indicators"] or concerns["contextual_indicators"])

    if rule_flags:
        sections.append({
            "title": "Consistency checks",
            "items": [flag["message"] for flag in rule_flags],
        })

    if rarity["rare_fields"]:
        sections.append({
            "title": "Reference comparison",
            "items": [item["message"] for item in rarity["rare_fields"][:5]],
        })

    if novelty["signal_strength"] != "none":
        sections.append({
            "title": "ML novelty check",
            "items": [novelty["message"]],
        })

    concern_items = [x["label"] for x in concerns["direct_pressure_indicators"]]
    concern_items += [x["label"] for x in concerns["contextual_indicators"]]
    if concern_items:
        sections.append({
            "title": "Reported concern indicators",
            "items": concern_items,
        })

    if quality_signal:
        headline = "Please review parts of this observation"
        summary = (
            "AquaVerify found one or more data-quality or novelty signals. These signals do not prove the observation is wrong. "
            "Please review the highlighted fields and either correct them or keep your answers if they accurately reflect what you observed."
        )
    elif concern_signal:
        headline = "Observation is internally consistent; concern indicators were reported"
        summary = (
            "AquaVerify did not find a citizen-data consistency signal, but the observation contains environmental pressure/context indicators "
            "that may be useful for researcher triage. The citizen does not need to change a consistent observation merely because the stream appears concerning."
        )
    else:
        headline = "No prototype review signal triggered"
        summary = (
            "The prototype did not detect a validation, consistency, rarity, novelty, or defined concern-triage signal for this observation. "
            "This is not a certification of ecological health or scientific accuracy."
        )

    return {
        "headline": headline,
        "summary": summary,
        "sections": sections,
        "human_control_message": (
            "AquaVerify never changes citizen answers automatically. The citizen or reviewer makes the final decision."
        ),
    }
