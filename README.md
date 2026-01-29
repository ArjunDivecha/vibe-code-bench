# Vibe Code Bench

> **Evaluate LLMs on "Vibe Coding" — building complete apps from natural language prompts.**

Vibe Code Bench is a framework for testing how well AI models can take casual, human-style prompts ("Build me a Pomodoro timer") and produce **fully working, self-contained applications** without installing any external packages.

## V3 Updates (2026-01-27)

- **Tiered Case Structure** - 30 cases across 3 tiers (Simple, Complex, Agentic)
- **Functional Test Suites** - Automated Playwright-based tests for objective scoring
- **Enhanced Agent Loop** - New tools: read_file, run_tests, lint_code, web_search
- **Detailed Agent Metrics** - Track turns, tool calls, errors, backtracks, test iterations
- **New Scoring Module** - Auto scorer (tests) + Static analyzer + Judge aggregator
- **8 Scoring Dimensions** - Added test_pass_rate, edge_cases, efficiency, robustness

## Why Vibe Code Bench?

Traditional coding benchmarks test narrow skills (syntax, algorithms). **Vibe Code Bench** tests what matters for real-world AI coding assistants:

- **End-to-end app generation** from natural language
- **Zero external dependencies** — stdlib only, no `pip install`
- **Single-file outputs** — HTML apps with embedded CSS/JS
- **Multi-judge arbitration** — 3 judges via OpenRouter reduce bias
- **Runtime validation** — Actually executes generated code
- **Functional tests** — Objective pass/fail metrics (V3)
- **Agentic evaluation** — Multi-step tasks with tool use (V3)

## Quick Start

```bash
# Install
pip install -e .

# Set API keys
cp .env.example .env
# Edit .env with your keys (OPENROUTER_API_KEY required)

# Run evaluation
python -m vibe_eval run -m claude-sonnet-4.5,gpt-4o -c all

# List all 30 cases
python -m vibe_eval list-cases
```

## Supported Models

| Provider | Models |
|----------|--------|
| **Anthropic** | `claude-opus-4.5`, `claude-sonnet-4.5`, `claude-sonnet-4`, `claude-haiku-4.5` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini` |
| **Google** | `gemini-2.0-flash`, `gemini-2.5-pro` |
| **Moonshot** | `kimi-k2.5` (via OpenRouter) |
| **OpenRouter** | `llama-3.1-8b`, `llama-3.1-70b`, any OpenRouter model |
| **Local** | `local` (LM Studio) |

## Evaluation Cases (30 Total)

### Tier 1: Simple Web Apps (Cases 1-15)
Baseline tasks - all frontier models should score 85-95.

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

### Tier 1b: Developer Tools (Cases 16-20)
| Case | Description |
|------|-------------|
| Repo Stats Infographic | Python → HTML stats dashboard |
| Legal Case Search | Professional document workspace |
| Slide Summary Reporter | Text → HTML report generator |
| Project Control Center | Glassmorphism dashboard UI |
| Log Analytics Dashboard | Python server with live charts |

### Tier 2: Complex Applications (Cases 21-25) - NEW
Multi-feature apps requiring proper architecture - designed to discriminate between top models.

| Case | Description | Discriminating Factors |
|------|-------------|------------------------|
| Spreadsheet | Basic spreadsheet with formulas | Formula parsing, cell references, A1 notation |
| Flowchart Editor | Drag-drop diagram editor | SVG manipulation, connection lines, state |
| Rich Text Editor | WYSIWYG text editor | contentEditable, formatting, undo/redo |
| File Browser | Virtual file system UI | Tree structure, breadcrumbs, navigation |
| Data Viz Dashboard | Interactive charts | SVG charts, filtering, responsive layout |

### Tier 3: Agentic Tasks (Cases 31-35) - NEW
Multi-step tasks requiring planning, tool use, and iteration.

| Case | Description | Agentic Factors |
|------|-------------|-----------------|
| API Integration | Weather CLI with real API | urllib, geocoding, error handling |
| Debug Session | Fix 5 bugs in broken app | Error analysis, targeted fixes |
| Refactor | Split monolith into modules | Multi-file coordination, imports |
| Test-Driven Dev | Implement to pass tests | Red-green-refactor loop |
| Data Pipeline | Build ETL from spec | Multi-step data processing |

**[See CASES.md](CASES.md)** for detailed requirements and scoring rubric.

## Scoring System (V3)

### Dimensions (8 total)

| Dimension | Weight | Source | Description |
|-----------|--------|--------|-------------|
| **Executes** | 15% | Validator | Code runs without errors |
| **Test Pass Rate** | 20% | Auto | Functional tests passing |
| **Features Complete** | 20% | Judge | All spec features implemented |
| **Edge Cases** | 10% | Combined | Handles errors, validation |
| **Code Quality** | 10% | Static+Judge | Readable, well-organized |
| **Efficiency** | 5% | Metrics | Minimal turns, smart tool use |
| **Direction Following** | 10% | Judge | Built exactly what was asked |
| **Robustness** | 10% | Tests | Works across scenarios |

### Execution Gate
If `executes < 3` OR `test_pass_rate < 2`, total score is capped at 30.

### Scoring Sources
- **Auto Scorer**: Runs functional tests, calculates pass rate
- **Static Analyzer**: Code complexity, docstrings, error handling
- **Multi-Judge**: LLM evaluation (Claude Opus, GPT-4o, Gemini Flash)
- **Aggregator**: Combines all sources with dimension weights

Fast suite uses V3 weights with higher test emphasis and a small speed
efficiency component to reward faster runtimes.

### Fast Suite Mode
The fast suite uses a high-signal subset of cases and a smaller test allowlist
per case. It also uses shorter timeouts and fast-fail validation to reduce
runtime while preserving differentiation.

Fast suite cases:
- case_03_calculator
- case_04_notes
- case_07_stopwatch
- case_08_typing
- case_11_palette
- case_15_markdown
- case_21_spreadsheet
- case_22_flowchart
- case_23_richtext
- case_25_dataviz
- case_31_api_integration
- case_33_refactor

## CLI Commands

```bash
# List all 30 cases
python -m vibe_eval list-cases

