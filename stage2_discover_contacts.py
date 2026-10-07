"""
Stage 2 — Contact discovery.

Reads data/01_orgs.jsonl and, for each organization, finds contacts matching
the target seniorities/titles in config.py (default: VP / CXO / BU Head /
Director). Writes data/02_contacts.jsonl.

Usage:
    python stage2_discover_contacts.py --max-contacts-per-org 5
"""

from __future__ import annotations

import argparse

import apollo_client
import config
from jsonl_utils import read_jsonl, write_jsonl


def discover_contacts_for_org(org: dict, max_contacts: int, page_size: int = 10) -> list[dict]:
    contacts: list[dict] = []
    page = 1

    while len(contacts) < max_contacts:
        data = apollo_client.search_people(
            organization_id=org["org_id"],
            seniorities=config.TARGET_SENIORITIES,
            titles=config.TARGET_TITLE_KEYWORDS,
            page=page,
            per_page=min(page_size, max_contacts - len(contacts)),
        )
        if not data:
            break

        batch = data.get("people") or []
        if not batch:
            break

        for p in batch:
            contacts.append({
                "person_id": str(p.get("id", "")),
                "org_id": org["org_id"],
                "org_name": org["org_name"],
                "org_industry": org.get("industry", ""),
                "org_employee_count": org.get("employee_count"),
                "name": p.get("name", ""),
                "title": p.get("title", ""),
                "seniority": p.get("seniority", ""),
                "email": p.get("email", ""),
                "linkedin_url": p.get("linkedin_url", ""),
            })
            if len(contacts) >= max_contacts:
                break

        total_pages = data.get("pagination", {}).get("total_pages", page)
        if page >= total_pages:
            break
        page += 1

    return contacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-contacts-per-org", type=int, default=5)
    args = parser.parse_args()

    orgs = read_jsonl(config.ORGS_FILE)
    if not orgs:
        raise SystemExit(f"No orgs found in {config.ORGS_FILE}. Run stage1 first.")

    all_contacts: list[dict] = []
    for i, org in enumerate(orgs, 1):
        print(f"[{i}/{len(orgs)}] {org['org_name']} -> searching contacts...")
        contacts = discover_contacts_for_org(org, max_contacts=args.max_contacts_per_org)
        print(f"    found {len(contacts)} target contacts")
        all_contacts.extend(contacts)

    write_jsonl(config.CONTACTS_FILE, all_contacts)
    print(f"\nWrote {len(all_contacts)} contacts to {config.CONTACTS_FILE}")


if __name__ == "__main__":
    main()
