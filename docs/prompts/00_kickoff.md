# Prompt 00: Kickoff (paste first, in Plan mode)

```
You are my pair-programmer on this repository. Do not write code yet.

1. Read AGENTS.md, docs/PLAN.md and docs/PROGRESS.md.
2. Run `ls -R` (skip .venv and node_modules) and `make test` and tell me whether the skeleton works.
3. In 8 lines or fewer, restate what we are building and the order of the milestones.
4. List anything in the plan that looks risky or unclear for a free or small LLM to build, and how you
   would reduce that risk.
5. Ask me at most three questions. Then stop and wait for my next prompt.

Rules for this whole session:
- One milestone at a time, tests first, small steps, show me each diff summary before committing.
- Never touch .env. Never add a dependency without asking.
- If you are unsure about a library API, check the installed version or say you are unsure.
```
