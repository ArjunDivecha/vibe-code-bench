# Vibe Code Bench V2 - 14-Model Benchmark Report

**Evaluation Date:** January 5, 2026
**Framework Version:** V2 (Multi-Judge Arbitration with Execution Validation)
**Results File:** `results/20260104_212554_results.json`

---

## Executive Summary

This report presents results from evaluating **14 frontier and open-source LLMs** on 20 "vibe coding" tasks - generating complete, self-contained applications from natural language prompts. V2 uses multi-judge arbitration with Claude Opus 4.5, GPT-4o, and Gemini 3 Flash as judges.

### Top 5 Results

| Rank | Model | Avg Score | Total Cost | Exec Failures |
|------|-------|-----------|------------|---------------|
| 🥇 1 | **z-ai/glm-4.7** | **74.2** | $0.11 | 0 |
| 🥈 2 | google/gemini-3-pro-preview | 74.2 | $1.80 | 0 |
| 🥉 3 | google/gemini-3-flash-preview | 72.6 | $0.20 | 0 |
| 4 | claude-opus-4.5 | 70.0 | $3.26 | 1 |
| 5 | openai/gpt-5.1-codex-max | 68.5 | $1.33 | 3 |

**Winner: z-ai/glm-4.7** - Tied with Gemini-3-Pro at 74.2 but at 1/16th the cost ($0.11 vs $1.80).

---

## Full Leaderboard

| Rank | Model | Score | Tokens | Cost | $/Point | Exec Fail |
|------|-------|-------|--------|------|---------|-----------|
| 1 | z-ai/glm-4.7 | 74.2 | 184K | $0.11 | $0.0015 | 0 |
| 2 | google/gemini-3-pro-preview | 74.2 | 157K | $1.80 | $0.0243 | 0 |
| 3 | google/gemini-3-flash-preview | 72.6 | 74K | $0.20 | $0.0028 | 0 |
| 4 | claude-opus-4.5 | 70.0 | 137K | $3.26 | $0.0465 | 1 |
| 5 | openai/gpt-5.1-codex-max | 68.5 | 218K | $1.33 | $0.0193 | 3 |
| 6 | claude-sonnet-4.5 | 67.0 | 146K | $1.91 | $0.0284 | 1 |
| 7 | openai/chatgpt-4o-latest | 66.5 | 43K | $0.56 | $0.0085 | 1 |
| 8 | gpt-oss | 66.0 | 2.2M | $2.38 | $0.0360 | 2 |
| 9 | moonshotai/kimi-k2-0905@Groq | 65.8 | 112K | $0.20 | $0.0030 | 1 |
| 10 | qwen/qwen3-235b-a22b-2507@Cerebras | 64.4 | 651K | $0.13 | $0.0020 | 2 |
| 11 | qwen/qwen3-coder | 63.0 | 92K | $0.08 | $0.0013 | 2 |
| 12 | minimax/minimax-m2.1 | 51.3 | 393K | $0.09 | $0.0018 | 5 |
| 13 | meta-llama/llama-3.1-8b-instruct@Cerebras | 29.7 | 334K | $0.01 | $0.0002 | 5 |
| 14 | anthropic/claude-haiku-4.5 | 25.1 | 236K | $0.96 | $0.0380 | 13 |

**Total LLM Inference Cost: $13.00**

---

## Scoring Methodology

### V2 Weighted Dimensions (100 point scale)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Executes | 25% | Code runs without errors |
| Features Complete | 30% | All requested features work |
| Output Quality | 20% | Visual polish and UX |
| Direction Following | 10% | Adherence to specifications |
| Code Quality | 15% | Clean, maintainable code |

**Execution Gate:** If code fails runtime validation, the score is capped at 30.

### Multi-Judge Arbitration

Three independent judges via OpenRouter:
- Claude Opus 4.5
- GPT-4o
- Gemini 3 Flash

Final scores use majority voting with deviation penalties.

