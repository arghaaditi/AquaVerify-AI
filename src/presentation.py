"""Human-readable UI labels for AquaVerify internal values."""

DISPLAY = {
    "v_shape": "V-shaped",
    "u_shape": "U-shaped",
    "flat": "Flat",
    "unsure": "Not sure",
    "natural": "Natural",
    "artificial": "Artificial",
    "laid_stones": "Laid stones",
    "yes": "Yes",
    "no": "No",
    "fast": "Fast",
    "slow": "Slow",
    "stagnant_intermittent": "Stagnant / intermittent",
    "dry": "Dry",
    "clear_transparent": "Clear / transparent",
    "muddy_turbid": "Muddy / turbid",
    "altered_color": "Altered colour",
    "has_foam": "Foam visible",
    "none": "None",
    "one_side": "One side",
    "both_sides": "Both sides",
    "good": "Good",
    "moderate": "Moderate",
    "poor": "Poor",
    "strong": "Strong",
    "moderate_signal": "Moderate",
    "not_available": "Not available",
}

FIELD_LABELS = {
    "channel_form": "Channel form",
    "bottom_type": "Channel bottom",
    "bank_type": "Bank type",
    "habitats_present": "Visible habitats",
    "natural_debris_present": "Natural debris",
    "water_flow": "Water flow",
    "water_aspect": "Water appearance",
    "barriers_present": "Barrier present",
    "draining_pipes": "Draining pipe",
    "sewage_discharge": "Sewage discharge",
    "construction_in_stream": "Construction in/near stream",
    "impervious_area": "Impervious area",
    "riparian_vegetation": "Riparian vegetation",
    "vegetation_cuts": "Vegetation cuts",
    "overall_ecosystem_quality": "Overall ecosystem quality",
    "site_name": "Site name",
    "observer_note": "Observer note",
}

DECISION_LABELS = {
    "accepted_without_correction": "Accepted without correction",
    "revised_and_accepted": "Revised and accepted",
    "kept_original_or_current_answers": "Kept submitted answers after review",
    "completed": "Completed",
}

RESEARCH_STATUS_LABELS = {
    "pending": "Pending review",
    "reviewed": "Reviewed",
    "follow_up_recommended": "Follow-up recommended",
    "no_further_action": "No further action",
    "not_required": "Not required",
}

ML_SIGNAL_LABELS = {
    "none": "None",
    "moderate": "Moderate",
    "strong": "Strong",
    "not_available": "Not available",
}


def pretty(value) -> str:
    if value is None:
        return "—"
    text = str(value)
    return DISPLAY.get(text, text.replace("_", " ").title())


def decision_label(value) -> str:
    return DECISION_LABELS.get(str(value), pretty(value))


def researcher_status_label(value) -> str:
    return RESEARCH_STATUS_LABELS.get(str(value), pretty(value))


def ml_signal_label(value) -> str:
    return ML_SIGNAL_LABELS.get(str(value), pretty(value))


def field_label(value) -> str:
    return FIELD_LABELS.get(str(value), pretty(value))
