#!/usr/bin/env python3
"""Offline integrity/preflight checks for the hard-test kit.

No Codex/API access is required. Run this before spending model time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any

REQUIRED_FILES = [
    "cases.jsonl",
    "HARD_TESTS.md",
    "JUDGE_PROMPT.md",
    "SCORING_RUBRIC.md",
    "run_codex_suite.py",
    "judge_codex_results.py",
    "transcript_lint.py",
    "summarize_suite.py",
    "harness_selftest.py",
    "results-template.jsonl",
    "suite.lock.json",
    "CODEX_RUN_PROMPT.md",
    "HARNESS_V2_CHANGELOG.md",
]
TIERS = {"Gating", "Adversarial", "Boundary/Diagnostic"}
STAGES = {
    "prompt",
    "prompt-preferred",
    "plan",
    "plan-preferred",
    "execute",
    "execute-dependency",
    "meta",
    "safety",
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number}: each row must be an object")
        rows.append(value)
    return rows


def validate_cases(path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        cases = load_jsonl(path)
    except Exception as exc:
        return [str(exc)]
    ids: set[str] = set()
    for index, case in enumerate(cases, 1):
        cid = case.get("id")
        where = f"case row {index} ({cid or '<missing id>'})"
        if not isinstance(cid, str) or not cid:
            errors.append(f"{where}: missing string id")
        elif cid in ids:
            errors.append(f"{where}: duplicate id {cid}")
        else:
            ids.add(cid)
        if case.get("tier") not in TIERS:
            errors.append(f"{where}: invalid tier {case.get('tier')!r}")
        if not isinstance(case.get("title"), str) or not case.get("title"):
            errors.append(f"{where}: missing title")
        if not isinstance(case.get("critical"), bool):
            errors.append(f"{where}: critical must be boolean")
        if not isinstance(case.get("purpose"), str) or not case.get("purpose"):
            errors.append(f"{where}: missing purpose")
        turns = case.get("turns")
        if not isinstance(turns, list) or not turns:
            errors.append(f"{where}: turns must be a non-empty list")
            continue
        for turn_index, turn in enumerate(turns, 1):
            twhere = f"{where} turn {turn_index}"
            if not isinstance(turn, dict):
                errors.append(f"{twhere}: turn must be an object")
                continue
            if not isinstance(turn.get("user"), str) or not turn.get("user"):
                errors.append(f"{twhere}: missing user text")
            if turn.get("expect_stage") not in STAGES:
                errors.append(f"{twhere}: invalid expect_stage {turn.get('expect_stage')!r}")
            for field in ("must", "must_not"):
                if not isinstance(turn.get(field), str) or not turn.get(field):
                    errors.append(f"{twhere}: missing {field}")
        if not isinstance(case.get("pass"), str) or not case.get("pass"):
            errors.append(f"{where}: missing pass criterion")
    return errors


def validate_lock(here: pathlib.Path, allow_case_drift: bool) -> list[str]:
    lock_path = here / "suite.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    cases_spec = lock["cases"]
    hard_spec = lock["hard_tests"]
    cases_path = here / cases_spec["path"]
    hard_path = here / hard_spec["path"]
    cases = load_jsonl(cases_path)
    ids = [case.get("id") for case in cases]
    drift: list[str] = []
    if sha256_file(cases_path) != cases_spec["sha256"]:
        drift.append("cases.jsonl sha256 differs from suite.lock.json")
    if len(cases) != cases_spec["count"]:
        drift.append(f"case count is {len(cases)}, expected {cases_spec['count']}")
    if ids != cases_spec["ids"]:
        drift.append("case ids/order differ from suite.lock.json")
    if sha256_file(hard_path) != hard_spec["sha256"]:
        drift.append("HARD_TESTS.md sha256 differs from suite.lock.json")
    if drift and not allow_case_drift:
        errors.extend(drift)
    elif drift:
        for item in drift:
            print(f"WARN case drift allowed: {item}")
    return errors


def validate_markdown_links(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in root.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for target in link_pattern.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "#", "<")):
                continue
            # Ignore Windows absolute paths documented as examples.
            if re.match(r"^[A-Za-z]:[\\/]", target):
                continue
            candidate = (md.parent / target).resolve()
            if not candidate.exists():
                errors.append(f"broken relative link in {md.relative_to(root)} -> {target}")
    return errors


def validate_scripts(here: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for name in (
        "run_codex_suite.py",
        "judge_codex_results.py",
        "transcript_lint.py",
        "summarize_suite.py",
        "harness_selftest.py",
        "preflight.py",
    ):
        path = here / name
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"{name}: {exc.msg} at line {exc.lineno}")
    return errors


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skill-path",
        type=pathlib.Path,
        default=here.parent.parent / "confirm-with-pseudocode",
        help="Source skill directory expected to be tested.",
    )
    parser.add_argument(
        "--link-root",
        type=pathlib.Path,
        default=here,
        help="Root within which harness-relative Markdown links are checked.",
    )
    parser.add_argument("--allow-case-drift", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (here / name).exists():
            errors.append(f"missing required file: {name}")
    skill = args.skill_path.expanduser().resolve()
    if not (skill / "SKILL.md").is_file():
        errors.append(f"skill SKILL.md not found under {skill}")
    if not (skill / "references" / "pdl-conventions.md").is_file():
        errors.append(f"skill PDL reference not found under {skill / 'references'}")

    if not errors:
        errors.extend(validate_cases(here / "cases.jsonl"))
        errors.extend(validate_lock(here, args.allow_case_drift))
        errors.extend(validate_scripts(here))
        errors.extend(validate_markdown_links(args.link_root.expanduser().resolve()))

    if errors:
        print("PREFLIGHT FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PREFLIGHT PASS")
    print("- behavioral suite lock verified")
    print("- case schema verified")
    print("- Python scripts compile")
    print("- relative Markdown links resolve")
    print(f"- source skill found: {skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
