"""Canonical demo scenarios used by the Streamlit UI and automated tests.

Keeping these outside app.py lets tests verify the same scenarios shown during
the hackathon demo without importing Streamlit.
"""
from copy import deepcopy

PRESETS = {
    "Healthy / consistent": {
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
    },
    "Concerning but consistent": {
        "channel_form": "flat",
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
    },
    "Contradictory assessment": {
        "channel_form": "flat",
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
        "overall_ecosystem_quality": "good",
    },
}


def get_preset(name: str) -> dict:
    return deepcopy(PRESETS[name])
