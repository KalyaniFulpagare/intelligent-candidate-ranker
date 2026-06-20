"""
Core scoring functions:
  - compute_disqualifiers: named JD-derived penalty flags
  - compute_skill_score_v2: trust-weighted skill match gated by career plausibility
  - compute_behavioral_score: availability/engagement composite from redrob_signals
  - compute_final_score: combines all components into one score
"""
from datetime import datetime
from src.constants import (
    ML_TITLES, TIER_1_TITLES, TIER_2_TITLES, TIER_3_TITLES,
    CONSULTING_FIRMS, NON_PRODUCT, CV_SPEECH_SKILLS, NLP_IR_SKILLS,
    RESEARCH_ONLY_SIGNALS, PRODUCTION_SIGNALS,
    JD_MUST_HAVE_SKILLS, JD_NICE_TO_HAVE_SKILLS, JD_NEGATIVE_SKILLS,
    ML_EVIDENCE_KEYWORDS, PROF_WEIGHTS
)


def is_consulting(name: str) -> bool:
    c = name.lower().strip()
    return any(f in c for f in CONSULTING_FIRMS) or any(f in c for f in NON_PRODUCT)


def compute_disqualifiers(candidate: dict) -> dict:
    """
    Returns named flags with severity [0,1].
    Flags encode JD explicit disqualifiers: consulting-only career,
    research-only, CV/speech without NLP/IR, title-chasing, location.
    """
    flags = {}
    p = candidate["profile"]
    career = candidate["career_history"]
    skills = candidate["skills"]
    sl = {s["name"].lower() for s in skills}
    desc = " ".join(j.get("description", "").lower() for j in career)

    # Consulting/generic company career
    if career:
        cos = [j["company"] for j in career]
        cj = [c for c in cos if is_consulting(c)]
        if len(cj) == len(cos):
            flags["pure_consulting"] = {
                "severity": 0.85,
                "detail": f"All {len(cos)} jobs at consulting/generic firms"
            }
        elif len(cj) >= len(cos) - 1 and len(cos) >= 3:
            flags["mostly_consulting"] = {
                "severity": 0.4,
                "detail": f"{len(cj)}/{len(cos)} jobs at consulting firms"
            }

    # Research-only signals
    res = sl & RESEARCH_ONLY_SIGNALS
    prod = sl & PRODUCTION_SIGNALS
    prod_text = any(k in desc for k in [
        "production", "deployed", "shipped", "real users",
        "a/b test", "inference", "serving", "pipeline"
    ])
    if res and not prod and not prod_text:
        flags["research_only"] = {
            "severity": 0.75, "detail": "Research signals, no production evidence"
        }

    # CV/speech without NLP/IR
    cv = sl & CV_SPEECH_SKILLS
    nlp = sl & NLP_IR_SKILLS
    if cv and not nlp:
        flags["cv_no_nlp"] = {"severity": 0.7, "detail": "CV/speech skills, no NLP/IR"}
    elif cv and nlp:
        flags["cv_with_nlp"] = {"severity": 0.1, "detail": "CV/speech + some NLP/IR"}

    # Title-chasing pattern
    if career:
        short = [
            j for j in career
            if not j.get("is_current") and j.get("duration_months", 99) < 18
        ]
        if len(short) >= 3:
            flags["title_chaser"] = {
                "severity": 0.5, "detail": f"{len(short)} roles under 18 months"
            }
        elif len(short) == 2 and len(career) <= 3:
            flags["title_chaser"] = {
                "severity": 0.25, "detail": f"{len(short)}/{len(career)} roles <18mo"
            }

    # ML title with no ML evidence in descriptions
    title = p["current_title"]
    if title in ML_TITLES:
        ml_text = any(k in desc for k in [
            "model", "train", "embedding", "retrieval", "ranking",
            "ml", "machine learning", "neural", "nlp", "inference",
            "vector", "classifier", "recommendation"
        ])
        if not ml_text:
            flags["ml_no_evidence"] = {
                "severity": 0.8, "detail": "ML title but no ML in descriptions"
            }

    # Location fit
    country = p.get("country", "").lower()
    loc = p.get("location", "").lower()
    willing = candidate["redrob_signals"].get("willing_to_relocate", False)
    preferred = {"pune", "noida"}
    india_cities = {
        "pune", "noida", "bangalore", "bengaluru", "mumbai", "delhi",
        "hyderabad", "chennai", "gurgaon", "gurugram", "kolkata", "ahmedabad",
        "kochi", "coimbatore", "indore", "jaipur", "trivandrum", "vizag",
        "bhubaneswar", "chandigarh"
    }
    if country == "india":
        if any(c in loc for c in preferred):
            flags["loc_preferred"] = {"severity": 0.0, "detail": "Pune/Noida preferred"}
        elif any(c in loc for c in india_cities):
            flags["loc_india_t1"] = {"severity": 0.0, "detail": "Tier-1 Indian city"}
        else:
            flags["loc_india_other"] = {"severity": 0.05, "detail": "India smaller city"}
    else:
        if willing:
            flags["loc_outside_relocate"] = {
                "severity": 0.2, "detail": "Outside India, willing to relocate"
            }
        else:
            flags["loc_outside_no"] = {
                "severity": 0.5, "detail": "Outside India, not willing to relocate"
            }
    return flags


