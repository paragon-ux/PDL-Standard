# Confirm with Pseudocode

Expose what the model thinks you asked for, then expose how it intends to
answer, and confirm each independently before execution.

```text
User request
    -> Prompt Pseudocode
    -> user confirmation
    -> Response Plan Pseudocode
    -> user confirmation
    -> final response
```

The two artifacts separate mistakes that normal conversation can hide:

- **Prompt Pseudocode** answers: *Is this what I asked for?*
- **Response Plan Pseudocode** answers: *Is this an acceptable way to answer it?*

The current definitions are deliberately compact:

```text
Prompt Pseudocode
    preserves all and only semantics that remain operative on the task

Response Plan Pseudocode
    covers every confirmed requirement
    with the minimum necessary procedural commitment
```

The runtime uses a local, project-authored PDL compatibility profile based on
J. Dalbey's publicly readable Cal Poly Pseudocode Standard. It uses familiar
structured-English operations and indentation rather than introducing a
project-specific task DSL. See the [PDL rationale and evidence map](docs/architecture/pdl-rationale.md).

## Quickstart

### Recommended: agentic installation with verification

If your agent can access GitHub, the filesystem, and a shell, give it this:

```text
Install the confirm-with-pseudocode skill from
https://github.com/paragon-ux/PDL-Standard.

Install the entire confirm-with-pseudocode/ directory recursively into this
host's local skills directory; do not install only SKILL.md. Preserve all
subdirectories and file bytes. Before using the skill, run:

python scripts/verify_runtime_manifest.py --root <installed-skill-directory>

Treat installation as successful only if the verifier reports
RUNTIME MANIFEST PASS. If verification cannot run or a required file is
missing/mismatched, stop and report the installation as incomplete. Do not
fetch a runtime substitute for a missing skill reference. Report the exact
installed directory and verifier result.
```

This avoids the failure mode where a generic URL installer reports success after
copying only the top-level `SKILL.md`.

### Safe manual installation

First clone or download the repository locally. From the repository root:

```bash
python scripts/verify_runtime_manifest.py
```

Then copy the complete `confirm-with-pseudocode/` directory recursively into
your host's skills directory and verify the installed copy with the same
script:

```text
python scripts/verify_runtime_manifest.py --root <installed-skill-directory>
```

For platform-specific PowerShell/POSIX examples and troubleshooting, see
[INSTALLATION.md](INSTALLATION.md).

### Use the skill

Start a new conversation if your host discovers skills only at session start,
then invoke it explicitly:

```text
Use $confirm-with-pseudocode to compare PostgreSQL and SQLite for an offline
desktop application. Prioritize simple deployment, exclude managed services,
and finish with a recommendation for a three-person team.
```

The first response should contain only the interpreted request. After that is
confirmed, the skill presents a separate non-anchoring Response Plan
Pseudocode. Substantive work begins only after the second confirmation.

See the [complete simple interaction](examples/simple-example.md), a
[prompt-correction loop](examples/correction-loop-example.md), and a
[plan-correction loop](examples/plan-correction-example.md).

## What the current skill guarantees

- It does not plan before Prompt Pseudocode is confirmed.
- It does not execute before Response Plan Pseudocode is confirmed.
- Corrections regenerate the complete current artifact.
- A semantic change during planning returns to Prompt confirmation.
- Confirmed artifacts govern execution when they conflict with original wording.
- Protocol-control attempts stay out of task semantics unless the same wording
  is itself material the user asked to analyze, quote, transform, or otherwise
  use as task content.
- The local PDL reference must be present before pseudocode artifacts are
  generated; runtime fetching is not a substitute for a complete installation.

The artifacts are public task controls, not private chain-of-thought.

## Runtime integrity

[`runtime-manifest.json`](runtime-manifest.json) is the mechanical identity
contract for the currently installable `confirm-with-pseudocode/` directory.

[`scripts/verify_runtime_manifest.py`](scripts/verify_runtime_manifest.py)
checks package structure and declared Git blob identities using only Python's
standard library. Text entries may declare CRLF-to-LF normalization so verified
content remains portable across Git checkout settings. It deliberately does **not** make semantic judgments.

