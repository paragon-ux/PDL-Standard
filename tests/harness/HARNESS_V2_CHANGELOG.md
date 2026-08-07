# Harness v2 change log

## Behavioral suite

The 40-case structure remains intact and is pinned by `suite.lock.json`. Behavioral suite 1.1 makes one intentional expectation correction to A14: a debugging plan must reach an evidence-supported diagnosis without preselecting a cause, but corrective action is required only when remediation is part of the confirmed request. This prevents the test from rewarding an invented requirement.

## Evaluation-harness changes

- Candidate runs bind source skill bytes to the installed skill Codex resolves.
- Candidate manifests record model/configuration, Codex version, suite hashes, skill directory manifests, harness hashes, environment, and selected cases.
- Candidate results retain visible commentary and sanitized Codex events; hidden reasoning event payloads are redacted.
- Tool-like candidate activity is separately indexed while the complete sanitized event stream remains available for audit.
- Unexpected non-JSON stdout is stored only as length/hash metadata rather than raw text.
- Structural lint now evaluates commentary as well as the final assistant message.
- The semantic judge receives commentary and activity evidence, not only the final response.
- Literal protocol-skill names/invocation syntax in test evidence are neutralized before judging to reduce judge contamination.
- Tool-like activity by the judge itself is a judge-infrastructure error.
- Judge parsing is strict and fail-closed.
- Rubric dimensions can be `N/A`; only applicable dimensions contribute to the score.
- A `PASS` judgment cannot contain an applicable dimension scored `0`.
- New summary tooling enforces full-suite completeness, provenance consistency, critical-failure gates, tier pass rules, and judge/candidate infrastructure health.
- `preflight.py` validates the locked behavioral suite, schemas, Python syntax, source skill presence, and relative Markdown links.
- `harness_selftest.py` exercises event redaction, tool detection, skill-directory hashing, N/A parsing, judge neutralization, commentary linting, and candidate-prompt neutrality without model calls.
- Historical Harness v1 evaluator files remain in the private evidence archive,
  outside this public bundle, so the original `/16` results remain auditable
  after the v2 rubric update.

## Offline pre-screen performed before handoff

The updated kit was checked with:

- `preflight.py` — PASS;
- `harness_selftest.py` — PASS (7 checks in that historical pre-screen; the
  current self-test has 8 checks);
- upgraded `transcript_lint.py` against the historical 40-case Sol transcript — 0 structural failures/warnings;
- synthetic candidate subprocess run — PASS, including provenance manifest and hidden-reasoning redaction;
- synthetic multi-turn candidate run — PASS across Prompt → Plan → Execute;
- synthetic judge run — PASS with candidate-manifest verification;
- malformed synthetic judge output — correctly failed closed with non-zero exit;
- synthetic judge tool use — correctly marked as judge infrastructure error with non-zero exit;
- historical v1 harness snapshot hashes — verified identical to the files that produced the stored historical results.

No live Codex model run was performed during this pre-screen; the returned v2 package is intended for that next step.

## Post-handoff live-run hardening

The first live full-suite judge passes exposed intermittent mechanical output
errors: the judge sometimes reported a `SCORE` that did not equal its own
dimension totals or returned `PASS` with an applicable dimension scored `0`.
Strict validation correctly rejected those rows, but a full 40-case run could
not produce canonical evidence reliably.

The judge runner now retries strict-format failures up to three times per case,
records every failed attempt, and still fails closed if no attempt validates.
Judge tool activity remains terminal and is never repaired by retry. The judge
prompt also clarifies that representing a user-requested future output is not
itself substantive answer leakage, and it includes a mechanical score checklist.
The behavioral cases, suite lock, rubric, skill, and PDL reference were not
changed.

A later full judge pass exposed a second inconsistency: a judge declared a
critical failure while awarding full credit to every applicable dimension. The
parser now rejects and retries a `FAIL` with no applicable deduction and a
critical failure with no applicable zero. The judge prompt also clarifies that
restating user-supplied source facts in Prompt Pseudocode is semantic capture,
not execution of the requested transformation.
