# Release readiness

## Release posture

**Open-method.** The protocol, PDL conventions, architecture decisions,
technical requirements, frozen test suite, rubric, and runner design are part
of the public value. They should not be withheld merely because they contain
the project's central mechanism.

## Inclusion record

| Material | Public treatment | Reason |
|---|---|---|
| Runtime skill and local PDL reference | Include | Operative public method |
| ADRs and TRD | Include | Inspectable future architecture |
| Suite 1.1 cases, runners, rubric, and schemas | Include | Reproducibility and claim auditability |
| Short fictional examples | Include | Safe first-use demonstrations |
| Evaluation methodology and scoped summary | Include | Evidence without overstating results |
| Raw model transcripts and internal logs | Exclude | Internal evidence contains noisy environment detail and is not needed for first-use proof |
| Exported conversations and source-working files | Exclude | Private development context |
| Local release-tool skills | Exclude | Tooling is not part of the PDL runtime release |

## Rights and attribution

- The rewritten `public-skill-launcher` is local release tooling and is excluded
  from this project package.
- The bundled sanitizer retains its upstream MIT notice but is also excluded
  from the project package.
- The supplied Cal Poly/J. Dalbey page had no explicit reuse license. The public
  bundle therefore does not redistribute its HTML, prose, or examples.
- The runtime PDL compatibility profile was independently rewritten to describe
  functional notation in project-authored language with project-authored
  examples. A contiguous-text comparison found no shared passage longer than
  four generic command words.
- Original project contributions, including that compatibility profile, are
  licensed under MIT. `NOTICE.md` records the provenance and identification
  boundary without claiming a license to the source page.

## Evidence boundary

The MIT-ready current skill has a fresh 15/15 affected-surface regression: 23
turns, 109/110 applicable-dimension points, no critical failures, no candidate
errors, and no unresolved judge errors. The most recent complete
provenance-bound run used suite 1.0 and passed its release gate at 38/40 with no
critical failures. Do not convert these into a current 40/40 claim.

## Current release decision

**READY.** The project is MIT-licensed, the source-expression dependency has
been removed, the current runtime bytes have fresh targeted evidence, the
CI-equivalent validation passes locally, and the
[independent documentation review](external-review.md) passed with no blockers.

A new 40-case model run is required only if launch copy will claim that the
current skill passed all 40 cases.

## Sanitizer review

The final 44-file Git-visible release set was scanned without sanitizer ignore
or suppression rules.

| Check | Result |
|---|---:|
| BLOCK findings | 0 |
| WARN findings | 16 reviewed |
| Scan errors | 0 |
| Suppressed files | 0 |
| Suppressed lines or findings | 0 |
| Dangerous ignore patterns | 0 |

The warnings were adjudicated as false positives:

- eight entropy warnings matched long ADR/TRD filenames or link targets;
- six entropy warnings matched long public skill or digest-field identifiers in
  the bundle validator;
- two entropy warnings matched the documented SHA-256 skill digest in the
  results and sanitized evidence ledger.

No credential, private key, personal contact, local absolute path, client name,
or unscanned file was reported.

## CI-equivalent validation

The exact workflow commands pass locally on Python 3.11:

- `python scripts/validate_bundle.py` — PASS, including the portable-path and
  public-link checks;
- `python tests/harness/preflight.py` — PASS;
- `python tests/harness/harness_selftest.py` — PASS (8 checks).

The workflow is defined in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).
No remote is configured in this working copy, so a hosted GitHub Actions run is
not available until the repository is committed and pushed.