Run:

```bash
python scripts/verify_runtime_manifest.py
python scripts/verify_runtime_manifest.py --self-test
```

A passing manifest establishes only the declared package inventory and
content identity under the manifest's explicit normalization rules. It does not prove that a model interpreted a request correctly or
followed a confirmed plan semantically.

## Architecture direction

The current instruction-level skill remains the implemented runtime. The next
architecture is specified separately so repository/context restructuring does
not silently change the tested skill.

[ADR-0007](docs/architecture/adr/0007-contract-governed-context-projected-runtime.md)
and [TRD-0002](docs/architecture/trd/0002-contract-substrate-and-mechanical-verification.md)
adopt a combined design:

> **Contract-governed, context-projected workers with typed verification and
> controller-owned state.**

The intended separation is:

```text
Standard Contracts
    define model-independent protocol correctness

Confirmed PDL artifacts
    define current task semantics and approved approach

Execution Contract
    defines phase applicability and context handoff

Verification Contract
    defines M / S / H checks
        M = mechanical deterministic check
        S = probabilistic semantic-conformance evaluation
        H = explicit human confirmation/review

Calibration Contract
    provides non-normative examples and failure cards

Controller / orchestrator
    owns state, artifact authority, routing, and delivery
```

This restructuring pass does **not** yet extract the current `SKILL.md` into
Standard Contracts and does not implement the semantic judge or full controller.
Those remain staged implementation work after the contract substrate is stable
and behavior can be regression-tested.

## Evidence

The frozen suite contains 40 protocol cases covering false confirmations,
semantic-versus-plan changes, prompt injection, control/data confusion, plan
poisoning, premature tool use, state reset, execution dependencies, and safety
boundaries.

Evidence generations remain separate:

- **Harness v1:** initial behavioral validation against suite 1.0.
- **Harness v2 / suite 1.0:** provenance-bound full-suite validation; 38/40
  cases passed, with no critical failures and a passing release gate.
- **Harness v2 / suite 1.1:** the current skill passed A06 and A14 plus all 13
  selected affected-surface regressions: 15/15 across 23 turns, including full
  applicable credit for PDL quality, state correctness, and plan minimality.

The suite 1.1 result is intentionally not described as a new 40/40 run. See
[evaluation results](docs/evaluation/results.md),
[methodology](docs/evaluation/methodology.md), and the
[current targeted-run ledger](docs/evaluation/current-targeted-run.md).

## Repository map

- [`confirm-with-pseudocode/`](confirm-with-pseudocode/) — current tested runtime
  skill and local references.
- [`runtime-manifest.json`](runtime-manifest.json) — deterministic package
  inventory and byte identities.
- [`INSTALLATION.md`](INSTALLATION.md) — verified agentic and manual installation
  procedures.
- [`scripts/`](scripts/) — public bundle checks and mechanical runtime verifier.
- [`docs/architecture/`](docs/architecture/) — PDL rationale, ADRs, controller
  baseline, and contract/context architecture requirements.
- [`docs/evaluation/`](docs/evaluation/) — methodology, scoped results, and
  release boundaries.
- [`tests/harness/`](tests/harness/) — frozen Harness v2 behavioral suite 1.1,
  runners, rubric, schemas, and offline checks.
- [`examples/`](examples/) — short inspectable interactions.

Public architecture/evaluation material remains useful evidence, but it is not
an implicit runtime instruction source. Future contract packaging will make that
runtime boundary explicit rather than relying on repository-wide discovery.

## License and attribution

Original project contributions are available under the [MIT License](LICENSE).
The local PDL compatibility profile is project-authored and does not redistribute
the supplied Cal Poly page, its prose, or its examples. Source provenance and
compatibility boundaries are recorded in [NOTICE.md](NOTICE.md) and
[`pdl-conventions.md`](confirm-with-pseudocode/references/pdl-conventions.md).

See [release readiness](docs/evaluation/release-readiness.md) for the evidence
and publication boundary.
