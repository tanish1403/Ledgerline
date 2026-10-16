# Prompt: Debug a failure (paste into a fresh task)

```
A test or command is failing. Find the root cause before changing anything.

Failing command: <paste the command>
Output (last 40 lines): <paste>

Steps:
1. Read the failing test and the code it exercises. Do not guess.
2. State your hypothesis in two sentences and the one experiment that would confirm it.
3. Run that experiment. Report the result.
4. Fix the cause, not the symptom. Do not skip, delete or loosen the test, and do not add `# noqa`.
5. Run `make lint` and `make test` and show me the output.

If you cannot find the cause in three experiments, stop and tell me what you ruled out.
```
