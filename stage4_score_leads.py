"""
Stage 4 — Lead scoring.

Reads data/03_enriched.jsonl and assigns each contact a simple, transparent
0-100 priority score based on seniority fit, company size fit, and data
completeness (do we actually have a usable email?). This is intentionally
rule-based and editable, not a black box — adjust the weights below to match
how your team actually prioritizes.

Writes data/04_scored.jsonl, sorted highest-priority first.

Usage:
    python stage4_score_leads.py
"""

from __future__ import annotations

import config
from jsonl_utils import read_jsonl, write_jsonl

# Edit these weights to match your actual GTM priorities.
SENIORITY_SCORES = {
    "c_suite": 40,
    "vp": 35,
    "head": 25,
    "director": 20,
}
EMAIL_PRESENT_SCORE = 20
VERIFIED_EMAIL_BONUS = 10          # on top of EMAIL_PRESENT_SCORE, if email_status == "verified"
EMPLOYEE_COUNT_SWEET_SPOT = (200, 5000)  # orgs in this range score higher — edit to your ICP
EMPLOYEE_COUNT_SWEET_SPOT_SCORE = 15
EMPLOYEE_COUNT_OTHER_SCORE = 5
HAS_LINKEDIN_SCORE = 5


def score_contact(contact: dict) -> tuple[int, list[str]]:
    """Returns (score, reasons) so the score is always explainable, not a black box."""
    score = 0
    reasons = []

    seniority = (contact.get("seniority") or "").lower()
    seniority_pts = SENIORITY_SCORES.get(seniority, 10)
    score += seniority_pts
    reasons.append(f"seniority '{seniority or 'unknown'}': +{seniority_pts}")

    if contact.get("email"):
        score += EMAIL_PRESENT_SCORE
        reasons.append(f"has email: +{EMAIL_PRESENT_SCORE}")
        if contact.get("email_status") == "verified":
            score += VERIFIED_EMAIL_BONUS
            reasons.append(f"verified email: +{VERIFIED_EMAIL_BONUS}")
    else:
        reasons.append("no email on file: +0")

    employees = contact.get("org_employee_count")
    if isinstance(employees, (int, float)):
        low, high = EMPLOYEE_COUNT_SWEET_SPOT
        if low <= employees <= high:
            score += EMPLOYEE_COUNT_SWEET_SPOT_SCORE
            reasons.append(f"company size {int(employees)} in sweet spot: +{EMPLOYEE_COUNT_SWEET_SPOT_SCORE}")
        else:
            score += EMPLOYEE_COUNT_OTHER_SCORE
            reasons.append(f"company size {int(employees)} outside sweet spot: +{EMPLOYEE_COUNT_OTHER_SCORE}")

    if contact.get("linkedin_url"):
        score += HAS_LINKEDIN_SCORE
        reasons.append(f"has LinkedIn: +{HAS_LINKEDIN_SCORE}")

    return min(score, 100), reasons


def main() -> None:
    contacts = read_jsonl(config.ENRICHED_FILE)
    if not contacts:
        raise SystemExit(f"No contacts found in {config.ENRICHED_FILE}. Run stage3 first.")

    for contact in contacts:
        score, reasons = score_contact(contact)
        contact["priority_score"] = score
        contact["score_reasons"] = reasons

    contacts.sort(key=lambda c: c["priority_score"], reverse=True)

    write_jsonl(config.SCORED_FILE, contacts)
    print(f"Scored {len(contacts)} contacts. Top 5:")
    for c in contacts[:5]:
        print(f"  {c['priority_score']:>3}  {c['name']} — {c['title']} @ {c['org_name']}")
    print(f"\nWrote {len(contacts)} scored contacts to {config.SCORED_FILE}")


if __name__ == "__main__":
    main()