# Run specific cases
python -m vibe_eval run -m claude-sonnet-4.5 -c case_01_pomodoro,case_21_spreadsheet

# Run all cases with custom timeout
python -m vibe_eval run -m claude-opus-4.5,gpt-4o -c all -t 15

# V3 options
python -m vibe_eval run -m gpt-4o -c all                  # Multi-judge + tests (default)
python -m vibe_eval run -m gpt-4o -c all --single-judge   # Single judge mode
python -m vibe_eval run -m gpt-4o -c all --no-validation  # Skip execution validation
python -m vibe_eval run -m gpt-4o -c all --suite fast     # Fast suite (high-signal subset)

# View results
python -m vibe_eval dashboard results/TIMESTAMP_results.json
python -m vibe_eval show results/TIMESTAMP_results.json

# Generate differentiation diagnostics
python -m vibe_eval diagnose --results-dir results --output-dir reports

# Generate benchmark report with differentiation summary
python generate_report.py results/TIMESTAMP_results.json -o BENCHMARK_REPORT.md
```

## Agent Tools (V3)

The agent loop now supports expanded tools:

| Tool | Description |
|------|-------------|
| `write_file` | Create or edit files |
| `read_file` | Read existing files |
| `list_files` | List directory contents |
| `run_command` | Execute shell commands |
| `run_tests` | Execute test suite |
| `lint_code` | Check code for errors |
| `web_search` | Search documentation (simulated) |
| `done` | Signal completion |

## Agent Metrics (V3)

Detailed tracking for agentic evaluation:

```python
@dataclass
class AgentMetrics:
    turns: int
    tool_calls: list[dict]
    errors_encountered: int
    errors_recovered: int
    backtrack_count: int      # Revisions to previous work
    planning_turns: int       # Turns spent planning
    test_iterations: int      # Times tests were run
    files_written: int
    files_read: int
    commands_run: int
```

## Configuration

### Environment Variables

```bash
# REQUIRED: For judges + OpenRouter models
OPENROUTER_API_KEY=sk-or-...

# Optional: Direct API access (bypasses OpenRouter)
ANTHROPIC_API_KEY=sk-ant-...       # For Claude models
OPENAI_API_KEY=sk-...              # For GPT models
GOOGLE_API_KEY=...                 # For Gemini models
LMSTUDIO_BASE_URL=http://localhost:1234/v1  # Local models
```

## Project Structure (V3)

```
vibe_eval/
├── agent_loop.py          # Enhanced with tools + metrics
├── tools/                  # Tool implementations
│   ├── file_tools.py      # read_file, list_files
│   ├── test_tools.py      # run_tests, lint_code
│   └── search_tools.py    # web_search
├── scoring/                # V3 scoring system
│   ├── auto_scorer.py     # Functional test scoring
│   ├── static_scorer.py   # Code quality metrics
│   └── aggregator.py      # Combines all scores
├── sandbox/
│   ├── executor.py        # Code execution
│   ├── validator.py       # Execution validation
│   └── test_runner.py     # Functional test runner
├── judge/
│   ├── absolute.py        # Single judge
│   └── multi_judge.py     # Multi-judge arbitration
├── models/                 # Model adapters
├── runner.py              # Main orchestration
└── cli.py                 # CLI interface

eval_cases/
├── case_01_pomodoro/
│   ├── spec.md            # Task specification
│   └── tests.py           # Functional tests
├── case_21_spreadsheet/   # Tier 2 complex
├── case_31_api_integration/  # Tier 3 agentic
└── ...
```

## Adding Custom Cases

Create a new folder in `eval_cases/`:

```
eval_cases/
└── case_XX_myapp/
    ├── spec.md          # Natural language task description
    └── tests.py         # Functional tests (optional but recommended)
```

Example `tests.py`:

```python
def test_has_start_button(page):
    """Should have a visible start button."""
    btn = page.locator("button:has-text('Start')")
    assert btn.count() > 0, "No start button found"

def test_timer_counts_down(page):
    """Clicking start should begin countdown."""
    page.locator("button:has-text('Start')").click()
    page.wait_for_timeout(1500)
    content = page.locator("body").text_content()
    assert "24:5" in content, "Timer not counting down"
```

## Generating Reports

```bash
# Merge split result files
python merge_run.py runs/run1 -o runs/run1_full.json

# Average multiple runs
python average_results.py runs/run1.json runs/run2.json -o final.json

# Generate Markdown report
python generate_report.py final.json -o REPORT.md
```

## Contributing

Contributions welcome! Areas of interest:
- New evaluation cases with tests
- Additional model adapters
- Improved functional tests
- Agentic task designs
- UI for viewing generated apps

## License

MIT
