from __future__ import annotations

import json
import sys
import uuid
from copy import deepcopy
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from demo_presets import PRESETS  # noqa: E402
from engine import analyze_observation  # noqa: E402
from presentation import (  # noqa: E402
    decision_label,
    field_label,
    ml_signal_label,
    pretty,
    researcher_status_label,
)
from database.db import (  # noqa: E402
    DEFAULT_DB_PATH,
    delete_all_observations,
    fetch_observation,
    fetch_observations,
    init_db,
    save_completed_review,
    update_researcher_review,
)
from database.demo_data import seed_demo_database  # noqa: E402


st.set_page_config(
    page_title="AquaVerify AI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

FIELD_GROUPS = [
    (
        "Channel & habitat",
        [
            ("channel_form", "Channel form", ["v_shape", "u_shape", "flat", "unsure"]),
            ("bottom_type", "Channel bottom", ["natural", "artificial", "unsure"]),
            ("bank_type", "Bank type", ["natural", "laid_stones", "artificial", "unsure"]),
            ("habitats_present", "Visible habitats present?", ["yes", "no"]),
            ("natural_debris_present", "Natural debris present?", ["yes", "no"]),
        ],
    ),
    (
        "Water observation",
        [
            ("water_flow", "Water flow", ["fast", "slow", "stagnant_intermittent", "dry", "unsure"]),
            ("water_aspect", "Water appearance", ["clear_transparent", "muddy_turbid", "altered_color", "has_foam", "unsure"]),
            ("barriers_present", "Barrier present?", ["no", "yes", "unsure"]),
        ],
    ),
    (
        "Human pressure",
        [
            ("draining_pipes", "Draining pipe observed?", ["no", "yes", "unsure"]),
            ("sewage_discharge", "Sewage discharge observed?", ["no", "yes", "unsure"]),
            ("construction_in_stream", "Construction in/near stream?", ["no", "yes", "unsure"]),
            ("impervious_area", "Impervious area", ["none", "one_side", "both_sides", "unsure"]),
            ("riparian_vegetation", "Riparian vegetation", ["both_sides", "one_side", "none", "unsure"]),
            ("vegetation_cuts", "Vegetation cuts observed?", ["no", "yes", "unsure"]),
        ],
    ),
]
QUALITY = ("overall_ecosystem_quality", "Overall ecosystem quality", ["good", "moderate", "poor"])


def apply_css():
    st.markdown(
        """
        <style>
          .block-container {max-width: 1240px; padding-top: 2rem; padding-bottom: 3rem;}
          [data-testid="stMetric"] {
              background: #ffffff;
              border: 1px solid #dce7e5;
              border-radius: 12px;
              padding: 14px 16px;
              min-height: 112px;
          }
          [data-testid="stMetricLabel"] {font-weight: 650;}
          .aq-card {
              border: 1px solid #dce7e5;
              border-radius: 12px;
              padding: 1rem 1.1rem;
              background: #fbfdfd;
          }
          .aq-kicker {color:#5d6b70; font-size:0.92rem; margin-bottom:0.15rem;}
          .aq-strong {font-weight:700; font-size:1.05rem;}
          div[data-testid="stDataFrame"] {border: 1px solid #e5eceb; border-radius: 10px; overflow: hidden;}
          .stButton > button, .stDownloadButton > button {border-radius: 9px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    defaults = {
        "page": "Submit Observation",
        "form_values": deepcopy(PRESETS["Healthy / consistent"]),
        "current_observation": None,
        "current_analysis": None,
        "original_observation": None,
        "original_analysis": None,
        "final_observation": None,
        "final_analysis": None,
        "user_decision": None,
        "revision_mode": False,
        "site_name": "Demo Stream",
        "observer_note": "",
        "submission_uuid": str(uuid.uuid4()),
        "saved_observation_id": None,
        "save_error": None,
        "site_name_input": "Demo Stream",
        "observer_note_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_page(page: str):
    st.session_state.page = page
    st.rerun()


def clear_analysis():
    st.session_state.current_observation = None
    st.session_state.current_analysis = None
    st.session_state.original_observation = None
    st.session_state.original_analysis = None
    st.session_state.final_observation = None
    st.session_state.final_analysis = None
    st.session_state.user_decision = None
    st.session_state.revision_mode = False
    st.session_state.submission_uuid = str(uuid.uuid4())
    st.session_state.saved_observation_id = None
    st.session_state.save_error = None


def sync_form_values_to_widgets(values: dict):
    for field, value in values.items():
        st.session_state[f"input_{field}"] = value


def sync_metadata_widgets(site_name: str, observer_note: str = ""):
    st.session_state.site_name = site_name
    st.session_state.observer_note = observer_note
    st.session_state.site_name_input = site_name
    st.session_state.observer_note_input = observer_note


def load_preset(name: str):
    clear_analysis()
    preset_values = deepcopy(PRESETS[name])
    st.session_state.form_values = preset_values
    sync_form_values_to_widgets(preset_values)
    sync_metadata_widgets(f"Demo Stream — {name}", "")
    st.session_state.page = "Submit Observation"


def start_new_observation():
    clear_analysis()
    defaults = deepcopy(PRESETS["Healthy / consistent"])
    st.session_state.form_values = defaults
    sync_form_values_to_widgets(defaults)
    sync_metadata_widgets("", "")
    st.session_state.page = "Submit Observation"


def render_header():
    st.title("AquaVerify AI")
    st.caption("Human-in-the-loop quality control for citizen stream assessments")
    st.info(
        "AquaVerify screens observation consistency, unusual patterns, and review priority. "
        "It does not diagnose pollution, drinking-water safety, or laboratory water quality."
    )


def render_sidebar():
    with st.sidebar:
        st.subheader("AquaVerify")
        pages = ["Submit Observation", "AI-Assisted Review", "Final Assessment", "Research Dashboard"]
        selected = st.radio("Workflow", pages, index=pages.index(st.session_state.page))
        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()

        st.divider()
        st.caption("Demo presets")
        preset = st.selectbox("Choose a test case", list(PRESETS), key="preset_selector")
        if st.button("Load demo preset", use_container_width=True):
            load_preset(preset)
            st.rerun()

        if st.button("Start new observation", use_container_width=True):
            start_new_observation()
            st.rerun()

        if st.session_state.page == "Research Dashboard":
            st.divider()
            with st.expander("Demo database tools"):
                st.caption("These controls affect only the local demo database.")
                confirm_seed = st.checkbox("I understand this will replace local demo records", key="confirm_seed")
                if st.button("Reset & seed 3 canonical demo records", use_container_width=True, disabled=not confirm_seed):
                    seed_demo_database(DEFAULT_DB_PATH, reset_first=True)
                    st.success("Clean demo database created.")
                    st.rerun()
                confirm_clear = st.checkbox("Confirm database clear", key="confirm_clear")
                if st.button("Clear local database", use_container_width=True, disabled=not confirm_clear):
                    delete_all_observations(DEFAULT_DB_PATH)
                    st.success("Local database cleared.")
                    st.rerun()



def select_field(field: str, label: str, options: list[str]):
    widget_key = f"input_{field}"
    current = st.session_state.form_values.get(field, options[0])
    if current not in options:
        current = options[0]
    if widget_key not in st.session_state:
        st.session_state[widget_key] = current
    value = st.selectbox(label, options, format_func=pretty, key=widget_key)
    st.session_state.form_values[field] = value
    return value


def submit_observation(observation: dict):
    analysis = analyze_observation(observation)
    if st.session_state.original_analysis is None:
        st.session_state.original_observation = deepcopy(observation)
        st.session_state.original_analysis = deepcopy(analysis)
    st.session_state.current_observation = deepcopy(observation)
    st.session_state.current_analysis = analysis
    st.session_state.form_values = deepcopy({k: v for k, v in observation.items() if k in st.session_state.form_values})
    st.session_state.page = "AI-Assisted Review"
    st.rerun()


def render_submit_page():
    st.header("1. Submit Observation")
    st.write(
        "Record the detailed field observations first, then provide your overall ecosystem assessment. "
        "AquaVerify will review the submission but will never change your answers automatically."
    )
    if st.session_state.revision_mode:
        st.warning("Review mode: edit any field you believe needs correction, then submit again to re-run all checks.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.text_input("Site name", key="site_name_input", placeholder="e.g., North bridge sampling point")
    with col_b:
        st.text_input("Optional observer note", key="observer_note_input", placeholder="Anything the structured form does not capture")

    values = {}
    for group_name, fields in FIELD_GROUPS:
        st.subheader(group_name)
        cols = st.columns(2)
        for idx, (field, label, options) in enumerate(fields):
            with cols[idx % 2]:
                values[field] = select_field(field, label, options)

    st.subheader("Your overall assessment")
    field, label, options = QUALITY
    values[field] = select_field(field, label, options)
    if st.button("Review Observation", type="primary", use_container_width=True):
        st.session_state.site_name = st.session_state.site_name_input.strip()
        st.session_state.observer_note = st.session_state.observer_note_input.strip()
        observation = dict(values)
        observation["site_name"] = st.session_state.site_name
        observation["observer_note"] = st.session_state.observer_note
        submit_observation(observation)


def metric_value(analysis, kind):
    if not analysis or analysis.get("analysis_status") != "complete":
        return "—"
    if kind == "rules":
        return str(analysis["consistency"]["rule_flag_count"])
    if kind == "rare":
        return str(analysis["consistency"]["conditional_rarity"]["rare_field_count"])
    if kind == "ml":
        return ml_signal_label(analysis["ml_novelty"]["signal_strength"])
    if kind == "concern":
        c = analysis["concern_indicators"]
        return str(c["direct_pressure_count"] + c["contextual_count"])
    return "—"


def render_evidence(analysis):
    if analysis["analysis_status"] != "complete":
        st.error(analysis["explanation"]["headline"])
        for err in analysis["basic_validation"]["errors"]:
            st.write("•", err)
        return

    exp = analysis["explanation"]
    st.subheader(exp["headline"])
    st.write(exp["summary"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Consistency rule flags", metric_value(analysis, "rules"), help="Transparent rule-based review signals.")
    c2.metric("Rare reference fields", metric_value(analysis, "rare"), help="Fields uncommon within the same overall-assessment reference group.")
    c3.metric("ML novelty", metric_value(analysis, "ml"), help="Agreement strength from the novelty-detection models.")
    c4.metric("Concern indicators", metric_value(analysis, "concern"), help="Reported pressure/context indicators used only for researcher triage.")

    for section in exp["sections"]:
        with st.expander(section["title"], expanded=True):
            for item in section["items"]:
                st.write("•", item)
    st.caption(exp["human_control_message"])


def render_review_page():
    st.header("2. AI-Assisted Review")
    analysis = st.session_state.current_analysis
    if analysis is None:
        st.warning("No observation has been submitted yet.")
        if st.button("Go to observation form"):
            set_page("Submit Observation")
        return

    render_evidence(analysis)
    if analysis["analysis_status"] != "complete":
        if st.button("Edit Observation", type="primary", use_container_width=True):
            st.session_state.revision_mode = True
            set_page("Submit Observation")
        return

    st.divider()
    review = analysis["review"]
    left, right = st.columns(2)
    citizen_state = "Review requested" if review["citizen_review_needed"] else "No correction requested"
    triage_state = "Attention suggested" if review["researcher_attention_suggested"] else "No triage signal"
    with left:
        st.markdown(
            f'<div class="aq-card"><div class="aq-kicker">Citizen data-quality review</div>'
            f'<div class="aq-strong">{citizen_state}</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<div class="aq-card"><div class="aq-kicker">Researcher triage</div>'
            f'<div class="aq-strong">{triage_state}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    if review["citizen_review_needed"]:
        st.warning(
            "AquaVerify found consistency and/or novelty evidence worth reviewing. "
            "These are review signals, not proof that the observation is wrong."
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit Observation", type="primary", use_container_width=True):
                st.session_state.revision_mode = True
                set_page("Submit Observation")
        with c2:
            if st.button("Keep My Answers", use_container_width=True):
                st.session_state.final_observation = deepcopy(st.session_state.current_observation)
                st.session_state.final_analysis = deepcopy(analysis)
                st.session_state.user_decision = "kept_original_or_current_answers"
                set_page("Final Assessment")
    else:
        st.success("AquaVerify is not asking the citizen to correct this submission.")
        if review["researcher_attention_suggested"]:
            st.info(
                "The observation is internally acceptable for citizen submission, while reported concern indicators "
                "still justify researcher triage. Bad environmental conditions do not imply bad citizen data."
            )
        if st.button("Accept & Continue", type="primary", use_container_width=True):
            st.session_state.final_observation = deepcopy(st.session_state.current_observation)
            st.session_state.final_analysis = deepcopy(analysis)
            st.session_state.user_decision = "revised_and_accepted" if st.session_state.revision_mode else "accepted_without_correction"
            set_page("Final Assessment")


def review_label(analysis):
    if not analysis or analysis.get("analysis_status") != "complete":
        return "Not available"
    return "Citizen review requested" if analysis["review"]["citizen_review_needed"] else "No citizen correction requested"


def persist_completed_workflow():
    if st.session_state.final_analysis is None:
        return None
    if st.session_state.saved_observation_id is not None:
        return st.session_state.saved_observation_id
    original_observation = st.session_state.original_observation or st.session_state.final_observation or {}
    original_analysis = st.session_state.original_analysis or st.session_state.final_analysis or {}
    final_observation = st.session_state.final_observation or st.session_state.current_observation or {}
    final_analysis = st.session_state.final_analysis or st.session_state.current_analysis or {}
    try:
        saved_id = save_completed_review(
            submission_uuid=st.session_state.submission_uuid,
            original_observation=original_observation,
            final_observation=final_observation,
            original_analysis=original_analysis,
            final_analysis=final_analysis,
            user_decision=st.session_state.user_decision or "completed",
        )
        st.session_state.saved_observation_id = saved_id
        st.session_state.save_error = None
        return saved_id
    except Exception as exc:
        st.session_state.save_error = str(exc)
        return None


def _dashboard_dataframe(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    for col in ["had_revision", "researcher_attention_suggested", "citizen_review_initial", "citizen_review_final"]:
        if col in df:
            df[col] = df[col].astype(bool)
    return df


def _display_timestamp(value) -> str:
    try:
        ts = pd.to_datetime(value, utc=True)
        return ts.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(value)


def _display_history(df: pd.DataFrame) -> pd.DataFrame:
    view = pd.DataFrame({
        "ID": df["id"].astype(int),
        "Submitted": df["created_at"].map(_display_timestamp),
        "Site": df["site_name"].fillna("Unnamed site"),
        "Original assessment": df["original_overall_quality"].map(pretty),
        "Final assessment": df["final_overall_quality"].map(pretty),
        "Citizen decision": df["user_decision"].map(decision_label),
        "Revised": df["had_revision"].map(lambda x: "Yes" if x else "No"),
        "Concern indicators": df["concern_indicator_count"].astype(int),
        "Researcher triage": df["researcher_attention_suggested"].map(lambda x: "Suggested" if x else "Not suggested"),
        "Researcher status": df["researcher_review_status"].map(researcher_status_label),
    })
    return view


def render_dashboard():
    st.header("4. Research Dashboard")
    st.write(
        "A persistent SQLite audit trail of completed citizen-review workflows. The dashboard helps researchers prioritize "
        "observations; triage signals are not laboratory diagnoses."
    )
    init_db()
    df = _dashboard_dataframe(fetch_observations())

    if df.empty:
        st.info("No completed observations are stored yet. Complete a Final Assessment, or use the clearly labelled demo-data tool in the sidebar.")
        return

    total = len(df)
    revised = int(df["had_revision"].sum())
    triage = int(df["researcher_attention_suggested"].sum())
    pending = int(((df["researcher_attention_suggested"]) & (df["researcher_review_status"] == "pending")).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stored observations", total)
    c2.metric("Revised after review", revised)
    c3.metric("Researcher triage suggested", triage)
    c4.metric("Pending researcher review", pending)

    st.subheader("Overview")
    left, right = st.columns(2)
    with left:
        st.caption("Final citizen ecosystem assessments")
        assessment_labels = df["final_overall_quality"].fillna("unknown").map(pretty)
        counts = assessment_labels.value_counts().rename_axis("Assessment").to_frame("Observations")
        st.bar_chart(counts)
    with right:
        st.caption("Human review decisions")
        decision_labels = df["user_decision"].fillna("unknown").map(decision_label)
        decisions = decision_labels.value_counts().rename_axis("Decision").to_frame("Observations")
        st.bar_chart(decisions)

    st.subheader("Researcher triage queue")
    triage_df = df[df["researcher_attention_suggested"]].copy()
    if triage_df.empty:
        st.info("No observation is currently flagged for concern-based researcher triage.")
    else:
        status_filter = st.multiselect(
            "Researcher status",
            ["pending", "reviewed", "follow_up_recommended", "no_further_action"],
            default=["pending", "reviewed", "follow_up_recommended", "no_further_action"],
            format_func=researcher_status_label,
            key="triage_status_filter",
        )
        filtered_triage = triage_df[triage_df["researcher_review_status"].isin(status_filter)].copy()
        if filtered_triage.empty:
            st.info("No triage records match the selected status filter.")
        else:
            queue_view = pd.DataFrame({
                "ID": filtered_triage["id"].astype(int),
                "Submitted": filtered_triage["created_at"].map(_display_timestamp),
                "Site": filtered_triage["site_name"].fillna("Unnamed site"),
                "Final assessment": filtered_triage["final_overall_quality"].map(pretty),
                "Concern indicators": filtered_triage["concern_indicator_count"].astype(int),
                "Direct pressures": filtered_triage["direct_pressure_count"].astype(int),
                "ML novelty": filtered_triage["final_ml_signal"].map(ml_signal_label),
                "Researcher status": filtered_triage["researcher_review_status"].map(researcher_status_label),
            })
            st.dataframe(queue_view, use_container_width=True, hide_index=True)

            ids = filtered_triage["id"].astype(int).tolist()
            st.markdown("### Researcher review workspace")
            selected_id = st.selectbox(
                "Select an observation to review",
                ids,
                format_func=lambda x: f"#{x} — {filtered_triage.loc[filtered_triage['id'] == x, 'site_name'].iloc[0] or 'Unnamed site'}",
                key="dashboard_triage_record",
            )
            record = fetch_observation(int(selected_id))
            if record:
                original_obs = json.loads(record["original_observation_json"])
                final_obs = json.loads(record["final_observation_json"])
                original_analysis = json.loads(record["original_analysis_json"])
                final_analysis = json.loads(record["final_analysis_json"])

                with st.expander("1. Full citizen observation", expanded=True):
                    meta1, meta2, meta3 = st.columns(3)
                    meta1.write(f"**Site**\n\n{record.get('site_name') or 'Unnamed site'}")
                    meta2.write(f"**Submitted**\n\n{_display_timestamp(record.get('created_at'))}")
                    meta3.write(f"**Citizen decision**\n\n{decision_label(record['user_decision'])}")

                    if record.get("observer_note"):
                        st.write(f"**Observer note:** {record['observer_note']}")

                    ordered_groups = FIELD_GROUPS + [("Overall assessment", [QUALITY])]
                    for group_name, fields in ordered_groups:
                        rows = []
                        for field_key, label, _options in fields:
                            before = original_obs.get(field_key)
                            after = final_obs.get(field_key)
                            rows.append({
                                "Field": label,
                                "Original submission": pretty(before),
                                "Final reviewed value": pretty(after),
                                "Changed": "Yes" if before != after else "No",
                            })
                        st.markdown(f"**{group_name}**")
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                with st.expander("2. AI screening evidence", expanded=True):
                    a, b, c, d = st.columns(4)
                    a.metric("Rule flags", f"{record['original_rule_flags']} → {record['final_rule_flags']}")
                    b.metric("Rare reference fields", f"{record['original_rare_fields']} → {record['final_rare_fields']}")
                    c.metric(
                        "ML novelty",
                        f"{ml_signal_label(record['original_ml_signal'])} → {ml_signal_label(record['final_ml_signal'])}",
                    )
                    d.metric("Concern indicators", int(record.get("concern_indicator_count") or 0))

                    final_consistency = final_analysis.get("consistency") or {}
                    rule_flags = final_consistency.get("rule_flags") or []
                    rare_fields = (final_consistency.get("conditional_rarity") or {}).get("rare_fields") or []
                    concerns = final_analysis.get("concern_indicators") or {}
                    concern_items = (concerns.get("direct_pressure_indicators") or []) + (concerns.get("contextual_indicators") or [])

                    if rule_flags:
                        st.write("**Current consistency findings**")
                        for flag in rule_flags:
                            st.write(f"- {flag.get('message', 'Consistency review signal')}")
                    if rare_fields:
                        st.write("**Current reference-comparison findings**")
                        for item in rare_fields[:8]:
                            st.write(f"- {item.get('message', 'Uncommon reference pattern')}")
                    if concern_items:
                        st.write("**Reported concern indicators**")
                        for item in concern_items:
                            st.write(f"- {item.get('label', 'Concern indicator')}")
                    if not rule_flags and not rare_fields and not concern_items and ml_signal_label(record['final_ml_signal']) == "None":
                        st.info("No current screening evidence is listed for this observation.")

                with st.expander("3. Citizen review history", expanded=True):
                    h1, h2, h3 = st.columns(3)
                    h1.write(f"**Citizen decision**\n\n{decision_label(record['user_decision'])}")
                    h2.write(f"**Original assessment**\n\n{pretty(record['original_overall_quality'])}")
                    h3.write(f"**Final assessment**\n\n{pretty(record['final_overall_quality'])}")

                    changed = []
                    for key in sorted(set(original_obs) | set(final_obs)):
                        if original_obs.get(key) != final_obs.get(key):
                            changed.append({
                                "Field": field_label(key),
                                "Before": pretty(original_obs.get(key)),
                                "After": pretty(final_obs.get(key)),
                            })
                    if changed:
                        st.write("**Changes made after citizen review**")
                        st.dataframe(pd.DataFrame(changed), use_container_width=True, hide_index=True)
                    else:
                        st.info("The citizen completed review without changing the submitted observation.")

                st.markdown("### Record researcher decision")
                st.caption("Review the full observation and screening evidence above before recording a triage decision.")
                acknowledgement = st.checkbox(
                    "I reviewed the observation details and screening evidence.",
                    key=f"researcher_ack_{selected_id}",
                )

                status_options = ["pending", "reviewed", "follow_up_recommended", "no_further_action"]
                current_status = record["researcher_review_status"]
                status_index = status_options.index(current_status) if current_status in status_options else 0
                new_status = st.selectbox(
                    "Researcher review status",
                    status_options,
                    index=status_index,
                    format_func=researcher_status_label,
                    key=f"status_{selected_id}",
                )
                note = st.text_area(
                    "Researcher note",
                    value=record.get("researcher_note") or "",
                    placeholder="Record what was reviewed and any follow-up rationale.",
                    key=f"note_{selected_id}",
                )
                if not acknowledgement:
                    st.caption("Confirm that you reviewed the observation and evidence to enable saving.")
                if st.button(
                    "Save researcher review",
                    type="primary",
                    disabled=not acknowledgement,
                ):
                    update_researcher_review(int(selected_id), new_status, note)
                    st.success("Researcher review saved.")
                    st.rerun()

    st.subheader("Observation history")
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search = st.text_input("Search site", placeholder="Type part of a site name", key="history_search")
    with f2:
        assessment_options = sorted(x for x in df["final_overall_quality"].dropna().unique())
        assessments = st.multiselect("Final assessment", assessment_options, format_func=pretty, key="history_assessment")
    with f3:
        only_revised = st.checkbox("Revised only", key="history_revised_only")

    history_df = df.copy()
    if search.strip():
        history_df = history_df[history_df["site_name"].fillna("").str.contains(search.strip(), case=False, regex=False)]
    if assessments:
        history_df = history_df[history_df["final_overall_quality"].isin(assessments)]
    if only_revised:
        history_df = history_df[history_df["had_revision"]]

    st.dataframe(_display_history(history_df), use_container_width=True, hide_index=True)

    export = _display_history(df).copy()
    export_csv = export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download dashboard CSV",
        data=export_csv,
        file_name="aquaverify_observation_history.csv",
        mime="text/csv",
    )

def render_final_page():
    st.header("3. Final Assessment")
    final = st.session_state.final_analysis
    if final is None:
        st.warning("Finish the AI-assisted review before opening the final assessment.")
        if st.button("Go to AI-Assisted Review"):
            set_page("AI-Assisted Review")
        return

    saved_id = persist_completed_workflow()
    st.success("Human review step completed")
    st.write(f"**Decision recorded:** {decision_label(st.session_state.user_decision)}")
    if saved_id is not None:
        st.caption(f"Saved to SQLite observation record #{saved_id}.")
    elif st.session_state.save_error:
        st.error(f"The assessment completed, but database saving failed: {st.session_state.save_error}")

    st.subheader("Final evidence summary")
    render_evidence(final)

    original = st.session_state.original_analysis
    if original is not None and st.session_state.current_observation != st.session_state.original_observation:
        st.subheader("Before / after review")
        st.caption("This comparison shows review signals, not ecological health and not a scientific accuracy score.")
        rows = [
            ("Consistency rule flags", metric_value(original, "rules"), metric_value(final, "rules")),
            ("Rare reference fields", metric_value(original, "rare"), metric_value(final, "rare")),
            ("ML novelty signal", metric_value(original, "ml"), metric_value(final, "ml")),
            ("Citizen review status", review_label(original), review_label(final)),
        ]
        for label, before, after in rows:
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{label}**")
            c2.write(f"Before: {before}")
            c3.write(f"After: {after}")

    st.subheader("Researcher triage")
    if final["review"]["researcher_attention_suggested"]:
        st.warning("Researcher attention suggested based on reported concern indicators.")
        st.write(final["review"]["researcher_next_action"])
    else:
        st.info("AquaVerify does not suggest concern-based researcher triage for this observation.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Open Research Dashboard", use_container_width=True):
            set_page("Research Dashboard")
    with c2:
        if st.button("Start another observation", use_container_width=True):
            start_new_observation()
            st.rerun()


init_state()
apply_css()
render_sidebar()
render_header()

if st.session_state.page == "Submit Observation":
    render_submit_page()
elif st.session_state.page == "AI-Assisted Review":
    render_review_page()
elif st.session_state.page == "Final Assessment":
    render_final_page()
else:
    render_dashboard()
