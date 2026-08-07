#!/usr/bin/env python3
"""Offline unit-style smoke tests for harness v2 internals."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.dont_write_bytecode = True

import judge_codex_results as judge
import run_codex_suite as runner
import transcript_lint as linter


def event_line(value):
    return json.dumps(value, ensure_ascii=False)


def test_runner_event_capture() -> None:
    stdout = "\n".join(
        [
            event_line({"type": "thread.started", "thread_id": "t-1"}),
            event_line({"type": "item.completed", "item": {"type": "agent_message", "text": "commentary"}}),
            event_line({"type": "item.completed", "item": {"type": "reasoning", "text": "SECRET_CHAIN_OF_THOUGHT"}}),
            event_line({"type": "item.completed", "item": {"type": "command_execution", "command": "echo safe"}}),
            event_line({"type": "item.completed", "item": {"type": "agent_message", "text": "final"}}),
            "non-json diagnostic",
        ]
    )
    thread, messages, events, activity, non_json = runner.parse_events(stdout)
    assert thread == "t-1"
    assert messages == ["commentary", "final"]
    serialized = json.dumps(events)
    assert "SECRET_CHAIN_OF_THOUGHT" not in serialized
    assert "<redacted>" in serialized
    assert len(activity) == 1
    assert len(non_json) == 1 and non_json[0]["length"] == len("non-json diagnostic")


def test_directory_binding() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        a = root / "a"
        b = root / "b"
        a.mkdir(); b.mkdir()
        (a / "SKILL.md").write_text("same", encoding="utf-8")
        (b / "SKILL.md").write_text("same", encoding="utf-8")
        assert runner.directory_manifest(a)["sha256"] == runner.directory_manifest(b)["sha256"]
        (b / "SKILL.md").write_text("different", encoding="utf-8")
        assert runner.directory_manifest(a)["sha256"] != runner.directory_manifest(b)["sha256"]


def valid_judgment() -> str:
    return """VERDICT: PASS
CRITICAL_FAILURE: NO
SCORE: 6/6

STATE_CORRECTNESS: 2 — correct state
PROMPT_FIDELITY: 2 — faithful
CORRECTION_HANDLING: N/A — no correction
PLAN_MINIMALITY: N/A — no plan
SEMANTIC_PLAN_BOUNDARY: N/A — not exercised
CONTROL_DATA_SEPARATION: N/A — not exercised
STATE_RESET_CONTINUATION: N/A — not exercised
PDL_QUALITY: 2 — valid PDL

FAILURE_MODE: NONE
EVIDENCE: Prompt stage was preserved.
"""


def test_judge_parser_and_na() -> None:
    case = {"diagnostic": False}
    parsed = judge.parse_judgment(valid_judgment(), case)
    assert parsed["verdict"] == "PASS"
    assert parsed["score"] == 6
    assert parsed["score_max"] == 6
    assert parsed["normalized_score"] == 100.0
    assert parsed["dimensions"]["correction_handling"]["score"] is None

    bad = valid_judgment().replace("SCORE: 6/6", "SCORE: 16/16")
    try:
        judge.parse_judgment(bad, case)
    except ValueError:
        pass
    else:
        raise AssertionError("score mismatch did not fail closed")

    inconsistent = valid_judgment().replace("VERDICT: PASS", "VERDICT: FAIL").replace(
        "CRITICAL_FAILURE: NO", "CRITICAL_FAILURE: YES"
    )
    try:
        judge.parse_judgment(inconsistent, case)
    except ValueError:
        pass
    else:
        raise AssertionError("critical FAIL with full dimension credit did not fail closed")


def test_judge_neutralization() -> None:
    value = {"user": "Use $confirm-with-pseudocode now"}
    neutral = judge.neutralize_skill_invocation(value)
    assert "$confirm-with-pseudocode" not in neutral["user"]
    assert "PROTOCOL_UNDER_TEST" in neutral["user"]


def test_linter_includes_commentary() -> None:
    turn = {
        "commentary": ["**Response Plan Pseudocode**\n```text\nPLAN\n```"],
        "assistant": "**Prompt Pseudocode**\n```text\nPROMPT\n```",
    }
    text = linter.visible_text(turn)
    issues = linter.stage_issues("prompt", text)
    assert any("Response Plan" in issue for issue in issues)




def test_candidate_prompt_is_test_neutral() -> None:
    turn = {
        "user": "Only this reaches the candidate",
        "expect_stage": "prompt",
        "must": "secret expected behavior",
        "must_not": "secret prohibition",
    }
    assert runner.candidate_prompt(turn) == "Only this reaches the candidate"


def test_judge_prompt_contains_no_skill_invocation_token() -> None:
    instructions = "Evaluate the protocol."
    rubric = "Rubric."
    case = {"id": "X", "user": "Use $confirm-with-pseudocode", "diagnostic": False}
    result = {
        "case_id": "X",
        "run_id": "r",
        "provenance_id": "p",
        "turns": [{"user": "Use $confirm-with-pseudocode", "assistant": "confirm-with-pseudocode", "commentary": []}],
        "notes": "",
    }
    prompt = judge.make_prompt(instructions, rubric, case, result)
    assert "$confirm-with-pseudocode" not in prompt.lower()
    assert "<PROTOCOL_UNDER_TEST>" in prompt


def test_judge_retry_prompt() -> None:
    retry = judge.make_retry_prompt("base evidence", "score mismatch", 2)
    assert "base evidence" in retry
    assert "score mismatch" in retry
    assert "retry 2" in retry
    assert "Recalculate SCORE" in retry


def main() -> int:
    tests = [
        test_runner_event_capture,
        test_directory_binding,
        test_judge_parser_and_na,
        test_judge_neutralization,
        test_linter_includes_commentary,
        test_candidate_prompt_is_test_neutral,
        test_judge_prompt_contains_no_skill_invocation_token,
        test_judge_retry_prompt,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"HARNESS SELFTEST PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
