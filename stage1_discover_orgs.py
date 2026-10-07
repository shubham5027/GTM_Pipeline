"""
Stage 1 — Organization discovery.

Finds companies matching the ICP technology/industry/size filters in
config.py (default: companies using Salesforce) and writes them to
data/01_orgs.jsonl.

Usage:
    python stage1_discover_orgs.py --max-orgs 50
"""

from __future__ import annotations

import argparse

import apollo_client
import config
from jsonl_utils import write_jsonl


def discover_orgs(max_orgs: int, page_size: int = 25) -> list[dict]:
    orgs: list[dict] = []
    page = 1

    print(f"Searching for organizations using {config.TARGET_TECHNOLOGY}...")
    while len(orgs) < max_orgs:
        data = apollo_client.search_organizations(
            technology=config.TARGET_TECHNOLOGY,
            page=page,
            per_page=min(page_size, max_orgs - len(orgs)),
            employee_ranges=config.TARGET_EMPLOYEE_RANGES,
            industries=config.TARGET_INDUSTRIES,
        )
        if not data:
            break

        batch = data.get("organizations") or data.get("accounts") or []
        if not batch:
            print("  no more results.")
            break

        for o in batch:
            orgs.append({
                "org_id": str(o.get("id", "")),
                "org_name": o.get("name", ""),
                "website": o.get("website_url", "") or o.get("primary_domain", ""),
                "industry": o.get("industry", ""),
                "employee_count": o.get("estimated_num_employees"),
                "linkedin_url": o.get("linkedin_url", ""),
            })
            if len(orgs) >= max_orgs:
                break

        total_pages = data.get("pagination", {}).get("total_pages", page)
        print(f"  page {page}/{total_pages} -> {len(orgs)} orgs so far")
        if page >= total_pages:
            break
        page += 1

    return orgs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-orgs", type=int, default=50)
    args = parser.parse_args()

    orgs = discover_orgs(max_orgs=args.max_orgs)
    write_jsonl(config.ORGS_FILE, orgs)
    print(f"\nWrote {len(orgs)} organizations to {config.ORGS_FILE}")


if __name__ == "__main__":
    main()
