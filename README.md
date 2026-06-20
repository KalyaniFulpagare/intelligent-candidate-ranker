# Intelligent Candidate Ranker — Redrob Hackathon

**Team:** KalyaniFulpagare
**Challenge:** Intelligent Candidate Discovery & Ranking
**Task:** Rank 100,000 candidates for a Senior AI Engineer role

---

## Approach

A transparent, rule-and-signal-based ranking pipeline with five components:

### 1. Honeypot Detection
Identifies ~66 candidates with subtly impossible profiles and excludes them.
Keeps honeypot rate in top 100 at 0%.

### 2. Hard Disqualifier Flags
Encodes the JD explicit knockouts as named penalty multipliers:
- Pure consulting career (TCS/Wipro/Infosys/etc.) -> 0.85 severity
- Research-only, no production evidence -> 0.75 severity
- CV/speech skills with no NLP/IR -> 0.70 severity
- Title-chasing pattern (3+ roles under 18 months) -> 0.50 severity
- Outside India, not willing to relocate -> 0.50 severity

### 3. Trust-Weighted Skill Score
Each skill scored by: proficiency x duration x endorsements x assessment_score.
Gated by career plausibility (ML evidence in job descriptions).
HR Managers listing Pinecone dropped from 0.65 to 0.06 after plausibility gate.

### 4. Behavioral Signal Modifier
Converts 23 redrob_signals into availability/engagement score.
Compresses to [0.5, 1.0] so it modifies but never dominates relevance.

### 5. Final Score Formula

    final = relevance x disqualifier_multiplier x behavioral_modifier
    relevance = 0.70 x skill_score + 0.30 x seniority_score
    disq_multiplier = product of (1 - severity) for all flags
    behavioral_modifier = 0.5 + 0.5 x behavioral_score

---

## Reproduce Submission

### Step 1: Pre-computation (run once)
    python precompute.py --candidates ./candidates.jsonl --out ./data/

### Step 2: Ranking (<=5 min, CPU only, no network)
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

### Step 3: Validate
    python validate_submission.py submission.csv

---

## Performance
- Runtime: ~30 seconds for 100K candidates on CPU
- Memory: <2GB peak (streams JSONL line by line)
- Honeypots in top 100: 0
- All top 100: India-based ML/AI engineers at product companies

---

## Files

    rank.py                  Main ranking script
    precompute.py            Honeypot pre-computation
    src/constants.py         JD-derived constants
    src/honeypot.py          Honeypot detector
    src/scoring.py           All scoring functions
    src/reasoning.py         Reasoning string generator
    data/honeypot_ids.json   Pre-computed honeypot IDs
    outputs/submission.csv   Final ranked output
