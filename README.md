# Vibe Code Bench 🎨

> **Evaluate LLMs on "Vibe Coding" — building complete apps from natural language prompts.**

Vibe Code Bench is a framework for testing how well AI models can take casual, human-style prompts ("Build me a Pomodoro timer") and produce **fully working, self-contained applications** without installing any external packages.

## ✨ Why Vibe Code Bench?

Traditional coding benchmarks test narrow skills (syntax, algorithms). **Vibe Code Bench** tests what matters for real-world AI coding assistants:

- 🎯 **End-to-end app generation** from natural language
- 🚫 **Zero external dependencies** — stdlib only, no `pip install`
- 📄 **Single-file outputs** — HTML apps with embedded CSS/JS
- ⚖️ **Automated judging** by Claude Opus with detailed scoring
- 📊 **Head-to-head comparisons** across multiple models

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Set API keys
cp .env.example .env
# Edit .env with your keys

# Run evaluation
python -m vibe_eval run -m claude-sonnet-4.5,llama-3.1-8b -c all
```

## 📦 Supported Models

| Provider | Models |
|----------|--------|
| **Anthropic** | `claude-opus-4.5`, `claude-sonnet-4.5`, `claude-sonnet-4`, `claude-haiku-4.5` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini` |
| **Google** | `gemini-2.0-flash`, `gemini-2.5-pro` |
| **OpenRouter** | `llama-3.1-8b`, `llama-3.1-70b`, any OpenRouter model |
| **Local** | `local` (LM Studio) |

## 📋 Evaluation Cases

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

📄 **[See CASES.md](CASES.md)** for detailed requirements and scoring rubric.

## 🎯 Scoring Dimensions

Each case is scored 0-100 across 6 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Executes** | 15% | Does the code actually run? |
| **Features Complete** | 30% | Are all spec features implemented? |
| **Output Quality** | 25% | Does output match expectations? |
| **Direction Following** | 15% | Did it build exactly what was asked? |
| **Code Quality** | 10% | Readable, well-organized code? |
| **Elegance** | 5% | Clever or particularly clean design? |

## 📊 CLI Commands

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

## 🔧 Configuration

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...      # For Claude models
OPENAI_API_KEY=sk-...              # For GPT models
GOOGLE_API_KEY=...                 # For Gemini models
OPENROUTER_API_KEY=sk-or-...       # For OpenRouter (Llama, etc.)
LMSTUDIO_BASE_URL=http://localhost:1234/v1  # For local models
```

## 🏗️ Adding Custom Cases

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

## 📈 Sample Results

From our benchmark run (Claude Sonnet 4.5 vs Llama 3.1 8B):

| Metric | Llama 3.1 8B | Claude Sonnet 4.5 |
|--------|--------------|-------------------|
| Avg Score | 26.8 | **87.8** |
| Generation Time | **18s** | 25 min |
| Cost | **<$0.01** | ~$1.20 |

## 🤝 Contributing

Contributions welcome! Areas of interest:
- New evaluation cases
- Additional model adapters
- Improved judging criteria
- UI for viewing generated apps

## 📄 License

MIT
