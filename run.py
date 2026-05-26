#!/usr/bin/env python3
"""
SCOPE: Scenario-based Operational Pipeline for Ethics Impact Assessment

Runs the full pipeline on a PDF document and writes structured JSON outputs
to outputs/<run_id>/.

Usage:
    python run.py path/to/document.pdf
    python run.py path/to/document.pdf --lang en
    python run.py path/to/document.pdf --lang ko --run-id my-run

    # Resume or re-run a specific step (each step checkpoints to disk):
    python run.py --resume <run_id>
    python run.py --resume <run_id> --from-step event_verify
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


STEPS = [
    "parse",
    "workflow_entity",
    "entity_role",
    "event_verify",
    "sim",
    "impact",
]

OUTPUT_FILES = {
    "parse":           ["parsed.md"],
    "workflow_entity": ["workflows.json", "entities.json"],
    "entity_role":     ["entity_roles.json", "stakeholder_agents.json"],
    "event_verify":    ["verified_events.json"],
    "sim":             ["merged_scenarios.md"],
    "impact":          ["impact_report.json"],
}


def get_run_dir(run_id: str) -> Path:
    from config import OUTPUTS_DIR
    d = OUTPUTS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_pipeline(pdf_path: Path, lang: str, run_id: str, from_step: str | None = None):
    from services.run_manager import generate_run_id
    if not run_id:
        run_id = generate_run_id()

    run_dir = get_run_dir(run_id)
    pdf_dest = run_dir / "input.pdf"
    if not pdf_dest.exists():
        shutil.copy2(pdf_path, pdf_dest)

    # Delete checkpoints from from_step onward so they re-run
    if from_step and from_step in STEPS:
        idx = STEPS.index(from_step)
        for step in STEPS[idx:]:
            for fname in OUTPUT_FILES.get(step, []):
                p = run_dir / fname
                if p.exists():
                    p.unlink()
                    print(f"  [reset] deleted {fname}")

    print(f"\nRun ID : {run_id}")
    print(f"Output : {run_dir}")
    print(f"Lang   : {lang}\n")

    from pipeline.graph import compile_graph
    graph = compile_graph()

    initial_state = {
        "run_id": run_id,
        "pdf_path": str(pdf_dest),
        "language": lang,
    }

    for event in graph.stream(initial_state, stream_mode="updates"):
        node_name = list(event.keys())[0]
        files = OUTPUT_FILES.get(node_name, [])
        label = ", ".join(files) if files else node_name
        print(f"  [done] {node_name} → {label}")

    print(f"\nFinished. All outputs in: {run_dir}/")
    print("\nOutput files:")
    for f in sorted(run_dir.iterdir()):
        if f.suffix in (".json", ".md") and not f.name.startswith("_"):
            size = f.stat().st_size
            print(f"  {f.name:<35} {size:>8,} bytes")

    return run_id


def main():
    parser = argparse.ArgumentParser(
        description="SCOPE — AI Ethics Impact Assessment Pipeline"
    )
    parser.add_argument("pdf", nargs="?", help="Path to the PDF document to analyze")
    parser.add_argument(
        "--lang", choices=["ko", "en"], default="ko",
        help="Output language: 'ko' (Korean) or 'en' (English). Default: ko",
    )
    parser.add_argument("--run-id", default="", help="Custom run ID (auto-generated if omitted)")
    parser.add_argument("--resume", metavar="RUN_ID", help="Resume an existing run")
    parser.add_argument(
        "--from-step",
        choices=STEPS,
        help="When resuming, re-run from this step onward (deletes its checkpoint)",
    )
    args = parser.parse_args()

    if args.resume:
        run_id = args.resume
        from config import OUTPUTS_DIR
        run_dir = OUTPUTS_DIR / run_id
        pdf_dest = run_dir / "input.pdf"
        if not pdf_dest.exists():
            print(f"Error: run {run_id} not found or missing input.pdf")
            sys.exit(1)
        run_pipeline(pdf_dest, args.lang, run_id, from_step=args.from_step)
    elif args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: file not found: {pdf_path}")
            sys.exit(1)
        run_pipeline(pdf_path, args.lang, args.run_id, from_step=args.from_step)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
