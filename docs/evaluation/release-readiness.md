# Release readiness

## Release posture

**Open-method.** The protocol, PDL conventions, architecture decisions,
technical requirements, frozen test suite, rubric, runner design, and mechanical
package-verification contract are part of the public value. They should not be
withheld merely because they expose the project's mechanism.

Public visibility and runtime visibility are separate concerns. Architecture,
evaluation, and historical evidence may remain public while being excluded from
the normal runtime instruction path.

## Inclusion record

| Material | Public treatment | Reason |
|---|---|---|
| Runtime skill and local PDL reference | Include | Operative public method |
| Runtime manifest and mechanical verifier | Include | Reproducible package integrity and safe installation |
| ADRs and TRDs | Include | Inspectable future architecture |
| Suite 1.1 cases, runners, rubric, and schemas | Include | Reproducibility and claim auditability |
| Short fictional examples | Include | Safe first-use demonstrations |
| Evaluation methodology and scoped summary | Include | Evidence without overstating results |
| Raw model transcripts and internal logs | Exclude from release bundle | Noisy environment detail; not needed for first-use proof |
| Exported conversations and source-working files | Exclude from release bundle | Private development context |
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
  examples.
- Original project contributions, including that compatibility profile, are
  licensed under MIT. `NOTICE.md` records provenance without claiming a license
  to the source page.

## Evidence boundary

The current skill has a fresh 15/15 affected-surface regression: 23 turns,
109/110 applicable-dimension points, no critical failures, no candidate errors,
and no unresolved judge errors. The most recent complete provenance-bound run
used suite 1.0 and passed its release gate at 38/40 with no critical failures.
Do not convert these into a current 40/40 claim.

The contract/manifest restructuring does not change `SKILL.md` or the frozen
behavioral harness. Mechanical installation verification therefore adds a new
assurance layer without creating new model-behavior evidence.

## Current release decision

**READY for the current instruction-level skill, subject to CI on the exact
committed bytes.**

A new 40-case model run is required only if launch copy will claim that the
current skill passed all 40 cases, or after a later migration changes the
runtime instruction path in a way that can affect behavior.

## Runtime package verification

The repository now defines the current installable package in
[`runtime-manifest.json`](../../runtime-manifest.json).

The deterministic verifier:

```text
python scripts/verify_runtime_manifest.py
python scripts/verify_runtime_manifest.py --self-test
```

checks required directories/files, declared Git blob identities, exact package
inventory, and manifest integrity. Text-file EOL normalization is explicit in
the manifest to avoid platform-only false failures. It does not perform semantic model evaluation.

Installation documentation requires agents and manual installers to verify the
installed copy before use. A partial `SKILL.md`-only copy is therefore a
mechanical installation failure rather than a runtime recovery scenario.

## Sanitizer review

The previously recorded sanitizer pass predates the contract/manifest
restructure. Before the next tagged/publicized release, rerun the sanitizer on
the exact Git-visible release set and record the new result rather than carrying
forward a stale file count.

The previous recorded scan had:

| Check | Result |
|---|---:|
| BLOCK findings | 0 |
| WARN findings | 16 reviewed |
| Scan errors | 0 |
| Suppressed files | 0 |
| Suppressed lines or findings | 0 |
| Dangerous ignore patterns | 0 |

No credential, private key, personal contact, local absolute path, client name,
or unscanned file was reported in that run.

## CI validation

GitHub Actions runs on pushes and pull requests through
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

The validation sequence is:

```text
python scripts/verify_runtime_manifest.py
python scripts/verify_runtime_manifest.py --self-test
python scripts/validate_bundle.py
python tests/harness/preflight.py
python tests/harness/harness_selftest.py
```

The first two commands cover mechanical runtime-package integrity. The existing
bundle and harness infrastructure checks remain separate so none of these is
misrepresented as semantic behavioral verification.
