# NOVA Engineering Principles

**Approved:** 6 August 2026

## Core rule

**Reuse first. Build last.**

Before writing custom code, search for proven, free, open-source software,
libraries, frameworks, or tools that already solve the problem.

## Decision order

1. Search for an existing proven solution.
2. Evaluate whether it can be integrated into NOVA.
3. Reuse or extend it where practical.
4. Write custom code only when no suitable free solution exists or a small
   integration layer is required.

The evaluation must consider:

- license compatibility and continued free use;
- security history and supply-chain risk;
- privacy and local-operation support;
- maintenance activity and project stability;
- reliability, testability, and recovery behavior;
- integration complexity and long-term ownership cost; and
- compatibility with NOVA's user-control and audit boundaries.

Choosing an existing dependency is not automatically preferable. Record why it
is a better fit than a small local implementation, and do not adopt it when its
risk, complexity, or authority exceeds the problem it solves.

## Current platform capability check

Before proposing custom code, verify whether the current versions of ChatGPT,
Codex, Codex Remote, GitHub, Docker, Tailscale, Ollama, Windows, or NOVA already
provide the required capability. Use current official documentation, installed
version evidence, the live repository, and a bounded proof when behavior is
uncertain.

Do not build a replacement because an older version lacked a feature or because
model memory says the platform cannot do it. Record the verified capability,
its limits, and why reuse, integration, extension, or custom implementation is
the better fit.

## Philosophy

- NOVA owns the workflow.
- External models and software are tools, not the brain.
- Keep data local whenever possible.
- Prefer simple, reliable solutions over clever ones.
- Avoid reinventing the wheel.
- Integrate first. Build second. Rewrite only when necessary.

## Rewrite threshold

Do not rewrite working systems for preference or novelty. A rewrite requires
evidence that extension or integration cannot safely meet an approved need,
plus a bounded migration, verification, recovery, and rollback plan.

## Required engineering-review evidence

For each new capability, record:

- what existing NOVA components can be reused;
- what free, open-source solutions were considered;
- why the selected option fits NOVA's boundaries;
- what custom code remains and why it is necessary; and
- any new license, security, privacy, maintenance, or recovery risk.

This review is proportional to the change, but it is never skipped.
