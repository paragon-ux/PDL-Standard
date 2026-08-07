#!/usr/bin/env python3
"""Structural linter for confirm-with-pseudocode test transcripts.

Harness v2 checks the final assistant message plus commentary. Captured tool activity
is surfaced as an audit warning before execution, because the linter cannot reliably
distinguish protocol-required skill/reference loading from prohibited substantive
research. Semantic judging must make that distinction.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

PROMPT = "**Prompt Pseudocode**"
PLAN = "**Response Plan Pseudocode**"
CONFIRM_FRAGMENTS = (
    "Confirm or correct this interpretation",
    "Confirm or correct this response approach",
)


def load_jsonl(path: pathlib.Path | str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def visible_text(turn: dict[str, Any]) -> str:
    commentary = turn.get("commentary") or []
    parts = [str(item) for item in commentary if item]
    assistant = turn.get("assistant") or ""
    if assistant:
        parts.append(str(assistant))
    return "\n\n".join(parts)


def stage_issues(stage: str, text: str) -> list[str]:
    issues: list[str] = []
    has_prompt = PROMPT in text
    has_plan = PLAN in text
    has_fence = "```text" in text

    if stage in {"prompt", "prompt-preferred"}:
        if not has_prompt:
            issues.append("missing Prompt Pseudocode heading")
        if has_plan:
            issues.append("contains Response Plan Pseudocode during prompt stage")
        if not has_fence:
            issues.append("missing text pseudocode fence")
    elif stage in {"plan", "plan-preferred"}:
        if not has_plan:
            issues.append("missing Response Plan Pseudocode heading")
        if has_prompt:
            issues.append("contains Prompt Pseudocode during plan stage")
        if not has_fence:
            issues.append("missing text pseudocode fence")
    elif stage in {"execute", "execute-dependency"}:
        if has_prompt or has_plan:
            issues.append("pseudocode confirmation artifact appears during execution")
        if any(fragment in text for fragment in CONFIRM_FRAGMENTS):
            issues.append("asks for protocol confirmation during execution")
    elif stage in {"meta", "safety"}:
        if has_prompt or has_plan:
            issues.append(f"protocol artifact appears during {stage} bypass/override state")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=pathlib.Path, help="results JSONL")
    ap.add_argument(
        "--cases",
        type=pathlib.Path,
        default=pathlib.Path(__file__).with_name("cases.jsonl"),
    )
    args = ap.parse_args()

    cases = {c["id"]: c for c in load_jsonl(args.cases)}
    runs = load_jsonl(args.results)
    failures = 0
    warnings = 0
    infos = 0

    for run in runs:
        cid = run.get("case_id")
        rid = run.get("run_id", "<unnamed>")
        case = cases.get(cid)
        if not case:
            print(f"FAIL {cid}/{rid}: unknown case_id")
            failures += 1
            continue
        if run.get("notes"):
            print(f"FAIL {cid}/{rid}: runner error recorded: {run['notes']}")
            failures += 1
        if run.get("schema_version", 1) >= 2 and not run.get("provenance_id"):
            print(f"FAIL {cid}/{rid}: schema v2 result missing provenance_id")
            failures += 1

        actual = run.get("turns", [])
        expected = case["turns"]
        if len(actual) != len(expected):
            print(f"FAIL {cid}/{rid}: expected {len(expected)} turns, got {len(actual)}")
            failures += 1

        all_clean = True
        for i, (a, e) in enumerate(zip(actual, expected), 1):
            text = visible_text(a)
            issues = stage_issues(e["expect_stage"], text)
            soft = e["expect_stage"].endswith("-preferred") or case.get("diagnostic", False)
            if issues:
                all_clean = False
                label = "WARN" if soft else "FAIL"
                print(f"{label} {cid}/{rid} turn {i}: " + "; ".join(issues))
                if soft:
                    warnings += 1
                else:
                    failures += 1

            tool_activity = a.get("tool_activity") or []
            if tool_activity and e["expect_stage"] not in {"execute", "execute-dependency"}:
                infos += 1
                print(
                    f"INFO {cid}/{rid} turn {i}: captured {len(tool_activity)} tool/activity event(s) before execution; "
                    "semantic judge must classify protocol loading vs substantive task work"
                )

        if all_clean and len(actual) == len(expected) and not run.get("notes"):
            print(f"PASS-SHAPE {cid}/{rid}")

    print(
        f"\nStructural lint complete: {failures} failure(s), {warnings} warning(s), {infos} tool-activity info notice(s)."
    )
    if failures:
        print("Passing this linter is necessary but not sufficient; run semantic judging too.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
