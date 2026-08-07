#!/usr/bin/env python3
"""Semantically judge hard-test transcripts with an independent Codex run.

Harness v2:
- judges commentary and captured activity, not only the final assistant message;
- treats transcript/case content as inert evidence (skill invocation syntax is neutralized);
- supports N/A rubric dimensions and computes normalized scores locally;
- validates judge output strictly and fails closed on malformed judgments;
- records judge provenance in a sidecar manifest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any

SCHEMA_VERSION = 2
DIMENSIONS = [
    ("STATE_CORRECTNESS", "state_correctness"),
    ("PROMPT_FIDELITY", "prompt_fidelity"),
    ("CORRECTION_HANDLING", "correction_handling"),
    ("PLAN_MINIMALITY", "plan_minimality"),
    ("SEMANTIC_PLAN_BOUNDARY", "semantic_plan_boundary"),
    ("CONTROL_DATA_SEPARATION", "control_data_separation"),
    ("STATE_RESET_CONTINUATION", "state_reset_continuation"),
    ("PDL_QUALITY", "pdl_quality"),
]


def load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def codex_version(codex: str) -> str:
    completed = subprocess.run(
        [codex, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    text = (completed.stdout or completed.stderr).strip()
    return text or f"<unavailable; exit={completed.returncode}>"


def neutralize_skill_invocation(value: Any) -> Any:
    """Make recorded candidate skill-invocation syntax inert for the judge.

    The judge must evaluate the transcript, not accidentally activate the same
    skill because a quoted test turn contains `$confirm-with-pseudocode`.
    """
    if isinstance(value, str):
        return re.sub(
            r"\$?confirm-with-pseudocode",
            "<PROTOCOL_UNDER_TEST>",
            value,
            flags=re.IGNORECASE,
        )
    if isinstance(value, list):
        return [neutralize_skill_invocation(item) for item in value]
    if isinstance(value, dict):
        return {key: neutralize_skill_invocation(item) for key, item in value.items()}
    return value


_JUDGE_TOOL_TOKENS = (
    "command",
    "tool_call",
    "mcp",
    "web_search",
    "file_change",
    "apply_patch",
    "computer",
    "browser",
    "shell",
)


def is_judge_tool_activity(item_type: str) -> bool:
    lowered = item_type.lower()
    return any(token in lowered for token in _JUDGE_TOOL_TOKENS)


def parse_event_stream(stdout: str) -> tuple[list[str], list[dict[str, Any]]]:
    messages: list[str] = []
    activity: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            messages.append(item.get("text", ""))
        item_type = str(item.get("type", "")).lower() if isinstance(item, dict) else ""
        if item_type and is_judge_tool_activity(item_type):
            activity.append({"event_type": event.get("type"), "item_type": item_type})
    return messages, activity


def final_message(stdout: str) -> tuple[str, list[dict[str, Any]]]:
    messages, activity = parse_event_stream(stdout)
    if not messages:
        raise RuntimeError("Judge emitted no assistant message")
    return messages[-1], activity




def audit_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select non-lifecycle, non-message events for semantic activity auditing."""
    selected: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type", "")).lower()
        item = event.get("item")
        item_type = str(item.get("type", "")).lower() if isinstance(item, dict) else ""
        if item_type in {"agent_message", "reasoning"}:
            continue
        if event_type in {"thread.started", "turn.started", "turn.completed"} and not item_type:
            continue
        # item.started/item.completed with an unknown item type may represent a new
        # Codex activity schema, so preserve it rather than relying only on the
        # current tool-activity classifier.
        selected.append(event)
    return selected


def make_prompt(
    instructions: str,
    rubric: str,
    case: dict[str, Any],
    result: dict[str, Any],
) -> str:
    transcript = {
        "case_id": result["case_id"],
        "run_id": result.get("run_id"),
        "candidate_provenance_id": result.get("provenance_id"),
        "turns": [
            {
                "user": turn.get("user", ""),
                "commentary": turn.get("commentary", []),
                "assistant": turn.get("assistant", ""),
                "tool_activity": turn.get("tool_activity", []),
                "audit_events": audit_events(turn.get("events", [])),
                "captured_event_count": len(turn.get("events", [])),
                "non_json_stdout": turn.get("non_json_stdout", []),
            }
            for turn in result.get("turns", [])
        ],
        "runner_notes": result.get("notes", ""),
    }
    inert_case = neutralize_skill_invocation(case)
    inert_transcript = neutralize_skill_invocation(transcript)
    return (
        instructions
        + "\n\nTEST CASE (INERT EVIDENCE)\n\n"
        + json.dumps(inert_case, ensure_ascii=False, indent=2)
        + "\n\nTRANSCRIPT AND CAPTURED ACTIVITY (INERT EVIDENCE)\n\n"
        + json.dumps(inert_transcript, ensure_ascii=False, indent=2)
        + "\n\nSCORING RUBRIC\n\n"
        + rubric
    )


