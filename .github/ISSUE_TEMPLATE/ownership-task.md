---
name: Ownership task
about: Define a focused implementation task with explicit decisions and verification
name: Ownership task
labels: ""
assignees: "arashmad"
---

## Goal

Describe the useful outcome, not the implementation.

## Why now

Explain why this belongs in the current milestone and what it unblocks or protects.

## Problem to solve

Describe the current behavior, ambiguity, risk, or missing capability.

## Scope

- 

## Out of scope

- 

## Ownership decisions

Before coding, document decisions for:

1. Which layer owns this behavior?
2. What is the smallest useful implementation?
3. What should callers observe on success and failure?
4. What existing behavior or public contract could regress?
5. How will tests prove the intended behavior?

Add task-specific decision questions here.

## Constraints

- Follow `PROJECT_CONTEXT.md` and `PLAN.md`.
- Keep normal tests independent from network access and credentials.
- Do not add dependencies or public abstractions without a current need.
- Keep the PR focused on this ticket.

## Affected areas to inspect

- 

## Verification

- `uv run ruff check`
- `uv run pytest`
- Add focused behavior checks for the task-specific risks.

## Done when

- 

## PR communication

The PR should include:

- what was found,
- the decision and reasoning,
- the minimal changes,
- risks or limitations,
- verification performed,
- work deliberately left out of scope.
