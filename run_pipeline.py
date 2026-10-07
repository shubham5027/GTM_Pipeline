"""
Full GTM pipeline orchestrator.

Runs, in order:
  1. Org discovery       (Apollo: companies using the target technology)
  2. Contact discovery   (Apollo: VP/CXO/BU Head/Director contacts per org)
  3. Enrichment          (Apollo: fill in missing verified emails)
  4. Lead scoring        (rule-based, transparent, editable in stage4)
  5. Outreach drafting   (template by default; --use-llm for personalization)
  6. CRM export          (flat CSV ready for import)

Each stage reads the previous stage's output file and writes its own, so any
stage can also be re-run standalone (e.g. `python stage4_score_leads.py`)
without rerunning earlier, more expensive/API-costly stages.

Usage:
    python run_pipeline.py --max-orgs 50 --max-contacts-per-org 5
    python run_pipeline.py --max-orgs 50 --use-llm
    python run_pipeline.py --skip-discovery --skip-enrichment   # re-score/redraft only
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(f"\n{'=' * 60}\n$ {' '.join(cmd)}\n{'=' * 60}")
    result = subprocess.run([sys.executable] + cmd)
    if result.returncode != 0:
        sys.exit(f"Stage failed: {' '.join(cmd)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-orgs", type=int, default=50)
    parser.add_argument("--max-contacts-per-org", type=int, default=5)
    parser.add_argument("--max-enrichments", type=int, default=50)
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--top-n-outreach", type=int, default=0,
                         help="Only draft outreach for the top N scored contacts (0 = all)")
    parser.add_argument("--skip-discovery", action="store_true",
                         help="Skip stages 1-2, reuse existing orgs/contacts files")
    parser.add_argument("--skip-enrichment", action="store_true",
                         help="Skip stage 3 (saves enrichment credits)")
    args = parser.parse_args()

    if not args.skip_discovery:
        run(["stage1_discover_orgs.py", "--max-orgs", str(args.max_orgs)])
        run(["stage2_discover_contacts.py", "--max-contacts-per-org", str(args.max_contacts_per_org)])
    else:
        print("Skipping discovery stages (--skip-discovery)")

    if not args.skip_enrichment:
        run(["stage3_enrich_contacts.py", "--max-enrichments", str(args.max_enrichments)])
    else:
        print("Skipping enrichment stage (--skip-enrichment)")

    run(["stage4_score_leads.py"])

    outreach_cmd = ["stage5_generate_outreach.py"]
    if args.use_llm:
        outreach_cmd.append("--use-llm")
    if args.top_n_outreach:
        outreach_cmd += ["--top-n", str(args.top_n_outreach)]
    run(outreach_cmd)

    run(["stage6_export_crm.py"])

    print("\nPipeline complete. See data/06_crm_export.csv for the final output.")


if __name__ == "__main__":
    main()
