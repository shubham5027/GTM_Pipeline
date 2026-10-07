"""
Stage 3 — Enrichment.

Reads data/02_contacts.jsonl and, for any contact missing a verified email,
calls Apollo's person-match/enrichment endpoint to try to fill it in. This
typically costs a separate credit per lookup, so it's a distinct stage you
can skip or throttle independently of discovery.

Writes data/03_enriched.jsonl.

Usage:
    python stage3_enrich_contacts.py --max-enrichments 50
"""

from __future__ import annotations

import argparse
import time

import apollo_client
import config
from jsonl_utils import read_jsonl, write_jsonl


def enrich_contacts(contacts: list[dict], max_enrichments: int) -> list[dict]:
    enriched = []
    calls_made = 0

    for i, contact in enumerate(contacts, 1):
        if contact.get("email") or calls_made >= max_enrichments:
            enriched.append(contact)
            continue

        print(f"[{i}/{len(contacts)}] enriching {contact['name']} ({contact['org_name']})...")
        data = apollo_client.match_person(contact["person_id"])
        calls_made += 1
        time.sleep(config.RATE_LIMIT_SLEEP_SECONDS)

        person = data.get("person", {}) if data else {}
        contact["email"] = person.get("email", contact.get("email", ""))
        contact["email_status"] = person.get("email_status", "unknown")
        enriched.append(contact)

    skipped = len(contacts) - calls_made - sum(1 for c in contacts if c.get("email"))
    print(f"\nEnriched {calls_made} contacts; "
          f"{sum(1 for c in enriched if c.get('email'))} now have an email on file.")
    return enriched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-enrichments", type=int, default=50,
                         help="Cap on enrichment API calls, since these cost credits")
    args = parser.parse_args()

    contacts = read_jsonl(config.CONTACTS_FILE)
    if not contacts:
        raise SystemExit(f"No contacts found in {config.CONTACTS_FILE}. Run stage2 first.")

    enriched = enrich_contacts(contacts, max_enrichments=args.max_enrichments)
    write_jsonl(config.ENRICHED_FILE, enriched)
    print(f"Wrote {len(enriched)} contacts to {config.ENRICHED_FILE}")


if __name__ == "__main__":
    main()
