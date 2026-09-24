from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from engine import analyze_observation


CASES = {
    "healthy_consistent": {
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
    "poor_but_consistent": {
        "channel_form": "u_shape",
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
    "contradictory_good": {
        "channel_form": "u_shape",
        "bottom_type": "artificial",
        "bank_type": "artificial",
        "habitats_present": "no",
        "natural_debris_present": "no",
        "water_flow": "stagnant_intermittent",
        "water_aspect": "has_foam",
        "barriers_present": "yes",
        "draining_pipes": "yes",
        "sewage_discharge": "yes",
        "construction_in_stream": "yes",
        "impervious_area": "both_sides",
        "riparian_vegetation": "none",
        "vegetation_cuts": "yes",
        "overall_ecosystem_quality": "good",
    },
    "invalid_missing_field": {
        "channel_form": "v_shape",
        "overall_ecosystem_quality": "good",
    },
}


if __name__ == "__main__":
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    for name, obs in CASES.items():
        result = analyze_observation(obs)
        print("\n" + "=" * 80)
        print(name)
        print("status:", result["analysis_status"])
        print("review:", result["review"])
        print("headline:", result["explanation"]["headline"])
        if result["analysis_status"] == "complete":
            print("rule flags:", result["consistency"]["rule_flag_count"])
            print("rare fields:", result["consistency"]["conditional_rarity"]["rare_field_count"])
            print("ML signal:", result["ml_novelty"]["signal_strength"])
            print("concern triage:", result["concern_indicators"]["triage_label"])
        (out_dir / f"demo_{name}.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
