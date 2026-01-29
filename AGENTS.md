# Repository Guidelines

## Project Structure & Module Organization
- `vibe_eval/` is the core library (CLI, runner, sandbox, scoring, judges, tools, model adapters).
- `eval_cases/` contains benchmark cases, each in `case_XX_slug/` with `spec.md` and optional `tests.py`.
- `tests/` holds pytest unit tests for core behavior (sandbox, scoring, judges).
- `results/`, `runs/`, and `logs/` store generated outputs; keep large artifacts out of source changes.
- `gold/` contains reference datasets for reports.

## Build, Test, and Development Commands
- `pip install -e .` — editable install for local development.
- `pip install -e .[test]` — adds pytest + Playwright.
- `python -m vibe_eval list-cases` — list all evaluation cases.
- `python -m vibe_eval run -m claude-sonnet-4.5 -c case_01_pomodoro` — run a single case.
- `python -m vibe_eval dashboard results/TIMESTAMP_results.json` — open the results dashboard.
- `python -m pytest` — run unit tests.
- `python -m playwright install` — install browser binaries for HTML validation/tests.

## Coding Style & Naming Conventions
- Python 3.9+; 4-space indentation; follow PEP 8.
- Use `snake_case` for modules/functions, `CamelCase` for classes, and `UPPER_CASE` for constants.
- Case folders follow `eval_cases/case_XX_slug/`; keep case specs in `spec.md` and tests in `tests.py`.
- Generated apps must be self-contained with stdlib-only execution (no external package installs).

## Testing Guidelines
- Framework: `pytest` for unit tests; Playwright for functional HTML validation.
- Test files use `test_*.py`; test functions use `test_*`.
- Example: `python -m pytest tests/test_scoring_weights.py`.
- No explicit coverage target is documented; add/extend tests when changing scoring, sandboxing, or judge logic.

## Commit & Pull Request Guidelines
- Commit messages in history are short, sentence-case, and imperative (no scope/prefix). Follow that style.
- PRs should include: concise summary, test commands run, and any new/updated case IDs.
- For UI/dashboard changes or HTML outputs, include a screenshot or sample render in the PR description.

## Configuration & Secrets
- Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`.
- **Only OpenRouter API key is required** - all models and judges route through OpenRouter.
- Never commit real secrets or generated result artifacts.

## Result Persistence & Fault Tolerance
- **CRITICAL: Always write results incrementally as they are generated, not only at the end.**
- Long-running processes (evaluations, batch jobs, data processing) must save progress after each unit of work completes.
- Benefits: progress recovery after crashes, real-time monitoring, fault tolerance.
- Implementation patterns:
  - Append results to JSON/checkpoint files after each case/item completes
  - Maintain partial state files that can be resumed
  - Leaderboards/metrics can be computed from partial results (mark as "partial" if incomplete)
  - Individual artifacts (code files, outputs) should be written immediately when created
- Avoid: accumulating all results in memory and writing only at completion.
- Exception: Only acceptable if the entire operation completes in < 30 seconds and failure is rare.
