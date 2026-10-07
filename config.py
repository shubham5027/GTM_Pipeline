"""
Shared configuration for the GTM pipeline.

All credentials come from environment variables — never hardcode keys.
Put them in a .env file (see .env.example) or export them in your shell.
"""

from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; env vars can be set directly

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"

# Optional: set if Stage 4 (outreach drafting) should call an LLM for
# personalization instead of using static templates. Leave unset to use
# templates only — the pipeline works fine without it.
LLM_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "")

# ICP (Ideal Customer Profile) filters — edit these for your actual target market.
TARGET_TECHNOLOGY = "Salesforce"
TARGET_SENIORITIES = ["c_suite", "vp", "head", "director"]
TARGET_TITLE_KEYWORDS = [
    "VP", "Vice President", "Chief", "CXO",
    "Business Unit Head", "BU Head", "Director",
]
TARGET_EMPLOYEE_RANGES: list[str] = []   # e.g. ["201,500", "501,1000"] — [] means no filter
TARGET_INDUSTRIES: list[str] = []        # e.g. ["information technology & services"]

# Pipeline I/O — each stage reads the previous stage's file and writes its own,
# so any stage can be re-run independently without redoing earlier ones.
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ORGS_FILE = os.path.join(DATA_DIR, "01_orgs.jsonl")
CONTACTS_FILE = os.path.join(DATA_DIR, "02_contacts.jsonl")
ENRICHED_FILE = os.path.join(DATA_DIR, "03_enriched.jsonl")
SCORED_FILE = os.path.join(DATA_DIR, "04_scored.jsonl")
OUTREACH_FILE = os.path.join(DATA_DIR, "05_outreach.jsonl")
CRM_EXPORT_FILE = os.path.join(DATA_DIR, "06_crm_export.csv")

REQUEST_TIMEOUT = 30
RATE_LIMIT_SLEEP_SECONDS = 1.0

os.makedirs(DATA_DIR, exist_ok=True)


def require_apollo_key() -> str:
    if not APOLLO_API_KEY:
        sys.exit(
            "APOLLO_API_KEY is not set. Export it or add it to a .env file "
            "before running this pipeline."
        )
    return APOLLO_API_KEY
