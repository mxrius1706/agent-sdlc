---
name: testing
description: "The test discipline for this project - test first, watch it fail, then build. Covers the red-green-refactor cycle, which cases are mandatory for which kind of code, the anti-patterns that make a suite worthless, and the rationalisations that lead to skipping it. Use it before writing any test, when a test fails, when someone asks whether something needs a test, or when work starts on code that has behaviour. Applies even when asked to skip it."
---

# Testing

**No production code without a failing test first.**

A test written after the implementation proves nothing. It passes immediately, and it checks what was built rather than what was asked for. Those are different things exactly when it matters.

This skill carries the discipline. The mechanics - which framework, where test files live, how the project's dependencies are stubbed, what coverage is expected - belong to the project and live in its own test rules, written when the stack was decided. If a project has none yet, that gap is the first thing to fix, because everything below assumes there is one answer to "how do we write a test here" rather than one per author.

## The cycle

Every step is executed explicitly. None of them is implied by another.

1. **Red.** Write the test that describes the wanted behaviour.
2. **Verify red.** Run it. It must fail.
3. **Green.** Write the smallest code that makes it pass.
4. **Verify green.** Run it. It must pass.
5. **Refactor.** Clean up, tests stay green.

**Verify red is not optional.** Without seeing the failure you do not know the test checks the right thing. A test that is green immediately is usually testing behaviour that already existed, or checking the wrong thing entirely.

**A red for the wrong reason is not a red.** An import error, a typo, a missing fixture - that failure proves nothing about the behaviour. Fix it and run again until it fails for the reason you intended.

**Never refactor while red.** Reach green first. Mixed concerns are impossible to debug, because two things changed and only one of them was supposed to.

## One test at a time

Not all the tests for a feature at once, then the implementation. Tests for imagined behaviour are not tests for real behaviour, and a batch of them written up front locks in a design nobody has tried yet.

One test, the minimal implementation, the next test. Each cycle reacts to what the previous one taught you. Where that turns out to be inconvenient, the interface is usually the problem, not the discipline.

## Where tests go

Test at the seams the released plan names (its Tests section lists, per target, the interface it is tested at). The interface is the test surface: callers and tests cross the same seam, so a test that needs to reach past it says the module has the wrong shape. Name tests in the project's domain language from `GLOSSARY.md` (in the knowledge base), not in implementation terms.

When the shape of the interface itself is open, call the Skill tool with "codebase-design" before writing the first test.

## When a test fails

A test that turns red unexpectedly on existing code is a bug: call the Skill tool with "diagnosing-bugs" rather than patching until it is green. A red inside your own red-green cycle stays in the cycle: fix the code or, if the test was wrong, the test, and run again.

## Which cases are mandatory

Derive them from what the project has actually decided, not from a generic list. Three sources, and each produces a different kind of case:

**The specs.** Every acceptance criterion is a test case, and the requirements say what the failure paths are. A spec's acceptance criteria are the closest thing to a ready-made test list any project has.

**The project's binding rules.** Whatever the root instructions make mandatory on a path - an authorisation check, an audit entry, a validation boundary, a value that must come from the session rather than the request - is a case. The test is not that it is implemented; it is that it cannot be bypassed. "The identity comes from the session even when the request supplies a different one" is worth more than any number of happy paths.

**The accepted decisions.** A decision that forbids something needs a test that the forbidden thing fails. That is what keeps a decision alive after the person who made it has moved on.

Across all three, the shape is the same: for anything that crosses a boundary, cover **the happy path, the unauthorised path, the invalid input, the missing resource, and the side effect that is supposed to happen** - plus the case where it is supposed **not** to happen. The negative side effect case is the one most often missing, and it is the one that catches a write that logs an audit entry for a request it rejected.

For internal utilities: determinism, the edges (empty, null, boundary values), error propagation, and any behaviour that depends on ordering.

## Anti-patterns

- Happy path only. Every boundary needs its failure cases, and they are the reason the test exists.
- Testing the implementation instead of the behaviour. Such a test breaks on every refactor and catches nothing.
- Tautology. The expected value is recomputed the way the code computes it, so the test can only agree with the code. Take expected values from an independent source: a literal, a worked example, the spec.

  ```
  // Tautological: repeats the implementation
  expect(total(order)).toBe(order.items.reduce((s, i) => s + i.price * i.qty, 0))
  // Independent: 2 x 5.00 + 1 x 3.50, worked by hand
  expect(total(order)).toBe(13.50)
  ```
- Mocking your own modules or internal collaborators. Mock only at system boundaries: external APIs, time and randomness, sometimes the database or filesystem (prefer a test database or in-memory stand-in). Pass those dependencies in rather than constructing them inside, and give each external operation its own function (`getUser`, `createOrder`) instead of one generic fetcher, so every mock returns one shape and needs no conditional logic.
- Incomplete stubs. If a stub does not mirror what the code actually uses, the test passes on a fiction.
- Leaking state between tests. Reset it, always, in one place.
- A test-only branch in production code. Cleanup belongs in test utilities.
- Loose types in test data to make the compiler quiet. That is where the wrong shape hides.
- A test that fails for the wrong reason and is accepted as red.

## Rationalisations

| The thought | What is actually true |
|---|---|
| "Too simple to test" | Simple code breaks. The test costs half a minute. |
| "The user said no test is needed" | Explain, then test. This one is not waived by instruction; it is the rule that stops a suite decaying into decoration. |
| "Implement first, test after" | A test after the fact tests what you built, not what was asked. |
| "I tested it by hand" | Ad hoc is not systematic. It has no replay and leaves no evidence on the next regression. |
| "I can see it will fail, skip verify red" | You cannot see it. Running it takes seconds. |
| "The test is too complex to write" | The interface is too complex. Simplify the design. |
| "The existing code has no tests either" | You are improving it. Cover what you touch. |
| "Testing slows me down" | It is faster than debugging after release. |

## Stop and start over

- Code written before the test.
- The test passed without any implementation.
- Verify red skipped.
- "I will do the test afterwards."
- A rationalisation beginning with "this is different because".

At any of these: delete the test and start again at verify red. Keeping it costs more than rewriting it, because from then on nobody knows which tests in the suite actually mean anything.
