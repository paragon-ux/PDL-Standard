#!/usr/bin/env python3
"""Validate the public bundle without machine-specific paths or dependencies."""

from __future__ import annotations

import json
import hashlib
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC_ENTRIES = (
    ".github",
    ".gitattributes",
    ".gitignore",
    "INSTALLATION.md",
    "LICENSE",
    "NOTICE.md",
    "README.md",
    "runtime-manifest.json",
    "confirm-with-pseudocode",
    "docs/architecture",
    "docs/evaluation",
    "examples",
    "scripts",
    "tests/harness",
)
REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    ".gitattributes",
    "README.md",
    "INSTALLATION.md",
    "LICENSE",
    "NOTICE.md",
    "runtime-manifest.json",
    "scripts/verify_runtime_manifest.py",
    "confirm-with-pseudocode/SKILL.md",
    "confirm-with-pseudocode/agents/openai.yaml",
    "confirm-with-pseudocode/references/pdl-conventions.md",
    "docs/evaluation/methodology.md",
    "docs/evaluation/external-review.md",
    "docs/evaluation/current-targeted-run.md",
    "docs/evaluation/current-targeted-run.json",
    "docs/evaluation/results.md",
    "docs/architecture/pdl-rationale.md",
    "docs/architecture/adr/0007-contract-governed-context-projected-runtime.md",
    "docs/architecture/trd/README.md",
    "docs/architecture/trd/0002-contract-substrate-and-mechanical-verification.md",
    "tests/harness/suite.lock.json",
)
TEXT_SUFFIXES = {"", ".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}
DOCUMENT_SUFFIXES = {"", ".json", ".jsonl", ".md", ".txt", ".yaml", ".yml"}
USER_HOME_PATTERN = re.compile(
    r"(?i)(?:[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]|/(?:Users|home)/[^/\s]+/)"
)
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:\\")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def public_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for entry in PUBLIC_ENTRIES:
        path = ROOT / entry
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return sorted(set(files))


def check_required(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required public file: {relative}")


def check_skill(errors: list[str]) -> None:
    path = ROOT / "confirm-with-pseudocode" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append("confirm-with-pseudocode/SKILL.md: missing YAML frontmatter")
        return
    try:
        frontmatter = text.split("---", 2)[1]
    except IndexError:
        errors.append("confirm-with-pseudocode/SKILL.md: unterminated YAML frontmatter")
        return
    if not re.search(r"(?m)^name:\s*confirm-with-pseudocode\s*$", frontmatter):
        errors.append("confirm-with-pseudocode/SKILL.md: unexpected or missing name")
    if not re.search(r"(?m)^description:\s*(?:>|[^\s].*)$", frontmatter):
        errors.append("confirm-with-pseudocode/SKILL.md: missing description")


def check_paths(files: list[pathlib.Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(ROOT).as_posix()
        if USER_HOME_PATTERN.search(text):
            errors.append(f"{relative}: contains a user-home absolute path")
        if path.suffix.lower() in DOCUMENT_SUFFIXES and WINDOWS_ABSOLUTE_PATTERN.search(text):
            errors.append(f"{relative}: contains a Windows absolute path")


def check_links(files: list[pathlib.Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for target in MARKDOWN_LINK_PATTERN.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "#", "<")):
                continue
            candidate = (path.parent / target).resolve()
            if not candidate.exists():
                relative = path.relative_to(ROOT).as_posix()
                errors.append(f"{relative}: broken relative link -> {target}")


def check_suite(errors: list[str]) -> None:
    path = ROOT / "tests" / "harness" / "suite.lock.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("behavioral_suite_version") != "1.1":
        errors.append("tests/harness/suite.lock.json: expected behavioral suite 1.1")
    if value.get("cases", {}).get("count") != 40:
        errors.append("tests/harness/suite.lock.json: expected 40 cases")


def directory_digest(path: pathlib.Path) -> str:
    files: list[dict[str, object]] = []
    for item in sorted((entry for entry in path.rglob("*") if entry.is_file()), key=lambda entry: entry.as_posix()):
        relative = item.relative_to(path)
        if any(part in {"__pycache__", ".git"} for part in relative.parts):
            continue
        if item.name in {".DS_Store", "Thumbs.db", "desktop.ini"} or item.suffix == ".pyc":
            continue
        data = item.read_bytes()
        files.append(
            {
                "path": relative.as_posix(),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    payload = "\n".join(
        f"{entry['path']}\0{entry['size']}\0{entry['sha256']}" for entry in files
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def check_current_evidence(errors: list[str]) -> None:
    path = ROOT / "docs" / "evaluation" / "current-targeted-run.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    cases = value.get("cases", [])
    expected_ids = {
        "A05", "A06", "A07", "A11", "A12", "A13", "A14", "A15",
        "A17", "A18", "A19", "A20", "B06", "B08", "B09",
    }
    ids = {case.get("id") for case in cases}
    if len(cases) != 15 or ids != expected_ids:
        errors.append("current targeted evidence: unexpected selected-case set")
    if any(case.get("verdict") != "PASS" or case.get("critical_failure") for case in cases):
        errors.append("current targeted evidence: expected 15 PASS results and no critical failures")

    earned = 0
    maximum = 0
    for case in cases:
        dimensions = case.get("dimensions", {})
        scores = [score for score in dimensions.values() if score is not None]
        case_earned = sum(scores)
        case_maximum = 2 * len(scores)
        if case.get("score") != case_earned or case.get("score_max") != case_maximum:
            errors.append(f"current targeted evidence: score mismatch for {case.get('id')}")
        earned += case_earned
        maximum += case_maximum
    if (earned, maximum) != (109, 110):
        errors.append(f"current targeted evidence: expected 109/110, found {earned}/{maximum}")

    skill_digest = directory_digest(ROOT / "confirm-with-pseudocode")
    if value.get("skill_directory_sha256") != skill_digest:
        errors.append("current targeted evidence: skill digest does not match release bytes")


def main() -> int:
    errors: list[str] = []
    check_required(errors)
    files = public_files()
    check_skill(errors)
    check_paths(files, errors)
    check_links(files, errors)
    check_suite(errors)
    check_current_evidence(errors)
    if errors:
        print("BUNDLE VALIDATION FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("BUNDLE VALIDATION PASS")
    print(f"- public files checked: {len(files)}")
    print("- required files, architecture docs, and skill metadata present")
    print("- no user-home or documented Windows absolute paths")
    print("- relative Markdown links resolve")
    print("- behavioral suite 1.1 lock present with 40 cases")
    print("- current 15-case evidence reconciles to 109/110 and matches skill bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
