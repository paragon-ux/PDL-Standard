# Architecture

The current runtime remains the tested instruction-level
`confirm-with-pseudocode` skill. Architecture documents describe how that
behavior can evolve into an explicitly governed runtime without treating public
repository material as implicit instructions.

The architecture now has two complementary tracks:

- **controller protocol baseline** — deterministic state, artifact authority,
  phase projection, and optional Result Pseudocode;
- **contract/context substrate** — one normative requirements layer, typed
  verification, mechanical package identity, source-bound semantics, and
  context-projected workers.

Start here:

- [Project origin, PDL rationale, and evidence map](pdl-rationale.md)
- [Architecture decision records](adr/README.md)
- [Technical requirements](trd/README.md)

Current implementation status:

- `confirm-with-pseudocode/SKILL.md` is the implemented and behaviorally tested
  runtime.
- `runtime-manifest.json` and `scripts/verify_runtime_manifest.py` provide the
  first deterministic mechanical substrate.
- ADR-0007 and TRD-0002 define the staged migration toward contract-governed,
  context-projected workers.
- Standard-contract extraction, semantic conformance workers, and the full
  controller UI remain future implementation work.

Architecture specifications do not themselves change the current skill's
behavior or expand the claims supported by the frozen evaluation evidence.
