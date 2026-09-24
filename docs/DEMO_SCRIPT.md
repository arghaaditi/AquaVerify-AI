# AquaVerify 4-Minute Demo Script

## 0:00–0:30 — Problem

“Citizen science can expand stream monitoring, but structured observations can be incomplete, internally inconsistent, or unusual. Reviewing every submission manually does not scale. AquaVerify helps identify which observations deserve another look, explains why, and keeps humans in control.”

Show the prototype boundary banner.

## 0:30–1:05 — Healthy / consistent

Load **Healthy / consistent**.

Show that:

- rule flags = 0;
- rare reference fields = 0;
- ML novelty = none;
- concern indicators = 0;
- no citizen correction is requested.

Key line: “No signal does not certify stream health; it only means this prototype did not trigger a review signal.”

## 1:05–1:45 — Concerning but consistent

Load **Concerning but consistent**.

Show:

- citizen correction is **not** requested;
- concern indicators are reported;
- researcher triage **is** suggested.

Key line: **“Bad environmental conditions do not imply bad citizen data.”**

## 1:45–2:45 — Contradictory + human-in-the-loop

Load **Contradictory assessment**.

Show rule flags and reference rarity. Explain that ML may remain `None` because the detailed degraded pattern itself can be plausible; the conflict is between the detailed fields and the citizen's `Good` summary.

Click **Edit Observation** and change only:

`Overall ecosystem quality: Good → Poor`

Re-run review.

Show:

- rule flags: 6 → 0;
- rare fields: 10 → 0;
- concern indicators remain;
- citizen correction is no longer requested.

Key line: “AquaVerify suggested review; the human made the correction.”

## 2:45–3:35 — Research dashboard

Open the dashboard.

Show:

- stored observations;
- revised count;
- triage count;
- triage queue;
- audit trail;
- researcher status/note;
- observation history;
- CSV export.

Optionally use **Reset & seed 3 canonical demo records** before recording to guarantee a clean dashboard.

## 3:35–4:00 — Responsible AI / close

“AquaVerify is not a pollution classifier and does not claim laboratory accuracy from synthetic data. It combines transparent rules, reference statistics, novelty detection, and human review to prioritize attention while preserving citizen and expert judgment.”