---

## Case-by-Case Winners

| Case | Winner(s) | Score |
|------|-----------|-------|
| 01_pomodoro | claude-opus-4.5 | 85.5 |
| 02_quiz | minimax-m2.1 | 85.5 |
| 03_calculator | gpt-5.1-codex-max | 83.5 |
| 04_notes | gemini-3-pro-preview | 79.5 |
| 05_weather | claude-sonnet-4.5, gemini-3-flash, gemini-3-pro | 79.5 |
| 06_kanban | gpt-5.1-codex-max, gemini-3-pro-preview | 79.5 |
| 07_stopwatch | qwen3-coder | 75.0 |
| 08_typing | gpt-5.1-codex-max | 79.5 |
| 09_expenses | gpt-5.1-codex-max, qwen3-235b | 78.0 |
| 10_memory | gemini-3-pro-preview, minimax-m2.1 | 85.5 |
| 11_palette | gpt-5.1-codex-max, claude-opus-4.5, claude-sonnet-4.5 | 75.0 |
| 12_habits | gemini-3-pro-preview | 79.5 |
| 13_password | gpt-5.1-codex-max | 82.5 |
| 14_units | 7-way tie | 69.0 |
| 15_markdown | gemini-3-pro-preview | 76.0 |
| 16_repostats | gemini-3-pro-preview | 77.5 |
| 17_legal | gpt-5.1-codex-max | 75.5 |
| 18_slides | gemini-3-flash, gemini-3-pro, qwen3-coder | 78.0 |
| 19_control_center | gpt-5.1-codex-max | 75.0 |
| 20_log_analytics | glm-4.7 | 75.5 |

---

## Tier Analysis

### Tier 1: Web Applications (Cases 1-15)

| Rank | Model | Avg Score |
|------|-------|-----------|
| 1 | google/gemini-3-pro-preview | 75.6 |
| 2 | z-ai/glm-4.7 | 74.7 |
| 3 | google/gemini-3-flash-preview | 74.3 |
| 4 | claude-opus-4.5 | 74.0 |
| 5 | gpt-oss | 73.3 |

### Tier 2: Developer Tools - Python (Cases 16-20)

| Rank | Model | Avg Score |
|------|-------|-----------|
| 1 | z-ai/glm-4.7 | 72.9 |
| 2 | google/gemini-3-pro-preview | 70.1 |
| 3 | google/gemini-3-flash-preview | 67.6 |
| 4 | minimax/minimax-m2.1 | 65.6 |
| 5 | claude-sonnet-4.5 | 65.0 |

---

## Execution Validation Results

| Model | Pass Rate | Failures |
|-------|-----------|----------|
| z-ai/glm-4.7 | 100% | 0 |
| google/gemini-3-pro-preview | 100% | 0 |
| google/gemini-3-flash-preview | 100% | 0 |
| claude-opus-4.5 | 95% | 1 |
| claude-sonnet-4.5 | 95% | 1 |
| openai/chatgpt-4o-latest | 95% | 1 |
| moonshotai/kimi-k2-0905@Groq | 95% | 1 |
| gpt-oss | 90% | 2 |
| qwen/qwen3-235b-a22b-2507@Cerebras | 90% | 2 |
| qwen/qwen3-coder | 90% | 2 |
| openai/gpt-5.1-codex-max | 85% | 3 |
| minimax/minimax-m2.1 | 75% | 5 |
| meta-llama/llama-3.1-8b-instruct@Cerebras | 75% | 5 |
| **anthropic/claude-haiku-4.5** | **35%** | **13** |

---

## Cost Efficiency Rankings

*Sorted by points-per-dollar (higher is better)*

