"""
Honeypot detection: identifies candidates with subtly impossible profiles.
Spec says ~80 honeypots exist; our calibrated detector finds 66.
Honeypots are forced to relevance tier 0 in ground truth.
Submissions with >10% honeypot rate in top 100 are disqualified.
"""
from datetime import datetime
from src.constants import ML_TITLES


def detect_honeypot(candidate: dict) -> tuple[bool, list[str]]:
    """
    Returns (is_honeypot, reasons).
    Checks for impossible timelines, zero-duration expert skills,
    implausible expert skill counts, and zero endorsements on many
    advanced/expert skills.
    """
    reasons = []
    p = candidate["profile"]
    career = candidate["career_history"]
    skills = candidate["skills"]
    yoe = p["years_of_experience"]
    is_ml = p["current_title"] in ML_TITLES

    # Check 1: Stated YOE far exceeds career history span
    if career:
        try:
            earliest = min(
                datetime.strptime(j["start_date"], "%Y-%m-%d").year
                for j in career
            )
            if yoe > (2026 - earliest) + 3:
                reasons.append(
                    f"YOE={yoe} but earliest job starts {earliest}"
                )
        except Exception:
            pass

    # Check 2: Expert skill with near-zero duration
    for s in skills:
        if s.get("proficiency") == "expert" and s.get("duration_months", 999) < 3:
            reasons.append(
                f"Expert in {s['name']} with {s.get('duration_months', 0)} months"
            )

    # Check 3: Too many expert skills (higher threshold for ML titles)
    expert_count = sum(1 for s in skills if s.get("proficiency") == "expert")
    threshold = 12 if is_ml else 8
    if expert_count >= threshold:
        reasons.append(f"{expert_count} expert skills (threshold={threshold})")

    # Check 4: Career history duration vs stated YOE
    if career:
        total_months = sum(j.get("duration_months", 0) for j in career)
        if total_months < yoe * 12 * 0.4 and yoe > 3:
            reasons.append(
                f"Career={total_months/12:.1f}yr vs stated YOE={yoe}"
            )

    # Check 5: Current role duration exceeds total YOE
    for j in career:
        if j.get("is_current") and j.get("duration_months", 0) > yoe * 12:
            reasons.append("Current role duration exceeds total YOE")

    # Check 6: Many advanced/expert skills but zero total endorsements
    total_end = sum(s.get("endorsements", 0) for s in skills)
    high_prof = [s for s in skills if s.get("proficiency") in ("expert", "advanced")]
    if len(high_prof) >= 6 and total_end == 0:
        reasons.append(f"{len(high_prof)} adv/expert skills, 0 endorsements")

    return (len(reasons) > 0, reasons)
