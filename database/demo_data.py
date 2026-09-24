"""Clearly labelled demo-data utilities for the hackathon presentation.

These helpers generate three canonical records through the same analysis engine
used by the live citizen workflow. They are demo records, not scientific data.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from demo_presets import PRESETS  # noqa: E402
from engine import analyze_observation  # noqa: E402
from database.db import (  # noqa: E402
    DEFAULT_DB_PATH,
    delete_all_observations,
    save_completed_review,
    update_researcher_review,
)


def _with_metadata(obs: dict, site_name: str, note: str) -> dict:
    result = deepcopy(obs)
    result["site_name"] = site_name
    result["observer_note"] = note
    return result


def seed_demo_database(db_path=DEFAULT_DB_PATH, *, reset_first: bool = False) -> list[int]:
    """Create three deterministic, clearly labelled demo workflows.

    Re-running is safe because submission UUIDs are unique and inserts are
    idempotent. Set reset_first=True for a clean presentation database.
    """
    if reset_first:
        delete_all_observations(db_path)

    saved_ids: list[int] = []

    # 1) Healthy / consistent: no citizen review and no researcher triage.
    healthy = _with_metadata(
        PRESETS["Healthy / consistent"],
        "Demo Stream — Healthy / consistent",
        "Seeded demonstration record",
    )
    healthy_analysis = analyze_observation(healthy)
    saved_ids.append(save_completed_review(
        submission_uuid="demo-seed-v1-healthy",
        original_observation=healthy,
        final_observation=healthy,
        original_analysis=healthy_analysis,
        final_analysis=healthy_analysis,
        user_decision="accepted_without_correction",
        db_path=db_path,
    ))

    # 2) Concerning but consistent: accepted by citizen, pending researcher triage.
    concern = _with_metadata(
        PRESETS["Concerning but consistent"],
        "Demo Stream — Concerning but consistent",
        "Seeded demonstration record",
    )
    concern_analysis = analyze_observation(concern)
    saved_ids.append(save_completed_review(
        submission_uuid="demo-seed-v1-concerning",
        original_observation=concern,
        final_observation=concern,
        original_analysis=concern_analysis,
        final_analysis=concern_analysis,
        user_decision="accepted_without_correction",
        db_path=db_path,
    ))

    # 3) Contradictory assessment: citizen revises Good -> Poor after review.
    original = _with_metadata(
        PRESETS["Contradictory assessment"],
        "Demo Stream — Revised after AI-assisted review",
        "Seeded demonstration record",
    )
    final = deepcopy(original)
    final["overall_ecosystem_quality"] = "poor"
    original_analysis = analyze_observation(original)
    final_analysis = analyze_observation(final)
    revised_id = save_completed_review(
        submission_uuid="demo-seed-v1-revised",
        original_observation=original,
        final_observation=final,
        original_analysis=original_analysis,
        final_analysis=final_analysis,
        user_decision="revised_and_accepted",
        db_path=db_path,
    )
    saved_ids.append(revised_id)
    update_researcher_review(
        revised_id,
        "follow_up_recommended",
        "Seeded demo: reviewer recommends follow-up field assessment.",
        db_path,
    )

    return saved_ids
