"""
Stage 6 — CRM export.

Reads data/05_outreach.jsonl and writes a flat CSV formatted for import into
a CRM (Salesforce, HubSpot, etc.) or a spreadsheet-based outreach tracker.

Usage:
    python stage6_export_crm.py
"""

from __future__ import annotations

import csv

import config
from jsonl_utils import read_jsonl

FIELDNAMES = [
    "priority_score", "name", "title", "seniority", "email", "email_status",
    "linkedin_url", "org_name", "org_industry", "org_employee_count",
    "outreach_draft", "score_reasons",
]


def main() -> None:
    contacts = read_jsonl(config.OUTREACH_FILE)
    if not contacts:
        raise SystemExit(f"No contacts found in {config.OUTREACH_FILE}. Run stage5 first.")

    with open(config.CRM_EXPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for c in contacts:
            row = dict(c)
            if isinstance(row.get("score_reasons"), list):
                row["score_reasons"] = " | ".join(row["score_reasons"])
            writer.writerow(row)

    print(f"Wrote {len(contacts)} rows to {config.CRM_EXPORT_FILE}")


if __name__ == "__main__":
    main()