| Rank | Model | Score | Cost | Points/$ |
|------|-------|-------|------|----------|
| 1 | z-ai/glm-4.7 | 74.2 | $0.11 | 675 |
| 2 | qwen/qwen3-coder | 63.0 | $0.08 | 788 |
| 3 | qwen/qwen3-235b-a22b-2507@Cerebras | 64.4 | $0.13 | 495 |
| 4 | google/gemini-3-flash-preview | 72.6 | $0.20 | 363 |
| 5 | moonshotai/kimi-k2-0905@Groq | 65.8 | $0.20 | 329 |

---

## Key Findings

### 1. Chinese AI Models Excel
**z-ai/glm-4.7** tied for first place at a fraction of the cost. This Chinese model demonstrated:
- 100% execution success rate
- Best performance on Python developer tools (Tier 2)
- Extremely cost-effective at $0.0015 per point

### 2. Google Gemini Strong Performance
Both Gemini models performed excellently:
- **Gemini-3-Pro**: Tied for 1st (74.2), best on Tier 1 web apps
- **Gemini-3-Flash**: 3rd place (72.6) at just $0.20 total

### 3. Claude Haiku Severe Issues
**anthropic/claude-haiku-4.5** had catastrophic failures:
- 13 out of 20 cases failed execution validation
- Only 25.1 average score (last place)
- Likely a model behavior/configuration issue

### 4. gpt-oss Inefficient
Despite using 2.2M tokens (10x the average), gpt-oss only achieved 66.0 average:
- Very "chatty" - uses many turns to complete tasks
- High cost relative to performance ($2.38)

### 5. Cost vs Quality Trade-offs
| Category | Best Choice |
|----------|-------------|
| Best Overall | z-ai/glm-4.7 (74.2 @ $0.11) |
| Best Proprietary | claude-opus-4.5 (70.0 @ $3.26) |
| Best Budget | qwen/qwen3-coder (63.0 @ $0.08) |
| Most Reliable | GLM-4.7, Gemini (100% execution) |

---

## Recommendations

### For Users Choosing Models

1. **Best Overall Value**: z-ai/glm-4.7 - Top score at minimal cost
2. **Best Google Option**: gemini-3-flash-preview - Excellent balance of quality and speed
3. **Best Anthropic Option**: claude-opus-4.5 - Reliable but expensive
4. **Avoid**: claude-haiku-4.5 (severe execution issues), llama-3.1-8b (underpowered)

### For Production Use

1. Models with 100% execution pass rate: GLM-4.7, Gemini-3-Pro, Gemini-3-Flash
2. Add fallback logic for models with >90% pass rate
3. Consider multi-model approach: cheap model first, escalate to expensive on failure

---

## Appendix: Evaluation Configuration

```
Timeout: 20 minutes per case per model
Max Turns: 50 per model
Judge Panel: claude-opus-4.5, gpt-4o, gemini-3-flash
Validation: Python syntax + runtime, HTML browser validation
Scoring: V2 weighted dimensions with execution gate
Total Cases: 20 (15 web apps, 5 Python tools)
```

### OpenRouter Pricing Used (per 1M tokens)

| Model | Input | Output |
|-------|-------|--------|
| claude-opus-4.5 | $5.00 | $25.00 |
| claude-sonnet-4.5 | $3.00 | $15.00 |
| claude-haiku-4.5 | $1.00 | $5.00 |
| gpt-5.1-codex-max | $1.25 | $10.00 |
| chatgpt-4o-latest | $5.00 | $15.00 |
| gpt-oss-120b | $0.02 | $0.10 |
| gemini-3-flash-preview | $0.50 | $3.00 |
| gemini-3-pro-preview | $2.00 | $12.00 |
| glm-4.7 | $0.16 | $0.80 |
| kimi-k2-0905 | $0.39 | $1.90 |
| qwen3-coder | $0.22 | $0.95 |
| qwen3-235b | $0.071 | $0.463 |
| minimax-m2.1 | $0.12 | $0.48 |
| llama-3.1-8b | $0.02 | $0.03 |

---

*Report generated by Vibe Code Bench V2*
*Multi-judge arbitration with execution validation*
