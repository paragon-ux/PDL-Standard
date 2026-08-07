#!/usr/bin/env python3
"""Run hard-test conversations against an installed Codex skill.

Harness v2 goals:
- keep candidate prompts test-neutral;
- bind a run to explicit source and installed skill bytes;
- record reproducibility metadata in a sidecar manifest;
- preserve all safe Codex JSON events needed to audit tool activity;
- redact hidden reasoning payloads;
- retain commentary separately from the final assistant message;
- fail non-zero on incomplete/errored runs.
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
SKILL_NAME = "confirm-with-pseudocode"


def load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def directory_manifest(path: pathlib.Path) -> dict[str, Any]:
    requested = path.expanduser().absolute()
    root = requested.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {requested}")
    files: list[dict[str, Any]] = []
    for item in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        rel_path = item.relative_to(root)
        rel = rel_path.as_posix()
        if any(part in {"__pycache__", ".git"} for part in rel_path.parts):
            continue
        if item.name in {".DS_Store", "Thumbs.db", "desktop.ini"} or item.suffix == ".pyc":
            continue
        data = item.read_bytes()
        files.append({"path": rel, "size": len(data), "sha256": sha256_bytes(data)})
    digest_payload = "\n".join(
        f"{entry['path']}\0{entry['size']}\0{entry['sha256']}" for entry in files
    ).encode("utf-8")
    return {
        "path": str(requested),
        "resolved_path": str(root),
        "sha256": sha256_bytes(digest_payload),
        "files": files,
    }


def json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


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


def sanitize_reasoning_payload(value: Any) -> Any:
    """Preserve event structure while removing hidden reasoning content.

    Visible agent messages are retained elsewhere. Codex event streams may contain
    reasoning items; those are useful only as activity markers for this harness, not
    as content, so their payload is deliberately redacted before writing to disk.
    """
    if isinstance(value, list):
        return [sanitize_reasoning_payload(item) for item in value]
    if not isinstance(value, dict):
        return value

    type_value = str(value.get("type", "")).lower()
    item_type = ""
    if isinstance(value.get("item"), dict):
        item_type = str(value["item"].get("type", "")).lower()

    if "reasoning" in type_value or "reasoning" in item_type:
        safe: dict[str, Any] = {}
        for key in ("type", "id", "status", "thread_id", "turn_id"):
            if key in value:
                safe[key] = value[key]
        if isinstance(value.get("item"), dict):
            item = value["item"]
            safe["item"] = {
                key: item[key]
                for key in ("type", "id", "status")
                if key in item
            }
        safe["reasoning_payload"] = "<redacted>"
        return safe

    return {key: sanitize_reasoning_payload(item) for key, item in value.items()}


_TOOL_TYPE_EXACT = {
    "command_execution",
    "shell_command",
    "tool_call",
    "mcp_tool_call",
    "web_search",
    "file_change",
    "apply_patch",
    "computer_action",
    "browser_action",
    "image_generation",
}
_TOOL_TYPE_TOKENS = (
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


def event_type_strings(event: dict[str, Any]) -> set[str]:
    types: set[str] = set()
    if event.get("type") is not None:
        types.add(str(event["type"]).lower())
    item = event.get("item")
    if isinstance(item, dict) and item.get("type") is not None:
        types.add(str(item["type"]).lower())
    return types


def is_tool_activity(event: dict[str, Any]) -> bool:
    for type_name in event_type_strings(event):
        if type_name in {"agent_message", "reasoning", "thread.started", "turn.started", "turn.completed"}:
            continue
        if type_name in _TOOL_TYPE_EXACT:
            return True
        if any(token in type_name for token in _TOOL_TYPE_TOKENS):
            return True
    return False


def parse_events(stdout: str) -> tuple[str | None, list[str], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    thread_id: str | None = None
    messages: list[str] = []
    events: list[dict[str, Any]] = []
    tool_activity: list[dict[str, Any]] = []
    non_json: list[dict[str, Any]] = []

    for line in stdout.splitlines():
        try:
            raw_event = json.loads(line)
        except json.JSONDecodeError:
            if line.strip():
                encoded = line.encode("utf-8", errors="replace")
                non_json.append({"length": len(line), "sha256": sha256_bytes(encoded)})
            continue
        if not isinstance(raw_event, dict):
            continue
        event = sanitize_reasoning_payload(raw_event)
        events.append(event)
        if raw_event.get("type") == "thread.started":
            thread_id = raw_event.get("thread_id") or thread_id
        item = raw_event.get("item") or {}
        if raw_event.get("type") == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            messages.append(item.get("text", ""))
        if is_tool_activity(event):
            tool_activity.append(event)
    return thread_id, messages, events, tool_activity, non_json


def candidate_prompt(turn: dict[str, Any]) -> str:
    """Return exactly the user test turn; never expose expected behavior to candidate."""
    return turn["user"]


def codex_base(args: argparse.Namespace) -> list[str]:
    return [
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
    ]


def run_turn(
    args: argparse.Namespace, prompt: str, thread_id: str | None
) -> tuple[str, list[str], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    command = codex_base(args)
    if thread_id:
        command.extend(
            [
                "resume",
                "--ignore-user-config",
                "--skip-git-repo-check",
                "--json",
                thread_id,
                prompt,
            ]
        )
    else:
        command.extend(
            [
                "--ignore-user-config",
                "--skip-git-repo-check",
                "--json",
                prompt,
            ]
        )

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=args.timeout,
        check=False,
    )
    parsed_thread, messages, events, tool_activity, non_json = parse_events(completed.stdout)
    active_thread = parsed_thread or thread_id
    if completed.returncode != 0:
        raise RuntimeError(
            f"Codex exited {completed.returncode}: {completed.stderr.strip()}\n"
            f"stdout: {completed.stdout[-4000:]}"
        )
    if not active_thread:
        raise RuntimeError("Codex did not emit a thread id")
    if not messages:
        raise RuntimeError(
            "Codex did not emit an assistant message; stderr: "
            + completed.stderr.strip()
        )
    return active_thread, messages, events, tool_activity, non_json, completed.stderr


def delete_session(args: argparse.Namespace, thread_id: str) -> None:
    completed = subprocess.run(
        [args.codex, "delete", "--force", thread_id],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        print(
            f"WARN could not delete session {thread_id}: {completed.stderr.strip()}",
            flush=True,
        )


def select_cases(cases: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = cases
    if args.ids:
        wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
        selected = [case for case in selected if case["id"] in wanted]
        missing = wanted - {case["id"] for case in selected}
        if missing:
            raise ValueError("Unknown case id(s): " + ", ".join(sorted(missing)))
    if args.tier:
        selected = [case for case in selected if case["tier"] == args.tier]
    return selected


def default_source_skill(here: pathlib.Path) -> pathlib.Path:
    return here.parent.parent / SKILL_NAME


def detect_installed_skill() -> pathlib.Path | None:
    candidates = [
        pathlib.Path.home() / ".agents" / "skills" / SKILL_NAME,
        pathlib.Path.home() / ".codex" / "skills" / SKILL_NAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def verify_skill_binding(source: pathlib.Path, installed: pathlib.Path | None, skip: bool) -> dict[str, Any]:
    source_manifest = directory_manifest(source)
    if skip:
        return {
            "status": "SKIPPED",
            "source": source_manifest,
            "installed": None if installed is None else directory_manifest(installed),
        }
    if installed is None:
        raise RuntimeError(
            "Could not locate the installed skill. Pass --installed-skill-path to the directory "
            "Codex resolves for $confirm-with-pseudocode, or use --skip-skill-verification only "
            "when you intentionally accept unbound results."
        )
    installed_manifest = directory_manifest(installed)
    if source_manifest["sha256"] != installed_manifest["sha256"]:
        source_files = {(f["path"], f["size"], f["sha256"]) for f in source_manifest["files"]}
        installed_files = {(f["path"], f["size"], f["sha256"]) for f in installed_manifest["files"]}
        only_source = sorted(source_files - installed_files)
        only_installed = sorted(installed_files - source_files)
        raise RuntimeError(
            "Installed skill bytes do not match the source skill under test.\n"
            f"source={source_manifest['path']} sha256={source_manifest['sha256']}\n"
            f"installed={installed_manifest['path']} sha256={installed_manifest['sha256']}\n"
            f"source-only entries={only_source[:8]}\ninstalled-only entries={only_installed[:8]}"
        )
    return {"status": "VERIFIED", "source": source_manifest, "installed": installed_manifest}


def manifest_path_for(output: pathlib.Path) -> pathlib.Path:
    return output.with_suffix(".manifest.json")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=pathlib.Path, default=here / "cases.jsonl")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--ids", help="Comma-separated case ids")
    parser.add_argument(
        "--tier", choices=["Gating", "Adversarial", "Boundary/Diagnostic"]
    )
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--workspace",
        type=pathlib.Path,
        help="Workspace used by Codex. Defaults to a run-specific temp directory.",
    )
    parser.add_argument("--skill-path", type=pathlib.Path, default=default_source_skill(here))
    parser.add_argument(
        "--installed-skill-path",
        type=pathlib.Path,
        help="Directory Codex resolves for $confirm-with-pseudocode. Auto-detects common locations.",
    )
    parser.add_argument(
        "--skip-skill-verification",
        action="store_true",
        help="Run without proving installed skill bytes match --skill-path. Manifest records SKIPPED.",
    )
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--keep-sessions", action="store_true")
    args = parser.parse_args()

    if args.workspace is None:
        safe_run_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.run_id).strip("-") or "run"
        args.workspace = pathlib.Path(
            tempfile.mkdtemp(prefix=f"confirm-with-pseudocode-{safe_run_id}-")
        )
    else:
        args.workspace = args.workspace.expanduser().resolve()
        args.workspace.mkdir(parents=True, exist_ok=True)

    args.skill_path = args.skill_path.expanduser().resolve()
    if args.installed_skill_path is None:
        args.installed_skill_path = detect_installed_skill()
    elif args.installed_skill_path:
        args.installed_skill_path = args.installed_skill_path.expanduser().resolve()

    cases_path = args.cases.expanduser().resolve()
    cases_all = load_jsonl(cases_path)
    cases = select_cases(cases_all, args)
    if not cases:
        parser.error("No cases selected")

    binding = verify_skill_binding(
        args.skill_path, args.installed_skill_path, args.skip_skill_verification
    )

    created_at = utc_now()
    manifest_core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_type": "candidate_run",
        "run_id": args.run_id,
        "created_at_utc": created_at,
        "candidate": {
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "codex": args.codex,
            "codex_version": codex_version(args.codex),
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "workspace": str(args.workspace.resolve()),
        },
        "suite": {
            "cases_path": str(cases_path),
            "cases_sha256": sha256_file(cases_path),
            "suite_lock_sha256": sha256_file(here / "suite.lock.json") if (here / "suite.lock.json").exists() else None,
            "hard_tests_sha256": sha256_file(here / "HARD_TESTS.md") if (here / "HARD_TESTS.md").exists() else None,
            "selected_case_ids": [case["id"] for case in cases],
            "selected_case_count": len(cases),
        },
        "skill_binding": binding,
        "harness": {
            "runner_path": str(pathlib.Path(__file__).resolve()),
            "runner_sha256": sha256_file(pathlib.Path(__file__).resolve()),
            "judge_prompt_sha256": sha256_file(here / "JUDGE_PROMPT.md") if (here / "JUDGE_PROMPT.md").exists() else None,
            "rubric_sha256": sha256_file(here / "SCORING_RUBRIC.md") if (here / "SCORING_RUBRIC.md").exists() else None,
            "linter_sha256": sha256_file(here / "transcript_lint.py") if (here / "transcript_lint.py").exists() else None,
        },
    }
    provenance_id = json_digest(manifest_core)
    manifest = {**manifest_core, "provenance_id": provenance_id}

    args.output = args.output.expanduser().resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = (args.manifest or manifest_path_for(args.output)).expanduser().resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    had_errors = False
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        for case_index, case in enumerate(cases, 1):
            print(
                f"CASE {case_index}/{len(cases)} {case['id']} {case['title']}",
                flush=True,
            )
            thread_id: str | None = None
            captured_turns: list[dict[str, Any]] = []
            case_error: str | None = None
            try:
                for turn_index, turn in enumerate(case["turns"], 1):
                    # Expected behavior is printed only to the human runner. It is never
                    # sent to the candidate model.
                    print(
                        f"  TURN {turn_index}/{len(case['turns'])} expected={turn['expect_stage']}",
                        flush=True,
                    )
                    thread_id, messages, events, tool_activity, non_json, stderr = run_turn(
                        args, candidate_prompt(turn), thread_id
                    )
                    captured_turns.append(
                        {
                            "user": turn["user"],
                            "assistant": messages[-1],
                            "commentary": messages[:-1],
                            "events": events,
                            "tool_activity": tool_activity,
                            "non_json_stdout": non_json,
                            "runner_stderr": stderr,
                        }
                    )
            except Exception as exc:  # Preserve partial transcripts for diagnosis.
                had_errors = True
                case_error = str(exc)
                print(f"  ERROR {case['id']}: {case_error}", flush=True)
            finally:
                if thread_id and not args.keep_sessions:
                    delete_session(args, thread_id)

            result = {
                "schema_version": SCHEMA_VERSION,
                "case_id": case["id"],
                "run_id": args.run_id,
                "provenance_id": provenance_id,
                "model": args.model,
                "reasoning_effort": args.reasoning_effort,
                "turns": captured_turns,
                "notes": case_error or "",
            }
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            output.flush()
            print(
                f"  RECORDED {case['id']} turns={len(captured_turns)}",
                flush=True,
            )

    print(f"MANIFEST {manifest_path}", flush=True)
    if had_errors:
        print("Candidate run completed with one or more case errors.", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