def compute_disqualifier_score(flags: dict) -> float:
    m = 1.0
    for _, d in flags.items():
        m *= (1.0 - d["severity"])
    return max(0.0, m)


def compute_career_plausibility(candidate: dict) -> float:
    """
    How plausible is it this person actually did ML/AI work?
    Reads career descriptions and title history, not just skill list.
    This gates the skill score to defeat keyword stuffers.
    """
    career = candidate["career_history"]
    title = candidate["profile"]["current_title"]
    desc = " ".join(j.get("description", "").lower() for j in career)
    titles_text = " ".join(j.get("title", "").lower() for j in career)

    hits = sum(1 for kw in ML_EVIDENCE_KEYWORDS if kw in desc)
    th = sum(1 for kw in [
        "ml", "machine learning", "data science", "ai ", "nlp",
        "search", "ranking", "recommendation", "research", "engineer"
    ] if kw in titles_text)

    if title in TIER_1_TITLES: tm = 1.0
    elif title in TIER_2_TITLES: tm = 0.85
    elif title in TIER_3_TITLES: tm = 0.6
    else: tm = 0.2

    ds = 1.0 if hits>=8 else 0.75 if hits>=5 else 0.5 if hits>=3 else 0.25 if hits>=1 else 0.0
    ths = min(th / 3.0, 1.0)
    return round(0.40*tm + 0.40*ds + 0.20*ths, 4)


def _skill_trust(skill: dict, assessments: dict) -> float:
    prof = PROF_WEIGHTS.get(skill.get("proficiency", "beginner"), 0.2)
    dur = min(skill.get("duration_months", 0) / 48.0, 1.0)
    end = min(skill.get("endorsements", 0) / 20.0, 1.0)
    a = assessments.get(skill["name"], None)
    if a is not None:
        return 0.30*prof + 0.25*dur + 0.20*end + 0.25*(a/100.0)
    return 0.40*prof + 0.35*dur + 0.25*end


def compute_skill_score_v2(candidate: dict) -> dict:
    """
    Trust-weighted skill score gated by career plausibility.
    Must-have skills weighted 70%, nice-to-have 30%.
    Plausibility gate defeats keyword stuffers: an HR Manager
    listing Pinecone scores near-zero because descriptions contain
    no ML evidence.
    """
    skills = candidate["skills"]
    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})
    must = nice = neg = 0.0
    mm, mn = [], []
    for s in skills:
        nl = s["name"].lower()
        t = _skill_trust(s, assessments)
        if nl in JD_MUST_HAVE_SKILLS:
            must += t; mm.append((s["name"], round(t, 3)))
        elif nl in JD_NICE_TO_HAVE_SKILLS:
            nice += t; mn.append((s["name"], round(t, 3)))
        if nl in JD_NEGATIVE_SKILLS:
            neg += t
    must_n = min(must/4.0, 1.0)
    nice_n = min(nice/3.0, 1.0)
    neg_p  = min(neg*0.15, 0.2)
    raw = max(0.0, 0.70*must_n + 0.30*nice_n - neg_p)
    plaus = compute_career_plausibility(candidate)
    return {
        "score": round(raw*plaus, 4),
        "raw_skill_score": round(raw, 4),
        "plausibility": plaus,
        "must_have_score": round(must_n, 4),
        "nice_to_have_score": round(nice_n, 4),
        "matched_must": mm,
        "matched_nice": mn,
    }