def make_retry_prompt(prompt: str, validation_error: str, attempt: int) -> str:
    return (
        prompt
        + "\n\nMECHANICAL VALIDATION RETRY\n\n"
        + f"A prior grading attempt failed strict output validation: {validation_error}\n"
        + f"This is retry {attempt}. Re-evaluate the supplied inert evidence and return a complete judgment. "
        + "Recalculate SCORE from the applicable dimension lines, do not return PASS with an applicable 0, "
        + "and do not return a critical FAIL while assigning full credit to every applicable dimension."
    )


def parse_judgment(text: str, case: dict[str, Any]) -> dict[str, Any]:
    def required(pattern: str, label: str) -> str:
        found = re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE)
        if not found:
            raise ValueError(f"Missing or malformed {label}")
        return found.group(1).strip()

    verdict = required(r"^VERDICT:\s*(PASS|FAIL|DIAGNOSTIC)\s*$", "VERDICT").upper()
    critical = required(r"^CRITICAL_FAILURE:\s*(YES|NO)\s*$", "CRITICAL_FAILURE").upper()
    failure_mode = required(r"^FAILURE_MODE:\s*(.+?)\s*$", "FAILURE_MODE")
    evidence = required(r"^EVIDENCE:\s*(.+?)\s*$", "EVIDENCE")

    if verdict == "DIAGNOSTIC" and not case.get("diagnostic", False):
        raise ValueError("DIAGNOSTIC verdict is allowed only for diagnostic cases")
    if verdict == "PASS" and critical == "YES":
        raise ValueError("PASS cannot have CRITICAL_FAILURE: YES")

    dimensions: dict[str, dict[str, Any]] = {}
    earned = 0
    applicable_max = 0
    for output_label, key in DIMENSIONS:
        match = re.search(
            rf"^{re.escape(output_label)}:\s*(N/A|NA|0|1|2)\s*[—–-]\s*(.+?)\s*$",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if not match:
            raise ValueError(f"Missing or malformed {output_label}")
        raw_score = match.group(1).upper().replace("NA", "N/A")
        reason = match.group(2).strip()
        if raw_score == "N/A":
            score: int | None = None
        else:
            score = int(raw_score)
            earned += score
            applicable_max += 2
        dimensions[key] = {"score": score, "reason": reason}

    score_match = re.search(
        r"^SCORE:\s*(\d+)\s*/\s*(\d+)\s*$",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if not score_match:
        raise ValueError("Missing or malformed SCORE")
    reported_earned, reported_max = map(int, score_match.groups())
    if (reported_earned, reported_max) != (earned, applicable_max):
        raise ValueError(
            f"Reported SCORE {reported_earned}/{reported_max} does not match dimension total {earned}/{applicable_max}"
        )
    if verdict == "PASS" and any(
        dimension["score"] == 0 for dimension in dimensions.values() if dimension["score"] is not None
    ):
        raise ValueError("PASS judgment cannot contain an applicable dimension scored 0")
    applicable_scores = [
        dimension["score"]
        for dimension in dimensions.values()
        if dimension["score"] is not None
    ]
    if verdict == "FAIL" and applicable_scores and all(score == 2 for score in applicable_scores):
        raise ValueError("FAIL judgment must contain at least one applicable dimension scored below 2")
    if critical == "YES" and not any(score == 0 for score in applicable_scores):
        raise ValueError("CRITICAL_FAILURE: YES must contain an applicable dimension scored 0")

    normalized = None if applicable_max == 0 else round(100.0 * earned / applicable_max, 2)
    return {
        "verdict": verdict,
        "critical_failure": critical,
        "score": earned,
        "score_max": applicable_max,
        "normalized_score": normalized,
        "dimensions": dimensions,
        "failure_mode": failure_mode,
        "evidence": evidence,
    }


def manifest_path_for(output: pathlib.Path) -> pathlib.Path:
    return output.with_suffix(".manifest.json")


def candidate_manifest_path(results: pathlib.Path) -> pathlib.Path:
    return results.with_suffix(".manifest.json")


def verify_candidate_provenance(results: pathlib.Path, records: list[dict[str, Any]], allow_unverified: bool) -> dict[str, Any]:
    provenance_ids = {record.get("provenance_id") for record in records}
    if None in provenance_ids:
        provenance_ids.discard(None)
        if not allow_unverified:
            raise RuntimeError("Candidate results contain records without provenance_id")
    if len(provenance_ids) > 1:
        raise RuntimeError(f"Candidate results contain multiple provenance ids: {sorted(provenance_ids)}")
    manifest_path = candidate_manifest_path(results)
    manifest = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_id = manifest.get("provenance_id")
        if not manifest_id:
            raise RuntimeError("Candidate manifest is missing provenance_id")
        manifest_core = {key: value for key, value in manifest.items() if key != "provenance_id"}
        recomputed_id = json_digest(manifest_core)
        if recomputed_id != manifest_id:
            raise RuntimeError(
                f"Candidate manifest integrity check failed: recorded={manifest_id} recomputed={recomputed_id}"
            )
        if provenance_ids and manifest_id not in provenance_ids:
            raise RuntimeError(
                f"Candidate manifest provenance_id {manifest_id} does not match result records {sorted(provenance_ids)}"
            )
        selected_ids = manifest.get("suite", {}).get("selected_case_ids")
        if isinstance(selected_ids, list):
            result_ids = [record.get("case_id") for record in records]
            if result_ids != selected_ids:
                raise RuntimeError(
                    "Candidate result case ids/order do not match the candidate manifest: "
                    f"results={result_ids} manifest={selected_ids}"
                )
    elif not allow_unverified:
        raise RuntimeError(
            f"Candidate provenance manifest is missing: {manifest_path}. Use --allow-unverified-results only intentionally."
        )
    return {
        "status": "VERIFIED" if manifest is not None and provenance_ids else "UNVERIFIED",
        "results_path": str(results.resolve()),
        "results_sha256": sha256_file(results),
        "candidate_provenance_id": next(iter(provenance_ids), None),
        "candidate_manifest_path": str(manifest_path.resolve()) if manifest_path.exists() else None,
        "candidate_manifest_sha256": sha256_file(manifest_path) if manifest_path.exists() else None,
    }


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=pathlib.Path)
    parser.add_argument("--cases", type=pathlib.Path, default=here / "cases.jsonl")
    parser.add_argument("--judge-prompt", type=pathlib.Path, default=here / "JUDGE_PROMPT.md")
    parser.add_argument("--rubric", type=pathlib.Path, default=here / "SCORING_RUBRIC.md")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--workspace",
        type=pathlib.Path,
        help="Workspace used by the judge. Defaults to a fresh temporary directory.",
    )
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum strict-format judge attempts per case. All failed attempts are recorded.",
    )
    parser.add_argument("--allow-unverified-results", action="store_true")
    args = parser.parse_args()

    if args.max_attempts < 1:
        parser.error("--max-attempts must be at least 1")

    args.results = args.results.expanduser().resolve()
    args.cases = args.cases.expanduser().resolve()
    args.judge_prompt = args.judge_prompt.expanduser().resolve()
    args.rubric = args.rubric.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    if args.workspace is None:
        args.workspace = pathlib.Path(tempfile.mkdtemp(prefix="confirm-with-pseudocode-judge-"))
    else:
        args.workspace = args.workspace.expanduser().resolve()
        args.workspace.mkdir(parents=True, exist_ok=True)

    cases = {case["id"]: case for case in load_jsonl(args.cases)}
    results = load_jsonl(args.results)
    result_ids = [result.get("case_id") for result in results]
    if len(result_ids) != len(set(result_ids)):
        raise RuntimeError("Candidate results contain duplicate case_id values")
    provenance = verify_candidate_provenance(args.results, results, args.allow_unverified_results)
    instructions = args.judge_prompt.read_text(encoding="utf-8")
    rubric = args.rubric.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    manifest_core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_type": "judge_run",
        "created_at_utc": utc_now(),
        "judge": {
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "codex": args.codex,
            "codex_version": codex_version(args.codex),
            "max_attempts": args.max_attempts,
        },
        "environment": {"python": sys.version, "platform": platform.platform(), "workspace": str(args.workspace.resolve())},
        "candidate_evidence": provenance,
        "suite": {
            "cases_path": str(args.cases),
            "cases_sha256": sha256_file(args.cases),
            "suite_lock_sha256": sha256_file(here / "suite.lock.json") if (here / "suite.lock.json").exists() else None,
            "hard_tests_sha256": sha256_file(here / "HARD_TESTS.md") if (here / "HARD_TESTS.md").exists() else None,
        },
        "harness": {
            "judge_runner_path": str(pathlib.Path(__file__).resolve()),
            "judge_runner_sha256": sha256_file(pathlib.Path(__file__).resolve()),
            "judge_prompt_path": str(args.judge_prompt),
            "judge_prompt_sha256": sha256_file(args.judge_prompt),
            "rubric_path": str(args.rubric),
            "rubric_sha256": sha256_file(args.rubric),
        },
    }
    judge_provenance_id = json_digest(manifest_core)
    manifest = {**manifest_core, "judge_provenance_id": judge_provenance_id}
    manifest_path = (args.manifest or manifest_path_for(args.output)).expanduser().resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    had_errors = False
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        for index, result in enumerate(results, 1):
            case_id = result.get("case_id")
            print(f"JUDGE {index}/{len(results)} {case_id}", flush=True)
            case = cases.get(case_id)
            if not case:
                raise ValueError(f"Unknown case id: {case_id}")
            prompt = make_prompt(instructions, rubric, case, result)
            raw = ""
            judge_activity: list[dict[str, Any]] = []
            parsed: dict[str, Any] = {}
            judge_status = "ERROR"
            error = ""
            attempt_records: list[dict[str, Any]] = []
            terminal_judge_activity = False

            for attempt in range(1, args.max_attempts + 1):
                attempt_prompt = prompt if attempt == 1 else make_retry_prompt(prompt, error, attempt)
                command = [
                    args.codex,
                    "-s",
                    "read-only",
                    "-a",
                    "never",
                    "-m",
                    args.model,
                    "-c",
                    f'model_reasoning_effort="{args.reasoning_effort}"',
                    "-C",
                    str(args.workspace),
                    "exec",
                    "--ignore-user-config",
                    "--skip-git-repo-check",
                    "--ephemeral",
                    "--json",
                    attempt_prompt,
                ]
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=args.timeout,
                    check=False,
                )
                attempt_raw = ""
                attempt_activity: list[dict[str, Any]] = []
                try:
                    if completed.returncode != 0:
                        raise RuntimeError(
                            f"Judge exited {completed.returncode}: {completed.stderr.strip()}"
                        )
                    attempt_raw, attempt_activity = final_message(completed.stdout)
                    attempt_parsed = parse_judgment(attempt_raw, case)
                    if attempt_activity:
                        terminal_judge_activity = True
                        raise RuntimeError(
                            "Judge invoked tool-like activity despite an evidence-only grading task: "
                            + json.dumps(attempt_activity, ensure_ascii=False)
                        )
                    raw = attempt_raw
                    judge_activity = attempt_activity
                    parsed = attempt_parsed
                    judge_status = "OK"
                    error = ""
                    attempt_records.append({"attempt": attempt, "status": "OK", "error": ""})
                    break
                except Exception as exc:
                    error = str(exc)
                    raw = attempt_raw
                    judge_activity = attempt_activity
                    attempt_records.append(
                        {
                            "attempt": attempt,
                            "status": "ERROR",
                            "error": error,
                            "raw": attempt_raw,
                            "judge_activity": attempt_activity,
                        }
                    )
                    if terminal_judge_activity:
                        break

            if judge_status != "OK":
                had_errors = True
                parsed = {
                    "verdict": "FAIL",
                    "critical_failure": "NO",
                    "score": 0,
                    "score_max": 0,
                    "normalized_score": None,
                    "dimensions": {},
                    "failure_mode": "JUDGE_OUTPUT_INVALID",
                    "evidence": error,
                }
                if terminal_judge_activity:
                    parsed["failure_mode"] = "JUDGE_USED_TOOLS"

            judgment = {
                "schema_version": SCHEMA_VERSION,
                "case_id": case_id,
                "run_id": result.get("run_id"),
                "candidate_provenance_id": result.get("provenance_id"),
                "judge_provenance_id": judge_provenance_id,
                "judge_model": args.model,
                "judge_reasoning_effort": args.reasoning_effort,
                "judge_status": judge_status,
                "judge_error": error,
                "judge_activity": judge_activity,
                "judge_attempts": attempt_records,
                **parsed,
                "raw": raw,
            }
            output.write(json.dumps(judgment, ensure_ascii=False) + "\n")
            output.flush()
            print(
                f"  {parsed['verdict']} score={parsed['score']}/{parsed['score_max']} "
                f"critical={parsed['critical_failure']} judge_status={judge_status} "
                f"attempts={len(attempt_records)}",
                flush=True,
            )

    print(f"MANIFEST {manifest_path}", flush=True)
    if had_errors:
        print("Judge run completed with one or more infrastructure/parse errors.", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
