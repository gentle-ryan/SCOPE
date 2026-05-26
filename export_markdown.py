#!/usr/bin/env python3
"""
Convert impact_report.json to a readable Markdown report.

Usage:
    python export_markdown.py outputs/<run_id>/impact_report.json
    python export_markdown.py outputs/<run_id>/impact_report.json -o report.md
"""

import argparse
import json
from pathlib import Path


def render_grade(g: dict) -> str:
    if not g:
        return ""
    grade = g.get("grade", "")
    reason = g.get("reason", "")
    return f"**{grade}** — {reason}" if reason else f"**{grade}**"


def render_impact_item(item: dict, impact_type: str) -> str:
    lines = []
    lines.append(f"#### {item.get('keyword', '')}")
    lines.append(f"\n{item.get('impact', '')}\n")

    grades = []
    for label, key in [("Scale", "scale"), ("Scope", "scope"), ("Likelihood", "likelihood")]:
        g = item.get(key, {})
        if g:
            grades.append(f"- **{label}:** {render_grade(g)}")
    if impact_type == "negative" and item.get("resolvability"):
        grades.append(f"- **Resolvability:** {render_grade(item['resolvability'])}")
    if grades:
        lines.append("\n".join(grades))

    ev = item.get("evidence_scenario")
    if ev:
        lines.append(f"\n> Evidence: {ev}")

    return "\n".join(lines)


def render_not_found(nf: dict) -> str:
    lines = []
    lines.append(f"#### {nf.get('item', '')}")
    lines.append(f"\n{nf.get('description', '')}\n")
    rec = nf.get("recommendation", "")
    if rec:
        lines.append(f"> **Recommendation:** {rec}")
    return "\n".join(lines)


def convert(report_path: Path) -> str:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assessment = (
        data.get("total_system_report", {}).get("ethics_assessment", [])
    )

    lines = ["# SCOPE Ethics Impact Assessment Report\n"]

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Code | Ethics Principle | Positive | Negative | Not Found |")
    lines.append("|---|---|---|---|---|")
    for code in assessment:
        lines.append(
            f"| {code['code']} | {code['name']} "
            f"| {len(code.get('positives', []))} "
            f"| {len(code.get('negatives', []))} "
            f"| {len(code.get('not_found', []))} |"
        )
    lines.append("")

    # Detail per code
    for code in assessment:
        lines.append(f"---\n\n## {code['code']}. {code['name']}\n")

        positives = code.get("positives", [])
        negatives = code.get("negatives", [])
        not_found = code.get("not_found", [])

        if positives:
            lines.append(f"### Positive Impacts ({len(positives)})\n")
            for item in positives:
                lines.append(render_impact_item(item, "positive"))
                lines.append("")

        if negatives:
            lines.append(f"### Negative Impacts ({len(negatives)})\n")
            for item in negatives:
                lines.append(render_impact_item(item, "negative"))
                lines.append("")

        if not_found:
            lines.append(f"### Not Found ({len(not_found)})\n")
            for nf in not_found:
                lines.append(render_not_found(nf))
                lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export impact_report.json to Markdown")
    parser.add_argument("report", help="Path to impact_report.json")
    parser.add_argument("-o", "--output", help="Output .md file (default: print to stdout)")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Error: {report_path} not found")
        raise SystemExit(1)

    md = convert(report_path)

    if args.output:
        out = Path(args.output)
        out.write_text(md, encoding="utf-8")
        print(f"Saved: {out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
