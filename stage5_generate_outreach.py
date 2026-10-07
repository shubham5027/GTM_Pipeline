"""
Stage 5 — Outreach drafting.

Reads data/04_scored.jsonl and drafts a first-touch email per contact.

Default mode uses a plain template (no API calls, no cost, always works).
If LLM_API_KEY is set in config.py, pass --use-llm to personalize each draft
with an LLM call instead — this costs API credits and calls an external
service, so it's opt-in, not automatic.

Writes data/05_outreach.jsonl.

Usage:
    python stage5_generate_outreach.py
    python stage5_generate_outreach.py --use-llm
"""

from __future__ import annotations

import argparse

import requests

import config
from jsonl_utils import read_jsonl, write_jsonl

TEMPLATE = """Subject: Quick question about Salesforce ops at {org_name}

Hi {first_name},

I noticed {org_name} runs on Salesforce and figured it's worth a quick note.
[ONE SENTENCE ON YOUR VALUE PROP — edit before sending]

Would you be open to a 15-minute call this week or next?

Best,
[YOUR NAME]
"""


def template_draft(contact: dict) -> str:
    first_name = (contact.get("name") or "there").split(" ")[0]
    return TEMPLATE.format(org_name=contact.get("org_name", "your company"), first_name=first_name)


def llm_draft(contact: dict) -> str:
    """
    Calls an LLM via OpenRouter's OpenAI-compatible chat endpoint to write a
    short, personalized first-touch email. Requires OPENROUTER_API_KEY (or
    ANTHROPIC_API_KEY, if you adapt the request body) and LLM_MODEL in your
    environment. Falls back to the template on any failure.
    """
    if not config.LLM_API_KEY or not config.LLM_MODEL:
        print("  [warn] LLM_API_KEY/LLM_MODEL not set, falling back to template")
        return template_draft(contact)

    prompt = (
        f"Write a short (under 80 words), plain, non-salesy first-touch cold "
        f"email to {contact.get('name')}, who is {contact.get('title')} at "
        f"{contact.get('org_name')}, a company using Salesforce. Include a "
        f"subject line. Leave a [VALUE PROP] placeholder for one sentence "
        f"about what we offer, since that's product-specific. No sign-off name "
        f"— leave [YOUR NAME]."
    )
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  [warn] LLM draft failed ({e}), falling back to template")
        return template_draft(contact)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use-llm", action="store_true",
                         help="Personalize drafts with an LLM call instead of the static template")
    parser.add_argument("--top-n", type=int, default=0,
                         help="Only draft for the top N scored contacts (0 = all)")
    args = parser.parse_args()

    contacts = read_jsonl(config.SCORED_FILE)
    if not contacts:
        raise SystemExit(f"No contacts found in {config.SCORED_FILE}. Run stage4 first.")

    if args.top_n:
        contacts = contacts[:args.top_n]

    for i, contact in enumerate(contacts, 1):
        print(f"[{i}/{len(contacts)}] drafting for {contact['name']} @ {contact['org_name']}...")
        contact["outreach_draft"] = llm_draft(contact) if args.use_llm else template_draft(contact)

    write_jsonl(config.OUTREACH_FILE, contacts)
    print(f"\nWrote {len(contacts)} drafts to {config.OUTREACH_FILE}")


if __name__ == "__main__":
    main()
