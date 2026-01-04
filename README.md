# Vibe Code Bench

> **Evaluate LLMs on "Vibe Coding" — building complete apps from natural language prompts.**

Vibe Code Bench is a framework for testing how well AI models can take casual, human-style prompts ("Build me a Pomodoro timer") and produce **fully working, self-contained applications** without installing any external packages.

## V2 Updates (2026-01-04)

- **Multi-Judge Arbitration** - Uses 3 judges by default (Claude Opus 4.5, GPT-4o, Gemini 3 Flash) via OpenRouter to reduce single-model bias
- **Runtime Execution Validation** - Actually runs generated code with Playwright for HTML, subprocess for Python
- **Dependency Enforcement** - Blocks pip/npm/etc. commands; validates imports against Python stdlib whitelist
- **Rebalanced Scoring** - Executes weight increased to 25%, Code Quality to 15%, Elegance removed (too subjective)
- **Execution Gate** - Non-running code (executes < 3) capped at 30 points maximum
- **Cost Tracking** - Separate LLM Cost and Judge Cost in results
- **Performance Optimizations** - File caching, Playwright browser reuse, head-to-head opt-in

```bash
# V2 CLI options
python -m vibe_eval run -m gpt-4o -c all                  # Multi-judge (default)
python -m vibe_eval run -m gpt-4o -c all --single-judge   # Single judge mode
python -m vibe_eval run -m gpt-4o -c all --no-validation  # Skip execution validation
python -m vibe_eval run -m gpt-4o -c all --head-to-head   # Enable O(n²) comparisons
```

## Why Vibe Code Bench?

Traditional coding benchmarks test narrow skills (syntax, algorithms). **Vibe Code Bench** tests what matters for real-world AI coding assistants:

- **End-to-end app generation** from natural language
- **Zero external dependencies** — stdlib only, no `pip install`
- **Single-file outputs** — HTML apps with embedded CSS/JS
- **Multi-judge arbitration** — 3 judges via OpenRouter reduce bias (V2)
- **Runtime validation** — Actually executes generated code (V2)

## Quick Start

```bash
# Install
pip install -e .

# Set API keys
cp .env.example .env
# Edit .env with your keys

# Run evaluation
python -m vibe_eval run -m claude-sonnet-4.5,llama-3.1-8b -c all
```

## Supported Models

| Provider | Models |
|----------|--------|
| **Anthropic** | `claude-opus-4.5`, `claude-sonnet-4.5`, `claude-sonnet-4`, `claude-haiku-4.5` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini` |
| **Google** | `gemini-2.0-flash`, `gemini-2.5-pro` |
| **OpenRouter** | `llama-3.1-8b`, `llama-3.1-70b`, any OpenRouter model |
| **Local** | `local` (LM Studio) |

## Evaluation Cases

20 carefully designed cases across 4 tiers:

### Tier 1: Modern Web Apps
| Case | Description |
|------|-------------|
| Pomodoro Timer | Work/break timer with notifications |
| Quiz App | Interactive quiz with scoring |
| Calculator | Full scientific calculator |
| Notes App | localStorage-based note taking |
| Weather Dashboard | Mock weather display |
| Kanban Board | Drag-and-drop task board |
| Stopwatch & Timer | Dual-mode time tracker |
| Typing Speed Test | WPM measurement game |
| Expense Tracker | Budget visualization |
| Memory Card Game | Matching pairs game |
| Color Palette Generator | Random palette with locking |
| Habit Tracker | Daily habit streaks |
| Password Generator | Secure password creation |
| Unit Converter | Multi-category conversions |
| Markdown Editor | Live preview editor |

### Tier 2: Developer Tools
| Case | Description |
|------|-------------|
| Repo Stats Infographic | Python → HTML stats dashboard |
| Legal Case Search | Professional document workspace |
| Slide Summary Reporter | Text → HTML report generator |
| Project Control Center | Glassmorphism dashboard UI |
| Log Analytics Dashboard | Python server with live charts |

**[See CASES.md](CASES.md)** for detailed requirements and scoring rubric.

## Scoring Dimensions (V2)

Each case is scored 0-100 across 5 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Executes** | 25% | Does the code actually run? (V2: increased from 15%) |
| **Features Complete** | 30% | Are all spec features implemented? |
| **Output Quality** | 20% | Does output match expectations? |
| **Direction Following** | 10% | Did it build exactly what was asked? |
| **Code Quality** | 15% | Readable, well-organized code? (V2: increased from 10%) |

**V2 Changes:** Elegance dimension removed (too subjective). Execution gate: if Executes < 3, total score capped at 30.

## CLI Commands

```bash
# List available cases
python -m vibe_eval list-cases

# Run specific cases
python -m vibe_eval run -m claude-sonnet-4.5 -c case_01_pomodoro,case_02_quiz

# Run all cases with custom timeout
python -m vibe_eval run -m llama-3.1-8b -c all -t 15

# View results dashboard
python -m vibe_eval dashboard results/TIMESTAMP_results.json

# Show leaderboard from previous run
python -m vibe_eval show results/TIMESTAMP_results.json
```

## Generating Reports

We include scripts to merge and average results across multiple runs:

```bash
# Merge split result files from a parallel run
python merge_run.py runs/run1 -o runs/run1_full.json

# Average multiple runs
python average_results.py runs/run1_full.json runs/run2_full.json -o final.json

# Generate Markdown report
python generate_report.py final.json -o REPORT.md
```

## Configuration

### Environment Variables

```bash
# V2: All judges use OpenRouter - only OPENROUTER_API_KEY required for judging
OPENROUTER_API_KEY=sk-or-...       # REQUIRED for judges + OpenRouter models

# Optional: For direct API access to models (bypasses OpenRouter)
ANTHROPIC_API_KEY=sk-ant-...       # For Claude models (direct)
OPENAI_API_KEY=sk-...              # For GPT models (direct)
GOOGLE_API_KEY=...                 # For Gemini models (direct)
LMSTUDIO_BASE_URL=http://localhost:1234/v1  # For local models
```

**Note:** V2 routes all judge calls through OpenRouter for unified billing. Set `OPENROUTER_API_KEY` to use multi-judge arbitration.

## Adding Custom Cases

Create a new folder in `eval_cases/`:

```
eval_cases/
└── case_21_myapp/
    └── spec.md          # Natural language task description
```

The `spec.md` should be a casual, human-style prompt like:

```markdown
# Build me a Recipe Book

I want a simple recipe organizer:
- Add recipes with ingredients and steps
- Search by name or ingredient
- Star my favorites
- Dark mode toggle

Single HTML file, save to localStorage.
```

## Benchmark Results (V1)
Full report: **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)**

| Rank | Model | Score (0-100) |
|------|-------|-------------------|
| 1 | `gpt-5.1-codex` | **87.4** |
| 2 | `claude-opus-4.5`* | **85.8** |
| 3 | `glm-4.7` | **85.3** |
| 4 | `claude-sonnet-4.5` | 84.4 |
| 5 | `gemini-3-flash` | 81.9 |
| ... | | |
| 12 | `llama-3.1-8b` | 25.3 |

*(Opus score impacted by content filtering on legal case)*

## Contributing

Contributions welcome! Areas of interest:
- New evaluation cases
- Additional model adapters
- Improved judging criteria
- UI for viewing generated apps

## License

MIT
