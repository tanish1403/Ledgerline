# Prompt: Review a milestone (paste after each milestone, in a fresh task)

```
Act as a skeptical senior reviewer. Do not edit files. Review the changes since the last commit tagged
`milestone-N-start` (or `git diff main`).

Check, and report only real findings with file and line:
1. Security: auth bypass, missing role checks, SQL built from strings, path traversal, secrets in code or
   logs, model output executed or trusted.
2. Correctness: wrong status codes, missing validation, race conditions, unhandled errors.
3. Tests: untested failure paths, tests that cannot fail, tests that call the network.
4. Simplicity: anything the owner could not explain in two minutes; dead code; needless abstraction.
5. Docs: README and docs/PROGRESS.md match what the code actually does.

End with a list ordered by severity: Fix now / Fix before next milestone / Optional.
```
