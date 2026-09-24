"""SQLite persistence layer for AquaVerify Phase 4.

The database stores the submitted observation, the reviewed/final observation,
AI-assisted evidence before and after human review, and researcher-triage state.
It deliberately stores review evidence rather than a scientific water-quality score.
"""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "database" / "aquaverify.db"


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn




@contextmanager
def _db_connection(db_path: Path | str = DEFAULT_DB_PATH):
    """Open a SQLite connection and always close it.

    sqlite3.Connection's own context-manager commits/rolls back transactions but
    does not close the connection. Explicit closure is important on Windows,
    where an open handle can keep temporary .db files locked.
    """
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create the database and schema if they do not yet exist."""
    with _db_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_uuid TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                site_name TEXT,
                observer_note TEXT,

                original_overall_quality TEXT,
                final_overall_quality TEXT,
                user_decision TEXT NOT NULL,
                had_revision INTEGER NOT NULL DEFAULT 0,

                original_rule_flags INTEGER,
                final_rule_flags INTEGER,
                original_rare_fields INTEGER,
                final_rare_fields INTEGER,
                original_ml_signal TEXT,
                final_ml_signal TEXT,

                concern_indicator_count INTEGER NOT NULL DEFAULT 0,
                direct_pressure_count INTEGER NOT NULL DEFAULT 0,
                contextual_indicator_count INTEGER NOT NULL DEFAULT 0,
                researcher_attention_suggested INTEGER NOT NULL DEFAULT 0,
                citizen_review_initial INTEGER NOT NULL DEFAULT 0,
                citizen_review_final INTEGER NOT NULL DEFAULT 0,

                researcher_review_status TEXT NOT NULL DEFAULT 'not_required',
                researcher_note TEXT NOT NULL DEFAULT '',
                researcher_reviewed_at TEXT,

                original_observation_json TEXT NOT NULL,
                final_observation_json TEXT NOT NULL,
                original_analysis_json TEXT NOT NULL,
                final_analysis_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_observations_created_at
                ON observations(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_observations_triage
                ON observations(researcher_attention_suggested, researcher_review_status);
            """
        )


def _metric(analysis: dict | None, path: tuple[str, ...], default: Any = None) -> Any:
    cur: Any = analysis or {}
    try:
        for key in path:
            cur = cur[key]
        return cur
    except (KeyError, TypeError):
        return default


def save_completed_review(
    *,
    submission_uuid: str,
    original_observation: dict,
    final_observation: dict,
    original_analysis: dict,
    final_analysis: dict,
    user_decision: str,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    """Persist one completed human-review workflow exactly once.

    submission_uuid is unique. Re-rendering the Streamlit final page therefore
    cannot create duplicate database rows.
    """
    init_db(db_path)

    site_name = str(final_observation.get("site_name") or original_observation.get("site_name") or "").strip()
    observer_note = str(final_observation.get("observer_note") or original_observation.get("observer_note") or "").strip()
    original_quality = original_observation.get("overall_ecosystem_quality")
    final_quality = final_observation.get("overall_ecosystem_quality")
    had_revision = int(original_observation != final_observation)

    original_rule_flags = _metric(original_analysis, ("consistency", "rule_flag_count"), 0)
    final_rule_flags = _metric(final_analysis, ("consistency", "rule_flag_count"), 0)
    original_rare = _metric(original_analysis, ("consistency", "conditional_rarity", "rare_field_count"), 0)
    final_rare = _metric(final_analysis, ("consistency", "conditional_rarity", "rare_field_count"), 0)
    original_ml = _metric(original_analysis, ("ml_novelty", "signal_strength"), "not_available")
    final_ml = _metric(final_analysis, ("ml_novelty", "signal_strength"), "not_available")

    direct_count = int(_metric(final_analysis, ("concern_indicators", "direct_pressure_count"), 0) or 0)
    contextual_count = int(_metric(final_analysis, ("concern_indicators", "contextual_count"), 0) or 0)
    concern_count = direct_count + contextual_count
    researcher_attention = int(bool(_metric(final_analysis, ("review", "researcher_attention_suggested"), False)))
    citizen_review_initial = int(bool(_metric(original_analysis, ("review", "citizen_review_needed"), False)))
    citizen_review_final = int(bool(_metric(final_analysis, ("review", "citizen_review_needed"), False)))
    researcher_status = "pending" if researcher_attention else "not_required"

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = (
        submission_uuid,
        now,
        site_name,
        observer_note,
        original_quality,
        final_quality,
        user_decision,
        had_revision,
        original_rule_flags,
        final_rule_flags,
        original_rare,
        final_rare,
        original_ml,
        final_ml,
        concern_count,
        direct_count,
        contextual_count,
        researcher_attention,
        citizen_review_initial,
        citizen_review_final,
        researcher_status,
        json.dumps(original_observation, ensure_ascii=False, sort_keys=True),
        json.dumps(final_observation, ensure_ascii=False, sort_keys=True),
        json.dumps(original_analysis, ensure_ascii=False, sort_keys=True),
        json.dumps(final_analysis, ensure_ascii=False, sort_keys=True),
    )

    with _db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO observations (
                submission_uuid, created_at, site_name, observer_note,
                original_overall_quality, final_overall_quality, user_decision, had_revision,
                original_rule_flags, final_rule_flags, original_rare_fields, final_rare_fields,
                original_ml_signal, final_ml_signal,
                concern_indicator_count, direct_pressure_count, contextual_indicator_count,
                researcher_attention_suggested, citizen_review_initial, citizen_review_final,
                researcher_review_status,
                original_observation_json, final_observation_json,
                original_analysis_json, final_analysis_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        row = conn.execute(
            "SELECT id FROM observations WHERE submission_uuid = ?",
            (submission_uuid,),
        ).fetchone()
        return int(row["id"])


def fetch_observations(db_path: Path | str = DEFAULT_DB_PATH) -> list[dict]:
    init_db(db_path)
    with _db_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM observations
            ORDER BY datetime(created_at) DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_observation(observation_id: int, db_path: Path | str = DEFAULT_DB_PATH) -> dict | None:
    init_db(db_path)
    with _db_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM observations WHERE id = ?", (int(observation_id),)).fetchone()
    return dict(row) if row else None


def update_researcher_review(
    observation_id: int,
    status: str,
    note: str = "",
    db_path: Path | str = DEFAULT_DB_PATH,
) -> None:
    allowed = {"pending", "reviewed", "follow_up_recommended", "no_further_action", "not_required"}
    if status not in allowed:
        raise ValueError(f"Unsupported researcher review status: {status}")
    reviewed_at = None if status == "pending" else datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _db_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE observations
            SET researcher_review_status = ?, researcher_note = ?, researcher_reviewed_at = ?
            WHERE id = ?
            """,
            (status, note.strip(), reviewed_at, int(observation_id)),
        )


def delete_all_observations(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Development/demo helper. Not exposed as the main workflow action."""
    init_db(db_path)
    with _db_connection(db_path) as conn:
        conn.execute("DELETE FROM observations")
        # Reset row IDs as well so a clean hackathon demo starts at #1.
        try:
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'observations'")
        except sqlite3.OperationalError:
            pass
