#!/usr/bin/env python3
"""Deterministically verify the installed confirm-with-pseudocode package.

This verifier intentionally checks only mechanical package invariants declared
in runtime-manifest.json. It does not evaluate prompt semantics, plan quality,
or execution conformance.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
from dataclasses import dataclass, asdict
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = SCRIPT_ROOT / "runtime-manifest.json"
HEX40 = set("0123456789abcdef")


@dataclass(frozen=True)
class CheckResult:
    check: str
    status: str
    subject: str
    expected: Any = None
    observed: Any = None
    detail: str | None = None


class ManifestError(ValueError):
    pass


def git_blob_sha1(path: pathlib.Path, normalization: str = "none") -> str:
    data = path.read_bytes()
    if normalization == "crlf_to_lf":
        data = data.replace(b"\r\n", b"\n")
    elif normalization != "none":
        raise ManifestError(f"unsupported digest normalization: {normalization}")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest is not valid JSON: {exc}") from exc

    if value.get("manifest_version") != "1.0":
        raise ManifestError("manifest_version must be '1.0'")

    package = value.get("package")
    if not isinstance(package, dict):
        raise ManifestError("package must be an object")
    if package.get("installation_unit") != "directory":
        raise ManifestError("package.installation_unit must be 'directory'")

    digest = value.get("digest")
    if not isinstance(digest, dict) or digest.get("algorithm") != "git_blob_sha1":
        raise ManifestError("digest.algorithm must be 'git_blob_sha1'")

    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestError("files must be a non-empty array")

    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise ManifestError("each files entry must be an object")
        relative = entry.get("path")
        digest_value = entry.get("git_blob_sha1")
        normalization = entry.get("digest_normalization", "none")
        if not isinstance(relative, str) or not relative:
            raise ManifestError("each files entry requires a non-empty path")
        pure = pathlib.PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ManifestError(f"unsafe manifest path: {relative}")
        if relative in seen:
            raise ManifestError(f"duplicate manifest path: {relative}")
        seen.add(relative)
        if not (
            isinstance(digest_value, str)
            and len(digest_value) == 40
            and set(digest_value.lower()) <= HEX40
        ):
            raise ManifestError(f"invalid git_blob_sha1 for {relative}")
        if normalization not in {"none", "crlf_to_lf"}:
            raise ManifestError(f"invalid digest_normalization for {relative}: {normalization}")

    directories = value.get("required_directories", [])
    if not isinstance(directories, list) or not all(isinstance(item, str) for item in directories):
        raise ManifestError("required_directories must be an array of strings")
    for relative in directories:
        pure = pathlib.PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ManifestError(f"unsafe required directory: {relative}")

    ignored = value.get("ignored_entries", [])
    if not isinstance(ignored, list) or not all(isinstance(item, str) for item in ignored):
        raise ManifestError("ignored_entries must be an array of strings")

    return value


def is_ignored(relative: pathlib.PurePosixPath, patterns: list[str]) -> bool:
    if any(part == "__pycache__" for part in relative.parts):
        return True
    text = relative.as_posix()
    name = relative.name
    return any(fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(text, pattern) for pattern in patterns)


def package_file_set(root: pathlib.Path, ignored: list[str]) -> set[str]:
    found: set[str] = set()
    if not root.is_dir():
        return found
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        relative = pathlib.PurePosixPath(item.relative_to(root).as_posix())
        if is_ignored(relative, ignored):
            continue
        found.add(relative.as_posix())
    return found


def verify(manifest: dict[str, Any], root: pathlib.Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    ignored: list[str] = list(manifest.get("ignored_entries", []))

    checks.append(
        CheckResult(
            check="package_directory",
            status="PASS" if root.is_dir() else "FAIL",
            subject=str(root),
            expected="directory exists",
            observed="directory" if root.is_dir() else "missing",
        )
    )
    if not root.is_dir():
        return checks

    for relative in manifest.get("required_directories", []):
        path = root / pathlib.PurePosixPath(relative)
        checks.append(
            CheckResult(
                check="required_directory",
                status="PASS" if path.is_dir() else "FAIL",
                subject=relative,
                expected="directory exists",
                observed="directory" if path.is_dir() else "missing",
            )
        )

    expected_files: set[str] = set()
    for entry in manifest["files"]:
        relative = entry["path"]
        if entry.get("required", True):
            expected_files.add(relative)
        path = root / pathlib.PurePosixPath(relative)
        if not path.is_file():
            checks.append(
                CheckResult(
                    check="required_file",
                    status="FAIL" if entry.get("required", True) else "WARN",
                    subject=relative,
                    expected="file exists",
                    observed="missing",
                )
            )
            continue

        checks.append(
            CheckResult(
                check="required_file",
                status="PASS",
                subject=relative,
                expected="file exists",
                observed="file",
            )
        )
        normalization = entry.get("digest_normalization", "none")
        observed_digest = git_blob_sha1(path, normalization)
        expected_digest = entry["git_blob_sha1"].lower()
        checks.append(
            CheckResult(
                check="git_blob_sha1",
                status="PASS" if observed_digest == expected_digest else "FAIL",
                subject=relative,
                expected=expected_digest,
                observed=observed_digest,
                detail=f"normalization={normalization}",
            )
        )

    if manifest["package"].get("exact_file_set", False):
        observed_files = package_file_set(root, ignored)
        declared_files = {entry["path"] for entry in manifest["files"]}
        missing = sorted(declared_files - observed_files)
        unexpected = sorted(observed_files - declared_files)
        status = "PASS" if not missing and not unexpected else "FAIL"
        checks.append(
            CheckResult(
                check="exact_file_set",
                status=status,
                subject=str(root),
                expected=sorted(declared_files),
                observed=sorted(observed_files),
                detail=(
                    None
                    if status == "PASS"
                    else f"missing={missing or '[]'}; unexpected={unexpected or '[]'}"
                ),
            )
        )

    return checks


def aggregate(checks: list[CheckResult]) -> str:
    if any(item.status == "FAIL" for item in checks):
        return "FAIL"
    if any(item.status == "WARN" for item in checks):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def report_dict(manifest_path: pathlib.Path, root: pathlib.Path, checks: list[CheckResult]) -> dict[str, Any]:
    return {
        "verifier": "verify_runtime_manifest.py",
        "manifest": str(manifest_path),
        "root": str(root),
        "result": aggregate(checks),
        "checks": [asdict(item) for item in checks],
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"RUNTIME MANIFEST {report['result']}")
    print(f"- manifest: {report['manifest']}")
    print(f"- package root: {report['root']}")
    for item in report["checks"]:
        marker = item["status"]
        line = f"- {marker:<4} {item['check']}: {item['subject']}"
        if item.get("detail"):
            line += f" ({item['detail']})"
        print(line)


def run_self_test(manifest_path: pathlib.Path, manifest: dict[str, Any]) -> int:
    del manifest_path, manifest  # self-test validates the engine with synthetic bytes.
    with tempfile.TemporaryDirectory(prefix="pdl-manifest-selftest-") as temp:
        temp_root = pathlib.Path(temp)
        source = temp_root / "source"
        (source / "agents").mkdir(parents=True)
        (source / "references").mkdir(parents=True)
        synthetic_files = {
            "SKILL.md": b"---\nname: synthetic\n---\n",
            "agents/openai.yaml": b"interface: {}\n",
            "references/evaluation-cases.md": b"# cases\n",
            "references/pdl-conventions.md": b"# conventions\n",
        }
        for relative, data in synthetic_files.items():
            path = source / pathlib.PurePosixPath(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        synthetic_manifest: dict[str, Any] = {
            "manifest_version": "1.0",
            "package": {
                "name": "synthetic",
                "source_path": "source",
                "installation_unit": "directory",
                "recursive_copy_required": True,
                "exact_file_set": True,
            },
            "digest": {"algorithm": "git_blob_sha1"},
            "ignored_entries": [".DS_Store", "Thumbs.db", "desktop.ini", "__pycache__", "*.pyc"],
            "required_directories": ["agents", "references"],
            "files": [
                {
                    "path": relative,
                    "required": True,
                    "git_blob_sha1": git_blob_sha1(source / pathlib.PurePosixPath(relative), "crlf_to_lf" if relative.endswith(".md") else "none"),
                    "digest_normalization": "crlf_to_lf" if relative.endswith(".md") else "none",
                }
                for relative in sorted(synthetic_files)
            ],
        }

        good = temp_root / "good"
        shutil.copytree(source, good)
        if aggregate(verify(synthetic_manifest, good)) != "PASS":
            print("SELF-TEST FAIL: exact copy should pass")
            return 1

        crlf = temp_root / "crlf"
        shutil.copytree(source, crlf)
        skill_crlf = crlf / "SKILL.md"
        skill_crlf.write_bytes(skill_crlf.read_bytes().replace(b"\n", b"\r\n"))
        if aggregate(verify(synthetic_manifest, crlf)) != "PASS":
            print("SELF-TEST FAIL: declared CRLF-to-LF normalization should pass")
            return 1

        missing = temp_root / "missing"
        shutil.copytree(source, missing)
        (missing / "references" / "pdl-conventions.md").unlink()
        if aggregate(verify(synthetic_manifest, missing)) != "FAIL":
            print("SELF-TEST FAIL: missing required reference should fail")
            return 1

        modified = temp_root / "modified"
        shutil.copytree(source, modified)
        skill = modified / "SKILL.md"
        skill.write_bytes(skill.read_bytes() + b"\n")
        if aggregate(verify(synthetic_manifest, modified)) != "FAIL":
            print("SELF-TEST FAIL: byte-modified skill should fail")
            return 1

        extra = temp_root / "extra"
        shutil.copytree(source, extra)
        (extra / "UNDECLARED.txt").write_text("undeclared", encoding="utf-8")
        if aggregate(verify(synthetic_manifest, extra)) != "FAIL":
            print("SELF-TEST FAIL: undeclared package file should fail")
            return 1

    print("RUNTIME MANIFEST SELF-TEST PASS")
    print("- exact recursive copy: PASS")
    print("- declared text EOL normalization: PASS")
    print("- missing required reference: detected")
    print("- modified runtime bytes: detected")
    print("- undeclared package file: detected")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a confirm-with-pseudocode installation against runtime-manifest.json."
    )
    parser.add_argument(
        "--manifest",
        type=pathlib.Path,
        default=DEFAULT_MANIFEST,
        help="Manifest path (default: repository runtime-manifest.json).",
    )
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        help="Package directory to verify. Defaults to package.source_path in the manifest.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--self-test", action="store_true", help="Run verifier failure-mode self-tests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        if args.json:
            print(json.dumps({"result": "ERROR", "error": str(exc)}, indent=2))
        else:
            print("RUNTIME MANIFEST ERROR")
            print(f"- {exc}")
        return 2

    if args.self_test:
        return run_self_test(manifest_path, manifest)

    root = args.root
    if root is None:
        root = SCRIPT_ROOT / manifest["package"]["source_path"]
    root = root.resolve()
    checks = verify(manifest, root)
    report = report_dict(manifest_path, root, checks)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    return 0 if report["result"] in {"PASS", "PASS_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    sys.exit(main())
