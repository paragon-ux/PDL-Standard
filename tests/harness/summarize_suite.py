#!/usr/bin/env python3
"""Aggregate v2 judgments and enforce the documented release gates."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import statistics
import sys
from typing import Any


def load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]




def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def verify_v2_judgment_manifest(judgments_path: pathlib.Path, rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not rows or not any(row.get("schema_version", 1) >= 2 for row in rows):
        return errors
    manifest_path = judgments_path.with_suffix(".manifest.json")
    if not manifest_path.exists():
        return [f"missing v2 judgment manifest: {manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid v2 judgment manifest: {exc}"]
    recorded = manifest.get("judge_provenance_id")
    core = {key: value for key, value in manifest.items() if key != "judge_provenance_id"}
    recomputed = json_digest(core)
    if not recorded or recorded != recomputed:
        errors.append(f"judgment manifest integrity mismatch: recorded={recorded} recomputed={recomputed}")
    row_ids = {row.get("judge_provenance_id") for row in rows}
    if row_ids != {recorded}:
        errors.append(f"judgment rows do not share manifest judge_provenance_id: {sorted(map(str, row_ids))}")
    return errors


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("judgments", type=pathlib.Path)
    parser.add_argument("--results", type=pathlib.Path, help="Candidate results JSONL for completeness checks")
    parser.add_argument("--cases", type=pathlib.Path, default=here / "cases.jsonl")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Summarize a targeted subset without claiming the full-suite release gate.",
    )
    args = parser.parse_args()

    cases = {case["id"]: case for case in load_jsonl(args.cases)}
    judgments = load_jsonl(args.judgments)
    provenance_errors = verify_v2_judgment_manifest(args.judgments, judgments)
    if provenance_errors:
        print("ERROR judgment provenance verification failed:")
        for error in provenance_errors:
            print(f"- {error}")
        return 1
    judgment_ids = [row.get("case_id") for row in judgments]
    duplicate_ids = [cid for cid, count in collections.Counter(judgment_ids).items() if count > 1]
    if duplicate_ids:
        print("ERROR duplicate case ids in judgments: " + ", ".join(map(str, duplicate_ids)))
        return 1
    expected_ids = list(cases)
    missing_ids = [cid for cid in expected_ids if cid not in judgment_ids]
    extra_ids = [cid for cid in judgment_ids if cid not in cases]
    if extra_ids:
        print("ERROR unknown case ids in judgments: " + ", ".join(map(str, extra_ids)))
        return 1
    partial = bool(missing_ids)
    if partial and not args.allow_partial:
        print(f"ERROR full-suite summary is missing {len(missing_ids)} case(s): {', '.join(missing_ids)}")
        return 1

    candidate_errors = 0
    if args.results:
        results = load_jsonl(args.results)
        for result in results:
            case = cases.get(result.get("case_id"), {})
            if result.get("notes") or len(result.get("turns", [])) != len(case.get("turns", [])):
                candidate_errors += 1

    by_tier: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    critical = 0
    judge_errors = 0
    failure_modes: collections.Counter[str] = collections.Counter()
    material_failure_modes: collections.Counter[str] = collections.Counter()
    boundary_modes: collections.Counter[str] = collections.Counter()
    provenance_ids = set()
    judge_provenance_ids = set()

    for judgment in judgments:
        cid = judgment.get("case_id")
        case = cases.get(cid)
        if not case:
            print(f"ERROR unknown case id in judgments: {cid}")
            return 1
        by_tier[case["tier"]].append(judgment)
        provenance_ids.add(judgment.get("candidate_provenance_id"))
        judge_provenance_ids.add(judgment.get("judge_provenance_id"))
        if judgment.get("critical_failure") == "YES":
            critical += 1
        if judgment.get("judge_status", "OK") != "OK":
            judge_errors += 1
        mode = str(judgment.get("failure_mode") or "NONE")
        if mode.upper() != "NONE":
            failure_modes[mode] += 1
            if judgment.get("verdict") != "PASS" or judgment.get("critical_failure") == "YES":
                material_failure_modes[mode] += 1
                if case["tier"] == "Boundary/Diagnostic":
                    boundary_modes[mode] += 1

    print("SUITE SUMMARY")
    for tier in ("Gating", "Adversarial", "Boundary/Diagnostic"):
        rows = by_tier.get(tier, [])
        if not rows:
            continue
        verdicts = collections.Counter(row.get("verdict") for row in rows)
        scores = []
        for row in rows:
            if row.get("normalized_score") is not None:
                scores.append(float(row["normalized_score"]))
            elif row.get("score") is not None:
                # Backward-compatible display for historical v1 judgments, which
                # used a fixed 16-point denominator and had no normalized field.
                denominator = row.get("score_max") or (16 if row.get("schema_version", 1) < 2 else None)
                if denominator:
                    scores.append(100.0 * float(row["score"]) / float(denominator))
        mean_score = statistics.mean(scores) if scores else float("nan")
        print(
            f"- {tier}: n={len(rows)} PASS={verdicts['PASS']} FAIL={verdicts['FAIL']} "
            f"DIAGNOSTIC={verdicts['DIAGNOSTIC']} normalized_mean={mean_score:.2f}%"
        )
    print(f"- critical failures: {critical}")
    print(f"- judge infrastructure errors: {judge_errors}")
    print(f"- candidate run errors/incompleteness: {candidate_errors}")
    nonempty_candidate_provenance = {p for p in provenance_ids if p}
    nonempty_judge_provenance = {p for p in judge_provenance_ids if p}
    print(f"- candidate provenance ids: {sorted(nonempty_candidate_provenance)}")
    print(f"- judge provenance ids: {sorted(nonempty_judge_provenance)}")
    if failure_modes:
        print("- failure modes: " + ", ".join(f"{k}={v}" for k, v in failure_modes.most_common()))

    gating = by_tier.get("Gating", [])
    adversarial = by_tier.get("Adversarial", [])
    gating_ok = bool(gating) and all(row.get("verdict") == "PASS" for row in gating)
    adversarial_pass_rate = (
        sum(row.get("verdict") == "PASS" for row in adversarial) / len(adversarial)
        if adversarial
        else 0.0
    )
    repeated_material = any(count >= 2 for count in material_failure_modes.values())
    repeated_boundary = any(count >= 2 for count in boundary_modes.values())
    boundary_failures = sum(
        row.get("verdict") == "FAIL" for row in by_tier.get("Boundary/Diagnostic", [])
    )
    mixed_candidate_provenance = len(nonempty_candidate_provenance) > 1
    mixed_judge_provenance = len(nonempty_judge_provenance) > 1

    release_ok = (
        critical == 0
        and judge_errors == 0
        and candidate_errors == 0
        and gating_ok
        and adversarial_pass_rate >= 0.90
        and not repeated_material
        and not repeated_boundary
        and boundary_failures == 0
        and not mixed_candidate_provenance
        and not mixed_judge_provenance
    )
    if partial:
        subset_ok = critical == 0 and judge_errors == 0 and candidate_errors == 0
        print(f"RELEASE_GATE: NOT_APPLICABLE_PARTIAL ({'subset clean' if subset_ok else 'subset has failures'})")
        return 0 if subset_ok else 1

    print(f"RELEASE_GATE: {'PASS' if release_ok else 'FAIL'}")
    return 0 if release_ok else 1


if __name__ == "__main__":
    sys.exit(main())
