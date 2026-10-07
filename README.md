# GTM Pipeline

A six-stage GTM prospecting pipeline built on the Apollo.io API: find
companies matching your ICP (default: Salesforce users), find target
contacts (VP / CXO / BU Head / Director), enrich missing emails, score and
rank leads, draft first-touch outreach, and export a CRM-ready CSV.

## Why stages, not one script

Each stage reads the previous stage's output file (`data/0N_*.jsonl`) and
writes its own. This means:
- You can inspect and sanity-check the output after any stage before
  spending API credits on the next one.
- A failed or rate-limited stage can be re-run alone, without re-paying for
  earlier stages.
- You can swap out one stage's logic (e.g. the scoring weights, or the
  outreach template) without touching the rest.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and fill in APOLLO_API_KEY (and optionally OPENROUTER_API_KEY for LLM drafting)
```

Before running at any real volume, check `apollo_client.py`'s docstring and
verify the endpoint/parameter names against current Apollo docs
(https://docs.apollo.io) — API field names shift between versions and a
wrong name tends to return an empty result rather than an error.

## Configure your ICP

Edit `config.py`:
- `TARGET_TECHNOLOGY` — currently `"Salesforce"`
- `TARGET_SENIORITIES` / `TARGET_TITLE_KEYWORDS` — currently VP/CXO/Head/Director
- `TARGET_EMPLOYEE_RANGES` / `TARGET_INDUSTRIES` — optional extra filters

## Run the whole pipeline

```bash
python run_pipeline.py --max-orgs 50 --max-contacts-per-org 5
```

Start smaller the first time, to confirm the data looks right before
spending more API credits:

```bash
python run_pipeline.py --max-orgs 5 --max-contacts-per-org 3
```

## Run a single stage

Every stage is also a standalone script:

```bash
python stage1_discover_orgs.py --max-orgs 50
python stage2_discover_contacts.py --max-contacts-per-org 5
python stage3_enrich_contacts.py --max-enrichments 50
python stage4_score_leads.py
python stage5_generate_outreach.py            # template-based, no extra cost
python stage5_generate_outreach.py --use-llm  # LLM-personalized, costs LLM credits
python stage6_export_crm.py
```

## Stages

| # | Script | What it does | Output |
|---|---|---|---|
| 1 | `stage1_discover_orgs.py` | Finds orgs matching your ICP tech/industry/size filters | `data/01_orgs.jsonl` |
| 2 | `stage2_discover_contacts.py` | Finds target-title contacts within each org | `data/02_contacts.jsonl` |
| 3 | `stage3_enrich_contacts.py` | Fills in missing verified emails | `data/03_enriched.jsonl` |
| 4 | `stage4_score_leads.py` | Rule-based 0-100 priority score, with reasons | `data/04_scored.jsonl` |
| 5 | `stage5_generate_outreach.py` | Drafts a first-touch email per contact | `data/05_outreach.jsonl` |
| 6 | `stage6_export_crm.py` | Flattens everything to one CSV for CRM import | `data/06_crm_export.csv` |

## Editing the scoring logic

`stage4_score_leads.py` is deliberately rule-based and readable — every score
comes with a `score_reasons` list explaining exactly why a contact got that
number. Edit `SENIORITY_SCORES`, `EMPLOYEE_COUNT_SWEET_SPOT`, and the other
constants at the top of the file to match how your team actually prioritizes
leads.

## Things worth checking before relying on this

- **Apollo credits**: organization search, people search, and especially
  `people/match` (enrichment) typically consume separate credit pools on
  your plan. Check your plan's limits before a large `--max-orgs` run.
- **Email drafts are a starting point.** Every draft contains a
  `[VALUE PROP]` and `[YOUR NAME]` placeholder — review before sending, and
  check your organization's outbound compliance policy (CAN-SPAM, GDPR, etc.)
  for cold email.
- **LLM drafting is opt-in** (`--use-llm`) and calls an external API with
  contact names, titles, and company names. Make sure that's acceptable
  under your data-handling policies before enabling it.
