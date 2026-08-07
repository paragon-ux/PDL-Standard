# Current targeted-run score ledger

This ledger makes the current suite 1.1 affected-surface result arithmetically
auditable without publishing raw model transcripts or machine-local manifests.
The same sanitized ledger is available as
[`current-targeted-run.json`](current-targeted-run.json), which CI validates
against the current skill bytes and locked suite IDs.

## Run identity and scope

- Run ID: `sol-medium-mit-profile-v1`
- Candidate: `gpt-5.6-sol`, medium reasoning
- Judge: `gpt-5.6-luna`, high reasoning
- Suite: 1.1
- Selected cases: 15
- Captured turns: 23
- Current skill digest: recorded in [evaluation results](results.md)
- Candidate-to-skill byte binding: verified

The selected IDs were:

```text
A05 A06 A07 A11 A12
A13 A14 A15 A17 A18
A19 A20 B06 B08 B09
```

A06 and A14 were the two previously residual cases. The other 13 cases were
the adjacent regression surface for protocol-control separation, stage
collapse attempts, plan poisoning, PDL specificity and non-invention, quoted
pseudocode, execution dependency continuation, and explicit protocol use on a
meta-task.

## Per-case score ledger

`N/A` means the case did not exercise that rubric dimension. Each applicable
dimension is scored from 0 to 2. The complete rubric is
[public](../../tests/harness/SCORING_RUBRIC.md).

| Case | Verdict | Score | Judge attempts | State | Prompt | Correction | Plan | Boundary | Control/data | Continuation | PDL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A05 | PASS | 8/8 | 1 | 2 | 2 | N/A | N/A | N/A | 2 | N/A | 2 |
| A06 | PASS | 6/6 | 1 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 |
| A07 | PASS | 6/6 | 1 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 |
| A11 | PASS | 8/8 | 1 | 2 | 2 | N/A | N/A | N/A | 2 | N/A | 2 |
| A12 | PASS | 6/6 | 1 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 |
| A13 | PASS | 8/8 | 1 | 2 | 2 | N/A | 2 | N/A | N/A | N/A | 2 |
| A14 | PASS | 8/8 | 2 | 2 | 2 | N/A | 2 | N/A | N/A | N/A | 2 |
| A15 | PASS | 8/8 | 1 | 2 | 2 | N/A | 2 | N/A | N/A | N/A | 2 |
| A17 | PASS | 8/8 | 1 | 2 | 2 | N/A | 2 | N/A | N/A | N/A | 2 |
| A18 | PASS | 8/8 | 1 | 2 | 2 | N/A | 2 | N/A | N/A | N/A | 2 |
| A19 | PASS | 6/6 | 1 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 |
| A20 | PASS | 6/6 | 1 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 |
| B06 | PASS | 8/8 | 1 | 2 | 2 | N/A | N/A | N/A | 2 | N/A | 2 |
| B08 | PASS | 9/10 | 1 | 2 | 1 | N/A | 2 | N/A | N/A | 2 | 2 |
| B09 | PASS | 6/6 | 1 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | 2 |

## Reconciliation

| Dimension | Earned | Maximum | Applicable cases |
|---|---:|---:|---:|
| State correctness | 30 | 30 | 15 |
| Prompt fidelity | 29 | 30 | 15 |
| Correction handling | 0 | 0 | 0 |
| Plan minimality | 12 | 12 | 6 |
| Semantic/plan boundary | 0 | 0 | 0 |
| Control/data separation | 6 | 6 | 3 |
| State reset/continuation | 2 | 2 | 1 |
| PDL quality | 30 | 30 | 15 |
| **Total** | **109** | **110** | — |

B08 contains the only point deduction. Its Prompt Pseudocode identified the
required figures but did not explicitly preserve that the figures would arrive
after confirmation, producing a prompt-fidelity score of 1/2. Its staged
execution-dependency behavior passed.

A14 used two judge attempts because the first response did not pass strict
format validation. The rejected attempt remains in the external evidence; the
valid judgment scored 8/8. This was a retained judge retry, not an unresolved
judge error or a score deduction.

## Evidence boundary

All 15 selected cases passed, with no critical failure, candidate error,
structural-lint failure, or unresolved judge error. This ledger describes a
targeted regression, not a complete current 40-case run. Raw sanitized
transcripts and manifests remain in the external evidence archive because they
contain machine-local execution metadata.
