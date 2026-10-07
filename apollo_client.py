"""
Minimal Apollo.io API client.

IMPORTANT — verify before a large run:
Apollo's endpoint and parameter names have changed across API versions.
Confirm against https://docs.apollo.io that these are still correct for your
plan:
  - organizations/search : q_organization_technology_names, page, per_page
  - people/search         : organization_ids, person_seniorities, person_titles
  - people/match          : for single-contact enrichment (email/phone reveal)
If a call returns an empty result where you expect matches, that's the most
likely cause — Apollo tends to fail silently rather than error on a bad param
name.
"""

from __future__ import annotations

import sys
import time

import requests

import config


def _post(endpoint: str, payload: dict) -> dict:
    url = f"{config.APOLLO_BASE_URL}/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": config.require_apollo_key(),
    }
    for attempt in range(5):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            print(f"  [warn] request error ({e}), retrying...", file=sys.stderr)
            time.sleep(2 ** attempt)
            continue

        if resp.status_code == 429:
            wait = 2 ** attempt * 2
            print(f"  [rate limited] waiting {wait}s...", file=sys.stderr)
            time.sleep(wait)
            continue
        if resp.status_code in (401, 403):
            sys.exit(
                f"Auth error ({resp.status_code}) calling {endpoint}. "
                f"Check APOLLO_API_KEY and plan access.\nResponse: {resp.text[:300]}"
            )
        if not resp.ok:
            print(f"  [warn] {endpoint} -> {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
            return {}

        time.sleep(config.RATE_LIMIT_SLEEP_SECONDS)
        return resp.json()

    print(f"  [error] giving up on {endpoint} after repeated failures", file=sys.stderr)
    return {}


def search_organizations(technology: str, page: int, per_page: int,
                          employee_ranges: list[str], industries: list[str]) -> dict:
    payload = {
        "q_organization_technology_names": [technology],
        "page": page,
        "per_page": per_page,
    }
    if employee_ranges:
        payload["organization_num_employees_ranges"] = employee_ranges
    if industries:
        payload["q_organization_industries"] = industries
    return _post("organizations/search", payload)


def search_people(organization_id: str, seniorities: list[str], titles: list[str],
                   page: int, per_page: int) -> dict:
    payload = {
        "organization_ids": [organization_id],
        "person_seniorities": seniorities,
        "person_titles": titles,
        "page": page,
        "per_page": per_page,
    }
    return _post("people/search", payload)


def match_person(person_id: str) -> dict:
    """
    Enrich a single person record (e.g. reveal verified email) via Apollo's
    match/enrichment endpoint. This typically consumes a separate credit from
    search — confirm your plan's credit model before running this at volume.
    """
    payload = {"id": person_id, "reveal_personal_emails": False}
    return _post("people/match", payload)
