# Setup: VS Code + Cline + OmniRoute (all free)

## 1. Install the basics

- VS Code, Git, Docker Desktop, Python 3.12, and `uv` (optional).
- Optional: Ollama for a fully local model.

## 2. Run OmniRoute (the model gateway)

```bash
npm install -g omniroute && omniroute
# or
docker run -p 20128:20128 diegosouzapw/omniroute
```

- Open the dashboard it prints, add providers that have a free tier, and create an API key.
- Check it works: `curl http://localhost:20128/v1/models`.
- Keep it on localhost. Do not tunnel or expose port 20128. Set an admin password.
- Upstream providers see your prompts. Never put secrets or private data in prompts.
- Use only free tiers you signed up for yourself, with your own keys.
- Use the repo `diegosouzapw/OmniRoute` and check its recent commits before installing.

## 3. Connect Cline

1. Install the **Cline** extension in VS Code.
2. Cline settings, then Providers, then **OpenAI Compatible**.
3. Base URL `http://localhost:20128/v1` (include `/v1`, no trailing slash).
4. API key: the key from the OmniRoute dashboard.
5. Model ID: pick one from the `/v1/models` list, or a combo you created. Click Verify.
6. Fill in the model details Cline cannot detect for custom endpoints: context window and max output.
   One Cline version ignored the separate Act model when Plan and Act used different models, so use the
   same model for both at first.

Cline reads project rules from `.clinerules`. This repo ships one (copied from `AGENTS.md`). Confirm the
current behaviour in Cline's docs if it does not pick it up.

## 4. Other tools (optional)

- **GitHub Copilot Free**: reads `.github/copilot-instructions.md`, which this repo ships. Free plan limits
  are small (about 2,000 completions and 50 chat requests a month at the time of writing) and Copilot moved
  to usage-based billing in June 2026. Use it for autocomplete, not as the main agent.
- **Antigravity**: has a free tier with weekly limits that have been cut before. I found nothing showing it
  accepts a custom endpoint, so OmniRoute will not plug into it. Paste `AGENTS.md` into its rules or
  context mechanism (check its docs for the current file name).

## 5. Working loop

1. `git init`, `cp .env.example .env`, edit it, `make install`, `make test` (one passing test), then make
   a first commit (`git add . && git commit -m "chore: skeleton"`). The milestone prompts use `git tag`,
   which needs at least one commit. Create a GitHub repo and push so CI runs.
2. Open the repo in VS Code. Open Cline.
3. Paste `docs/prompts/00_kickoff.md`. Let it read the rules and restate the plan.
4. Paste the next milestone prompt. Use **Plan** mode first, read the plan, then switch to **Act**.
5. Review every diff. Run `make lint` and `make test` yourself.
6. Commit. Tick the box in `docs/PROGRESS.md`. Open a pull request against your own repo and review it.

## 6. Tips for free or small models

- Give one milestone at a time, and ask for one step at a time inside it.
- If it loops or produces broken code, stop, start a new task, and paste only the failing test and file.
- If tool calling is unreliable, switch the model in your OmniRoute combo.
- Keep `AGENTS.md` short. Long rules files get ignored by small models.
- You are the reviewer. Read the code, run it, and ask the agent to explain anything you cannot explain.

## 7. Interview honesty

Write in `docs/PROGRESS.md` which parts the agent wrote and which you changed. Be ready to explain any
file without the agent open. Name the agentic coding tool you actually used on your resume.
