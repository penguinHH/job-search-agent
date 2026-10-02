# Fit scoring rubric (0–100)

Shared by the GUI agent (`score_company`) and Claude Code sessions. The score answers: "How worthwhile is it
for this candidate to spend effort applying here now?" It blends role fit with practical feasibility. The
candidate's role and domain preferences come from the profile ("求职偏好"); calibration anchors from earlier
batches are in the personal knowledge file (`资料/knowledge.md` → "Scoring anchors") so scores stay comparable
across sessions.

## Components (guide, not a formula)

| Weight | Component | High end looks like |
|---|---|---|
| ~40 | Role fit | An open role that matches the candidate's first-choice role type directly; then the next role types in the profile's preference order |
| ~20 | Domain fit | The profile's preferred industries |
| ~15 | Hiring signal | Concrete relevant openings on the live ATS board > open-position / "send CV" page > no careers page |
| ~15 | Practicality | Preferred location or remote; working language the candidate can use; company able to sponsor a work visa and to wait until the candidate's start date (or to offer part-time/internship before) |
| ~10 | Upside | Growth stage, strong team/funding, learning value, uses the candidate's distinctive background |

Adjustments: acquired companies usually fold into a parent — score the parent's relevance or skip. Public
companies are fine but note they are no longer early-stage.

Rough bands: 90+ near-perfect (relevant open role, practical) · 70–89 strong · 50–69 possible with clear gaps
(location, seniority, field) · 35–49 weak · <35 little relevance or impractical.

## Writing the entry

- `roles`: concrete role names, ideally the actual posting titles.
- `reasons`: facts with specifics (what they build, which posting, which skill applies).
- `concerns`: gaps (missing skills, seniority, lab experience), location, language, visa, no openings.
- Keep it in English; say "not verified" when a fact comes only from inference.
