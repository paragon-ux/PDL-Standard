# Response-plan correction loop

Assume the user has already confirmed Prompt Pseudocode for comparing two
deployment approaches and receiving a recommendation.

The assistant proposes a high-level Response Plan Pseudocode. Before confirming
it, the user says:

```text
Keep the confirmed request fixed, but use qualitative tradeoff analysis only.
Do not calculate a numeric score.
```

The assistant keeps the confirmed Prompt Pseudocode fixed and regenerates the
complete plan:

```text
GATHER information needed to evaluate both deployment approaches

COMPARE the approaches
    USING the confirmed criteria
    WITHOUT numeric scoring

ASSESS qualitative tradeoffs

FORM the requested recommendation
```

It waits for confirmation again. If the user instead changed the alternatives,
audience, or requested output, the skill would return to Prompt Pseudocode
because those are semantic changes.