def compute_behavioral_score(candidate: dict) -> dict:
    """
    Converts redrob_signals into availability/engagement multiplier.
    Per JD: a perfect-on-paper candidate inactive for 6 months with
    5% response rate is not actually available — down-weight them.
    """
    sig = candidate["redrob_signals"]
    try:
        days_ago = (
            datetime(2026, 6, 1) -
            datetime.strptime(sig.get("last_active_date", "2020-01-01"), "%Y-%m-%d")
        ).days
    except Exception:
        days_ago = 365

    if days_ago<=14: rec=1.0
    elif days_ago<=30: rec=0.9
    elif days_ago<=60: rec=0.75
    elif days_ago<=90: rec=0.6
    elif days_ago<=180: rec=0.35
    else: rec=0.1

    otw = 1.0 if sig.get("open_to_work_flag") else 0.6
    availability = 0.60*rec + 0.40*otw

    rr = sig.get("recruiter_response_rate", 0.0)
    rt = sig.get("avg_response_time_hours", 168)
    if rt<=4: rts=1.0
    elif rt<=24: rts=0.85
    elif rt<=48: rts=0.7
    elif rt<=96: rts=0.5
    elif rt<=168: rts=0.3
    else: rts=0.1
    responsiveness = 0.60*rr + 0.40*rts

    ic = sig.get("interview_completion_rate", 0.5)
    oa = sig.get("offer_acceptance_rate", -1)
    if oa==-1: os_=0.6
    elif oa>=0.7: os_=1.0
    elif oa>=0.4: os_=0.75
    elif oa>=0.1: os_=0.5
    else: os_=0.25

    apps = sig.get("applications_submitted_30d", 0)
    act = 1.0 if apps>=5 else 0.85 if apps>=3 else 0.7 if apps>=1 else 0.4

    nd = sig.get("notice_period_days", 90)
    ns = 1.0 if nd<=30 else 0.8 if nd<=60 else 0.6 if nd<=90 else 0.4 if nd<=120 else 0.2
    engagement = 0.30*ic + 0.25*os_ + 0.25*act + 0.20*ns

    ve = sig.get("verified_email", False)
    vp = sig.get("verified_phone", False)
    pc = sig.get("profile_completeness_score", 0) / 100.0
    lc = sig.get("linkedin_connected", False)
    credibility = 0.35*pc + 0.25*(1 if ve else 0) + 0.25*(1 if vp else 0) + 0.15*(1 if lc else 0)

    final = 0.35*availability + 0.30*responsiveness + 0.20*engagement + 0.15*credibility
    return {
        "score": round(final, 4),
        "availability": round(availability, 4),
        "responsiveness": round(responsiveness, 4),
        "engagement": round(engagement, 4),
        "credibility": round(credibility, 4),
        "notice_days": nd,
        "days_since_active": days_ago,
        "response_rate": rr,
        "open_to_work": sig.get("open_to_work_flag", False),
    }


def compute_final_score(candidate: dict, honeypot_ids: set) -> dict:
    """
    Final score = relevance × disqualifier_multiplier × behavioral_modifier

    relevance        = 0.70 × skill_score + 0.30 × seniority_score
    disq_multiplier  = product of (1 - severity) for all flags
    behavioral_modifier = 0.5 + 0.5 × behavioral_score
      (compressed to [0.5,1.0] so behavioral modifies but never dominates)
    """
    cid = candidate["candidate_id"]
    if cid in honeypot_ids:
        return {"candidate_id": cid, "final_score": 0.0, "excluded": "honeypot", "components": {}}

    p = candidate["profile"]
    yoe = p["years_of_experience"]

    if 6<=yoe<=8: sen=1.0
    elif 5<=yoe<6 or 8<yoe<=9: sen=0.9
    elif 4<=yoe<5 or 9<yoe<=11: sen=0.75
    elif 3<=yoe<4 or 11<yoe<=14: sen=0.6
    else: sen=0.3

    skill_r = compute_skill_score_v2(candidate)
    disq_f  = compute_disqualifiers(candidate)
    beh_r   = compute_behavioral_score(candidate)

    skill_s = skill_r["score"]
    disq_m  = compute_disqualifier_score(disq_f)
    beh_s   = beh_r["score"]
    relevance = 0.70*skill_s + 0.30*sen
    beh_mod   = 0.5 + 0.5*beh_s
    final = relevance * disq_m * beh_mod

    return {
        "candidate_id": cid,
        "final_score": round(final, 6),
        "excluded": None,
        "components": {
            "skill_score": skill_s,
            "seniority_score": sen,
            "relevance_score": round(relevance, 4),
            "disq_multiplier": round(disq_m, 4),
            "behavioral_score": beh_s,
            "behavioral_modifier": round(beh_mod, 4),
            "yoe": yoe,
            "title": p["current_title"],
            "company": p["current_company"],
            "location": p["location"],
            "country": p["country"],
            "disq_flags": list(disq_f.keys()),
            "matched_must": skill_r["matched_must"],
            "matched_nice": skill_r["matched_nice"],
            "notice_days": beh_r["notice_days"],
            "days_since_active": beh_r["days_since_active"],
            "response_rate": beh_r["response_rate"],
            "open_to_work": beh_r["open_to_work"],
        }
    }
