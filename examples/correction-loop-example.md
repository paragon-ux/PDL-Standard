# Prompt correction loop

**User**

```text
Use $confirm-with-pseudocode to draft a migration checklist for a ten-person
team moving from System A to System B. Prioritize speed.
```

The assistant returns the complete Prompt Pseudocode and waits.

**User**

```text
Change the team to twelve people and prioritize rollback safety instead.
Everything else is correct.
```

The assistant regenerates the entire interpretation:

```text
CREATE a migration checklist
    FOR moving from System A to System B
    FOR a twelve-person team
    PRIORITIZING rollback safety
```

It does not emit a patch, plan the migration, or treat "everything else is
correct" as confirmation that overrides the correction.
