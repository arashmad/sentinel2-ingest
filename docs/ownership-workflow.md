# Ownership Task Workflow

This workflow is used for meaningful features, bugs, and refactors in Sentinel2 Ingest.

The objective is not only to complete tickets. Each task should train repository inspection, scope control, design ownership, implementation judgment, verification, and PR communication.

## 1. Read the task as a problem

Before touching code, identify:

- the caller or system problem,
- why it belongs in the current milestone,
- the smallest useful outcome,
- what is explicitly out of scope.

Do not treat suggested files, class names, or implementation notes as automatically correct. Verify them against the repository.

## 2. Inspect the repository

Find the current behavior before proposing changes.

Check at least:

- the relevant public contract,
- the owning module or layer,
- existing exceptions and exports,
- nearby tests and test style,
- architecture rules in `PROJECT_CONTEXT.md` and `PLAN.md`,
- dependencies and CI commands.

Summarize facts separately from assumptions.

## 3. Write the decision note

Before coding, record concise answers to the ticket's ownership questions.

A useful decision note contains:

- **Facts:** what the code currently does,
- **Decision:** the approach you will take,
- **Reason:** why it is the smallest correct choice,
- **Risk:** what could regress or become ambiguous,
- **Verification:** how tests will prove the decision.

Ask for alignment only when a decision triggers one of the alignment conditions in `PROJECT_CONTEXT.md`.

## 4. Propose a small implementation plan

The plan should name responsibilities, not just files.

Example structure:

1. Define or change the domain/public contract.
2. Wire it into the owning boundary.
3. Add behavior-focused tests.
4. Update exports or documentation only where required.
5. Run repository checks.

Avoid combining unrelated cleanup with the ticket.

## 5. Implement independently

The implementer owns the first implementation attempt.

Guidance should normally provide:

- questions that expose missing reasoning,
- constraints from the current architecture,
- targeted hints,
- review of proposed code or diffs,
- help debugging a concrete failure.

Guidance should not normally provide a complete ready-to-paste implementation before the implementer has proposed a solution. Full code is appropriate only for narrowly mechanical work or after the implementer has shown the design and is blocked on syntax or tooling.

## 6. Verify behavior

Verification must match the risk of the task.

Minimum checks:

```bash
uv run ruff check
uv run pytest
```

Also verify, when relevant:

- public import paths,
- exception inheritance and messages,
- serialization behavior,
- no network or credentials are required by normal tests,
- no dependency or public API change occurred accidentally,
- failure paths are distinguishable when callers need different actions.

Do not write tests that only repeat implementation details.

## 7. Prepare PR communication

The PR should explain ownership, not only list files.

Use this structure:

```md
Closes #<issue>

## What I found
- Current behavior and relevant boundary

## Decision
- Chosen approach and why

## Changes
- Minimal implementation summary

## Risks and limitations
- Important edge cases or deferred behavior

## Verification
- Commands and focused scenarios checked

## Out of scope
- Work deliberately left for later tickets
```

A reviewer should be able to understand the reasoning without reconstructing it from the diff.

## 8. Review before merge

Before merging, confirm:

- the issue's done conditions are satisfied,
- CI passes,
- review threads are resolved,
- scope did not expand,
- public behavior is intentional,
- follow-up work has not been hidden inside comments or TODOs.

## Task interaction pattern

For each new ticket, the working sequence is:

1. Review the ticket and current repository state.
2. Present the ownership questions.
3. The implementer answers with a decision note and plan.
4. Review and correct weak assumptions.
5. The implementer writes the code.
6. Review the diff, tests, and PR.
7. Merge only when the task contract is satisfied.

This replaces the previous pattern of receiving a complete implementation before making the design decisions.
