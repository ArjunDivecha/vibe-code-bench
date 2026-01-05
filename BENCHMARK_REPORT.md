# Vibe Code Bench V2 - Benchmark Report

**Evaluation Date:** January 4, 2026
**Framework Version:** V2 (Multi-Judge Arbitration with Execution Validation)
**Results File:** `results/20260104_122756_results.json`

---

## Executive Summary

This report presents the results of evaluating three LLMs on 20 "vibe coding" tasks - generating complete, self-contained applications from natural language prompts. The evaluation uses V2's multi-judge arbitration system with Claude Opus 4.5, GPT-4o, and Gemini 3 Flash as judges.

### Key Findings

| Metric | gpt-oss-120b | claude-sonnet-4.5 | gpt-4o |
|--------|--------------|-------------------|--------|
| **Average Score** | **71.0** | 69.6 | 51.0 |
| **Avg Response Time** | 58s | 79s | 23s |
| **LLM Cost** | $4.25 | $0.39 | $0.87 |
| **Judge Cost** | $0.90 | $1.53 | $0.65 |
| **Files Generated** | 31 | 28 | 20 |
| **Execution Failures** | 0 | 1 | 4 |

**Winner: gpt-oss-120b** with the highest average score of 71.0, demonstrating that open-source models can compete with and exceed proprietary models on vibe coding tasks.

---

## Evaluation Methodology

### V2 Scoring System

Scores are calculated using weighted dimensions (0-10 scale each):

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Executes | 25% | Code runs without errors |
| Features Complete | 30% | All requested features work |
| Output Quality | 20% | Visual polish and UX |
| Direction Following | 10% | Adherence to specifications |
| Code Quality | 15% | Clean, maintainable code |

**Execution Gate:** If code fails runtime validation, the score is capped at 30 (Executes = 2).

### Multi-Judge Arbitration

Three judges evaluate each submission independently:
- Claude Opus 4.5
- GPT-4o
- Gemini 3 Flash

Final scores are aggregated using majority voting with deviation penalties.

---

## Detailed Results

### Case-by-Case Scores

| Case | claude-sonnet-4.5 | gpt-4o | gpt-oss | Winner |
|------|-------------------|--------|---------|--------|
| 01_pomodoro | 77.5 | 71.5 | **79.5** | gpt-oss |
| 02_quiz | **79.5** | 72.0 | 78.0 | claude |
| 03_calculator | **82.5** | 66.0 | 77.5 | claude |
| 04_notes | **73.5** | 57.0 | 67.5 | claude |
| 05_weather | 76.0 | 48.0 | **76.0** | tie |
| 06_kanban | **75.5** | 63.0 | 65.0 | claude |
| 07_stopwatch | 65.0 | 62.0 | **65.0** | tie |
| 08_typing | 68.0 | 58.5 | **68.0** | tie |
| 09_expenses | **78.0** | 52.5 | 73.0 | claude |
| 10_memory | **82.5** | 66.0 | 78.0 | claude |
| 11_palette | **75.0** | 64.5 | 68.0 | claude |
| 12_habits | 70.0 | 0.0* | **78.0** | gpt-oss |
| 13_password | 66.5 | 59.0 | **76.0** | gpt-oss |
| 14_units | 66.5 | 58.0 | **69.0** | gpt-oss |
| 15_markdown | **69.0** | 55.0 | 65.5 | claude |
| 16_repostats | **75.5** | 30.0* | 73.5 | claude |
| 17_legal | 0.0* | **52.0** | 48.5 | gpt-4o |
| 18_slides | 75.0 | 0.0* | **79.5** | gpt-oss |
| 19_control_center | 66.5 | 56.0 | **69.0** | gpt-oss |
| 20_log_analytics | **70.0** | 30.0* | 65.5 | claude |

*\* Score of 0 or 30 indicates execution failure (capped by execution gate)*

### Win Distribution

| Model | Wins | Ties | Score > 70 |
|-------|------|------|------------|
| claude-sonnet-4.5 | 10 | 3 | 12 cases |
| gpt-oss-120b | 6 | 3 | 12 cases |
| gpt-4o | 1 | 0 | 2 cases |

---

## Model Analysis

### claude-sonnet-4.5

**Strengths:**
- Most consistent performer across cases (69.6 avg)
- Excellent code structure and organization
- Strong feature completeness (often 8-9/10)
- Most cost-effective ($0.39 LLM cost)

**Weaknesses:**
- One execution failure (case_17_legal - no files generated)
- Slower response times (79s average)
- Occasionally over-engineers solutions

**Best Cases:** calculator (82.5), memory (82.5), quiz (79.5)

### gpt-oss-120b (OpenAI Open Source)

**Strengths:**
- Highest average score (71.0)
- No execution failures when completed
- Excellent direction following (often 9/10)
- Strong on complex tasks (slides, control_center)

**Weaknesses:**
- Frequent timeouts (5 cases hit 50-turn limit)
- Very expensive ($4.25 LLM cost - 10x claude)
- Takes multiple turns to complete

**Best Cases:** pomodoro (79.5), slides (79.5), quiz (78.0)

### gpt-4o

**Strengths:**
- Fastest response times (23s average)
- Reliable on simple tasks
- Only model to solve case_17_legal

**Weaknesses:**
- Lowest average score (51.0)
- 4 execution failures (cases 12, 16, 18, 20)
- Struggled with Python cases
- Frequent timeout issues

**Best Cases:** pomodoro (71.5), quiz (72.0), calculator (66.0)

---

## Execution Validation Results

V2 introduced runtime validation for generated code:

| Model | Cases Validated | Execution Failures | Pass Rate |
|-------|-----------------|-------------------|-----------|
| claude-sonnet-4.5 | 20 | 1 | 95% |
| gpt-oss-120b | 20 | 0 | 100% |
| gpt-4o | 20 | 4 | 80% |

**Failure Reasons:**
- gpt-4o case_12: Script crashed on startup
- gpt-4o case_16: Missing dependencies in git analysis
- gpt-4o case_18: No .txt files generated for slides
- gpt-4o case_20: Script never completed (log server)
- claude case_17: No files generated (legal doc analyzer)

---

## Cost Analysis

### Total Evaluation Cost

| Category | Amount |
|----------|--------|
| LLM Inference | $5.52 |
| Judge Inference | $3.07 |
| **Total** | **$8.59** |

### Cost per Model

| Model | LLM Cost | Judge Cost | Total | Cost per Point |
|-------|----------|------------|-------|----------------|
| claude-sonnet-4.5 | $0.39 | $1.53 | $1.92 | $0.028/pt |
| gpt-4o | $0.87 | $0.65 | $1.52 | $0.030/pt |
| gpt-oss-120b | $4.25 | $0.90 | $5.15 | $0.073/pt |

**Most Cost-Efficient:** claude-sonnet-4.5 at $0.028 per score point

---

## Task Tier Analysis

### Tier 1: Web Applications (HTML/CSS/JS)
*Cases 1-15: Single-file web apps*

| Model | Avg Score | Pass Rate |
|-------|-----------|-----------|
| claude-sonnet-4.5 | 73.2 | 100% |
| gpt-oss-120b | 72.2 | 100% |
| gpt-4o | 56.4 | 87% |

### Tier 2: Developer Tools (Python stdlib)
*Cases 16-20: Python scripts with file I/O*

| Model | Avg Score | Pass Rate |
|-------|-----------|-----------|
| claude-sonnet-4.5 | 57.4 | 80% |
| gpt-oss-120b | 67.2 | 100% |
| gpt-4o | 33.6 | 40% |

**Key Finding:** gpt-oss excels at Python developer tools while gpt-4o struggles significantly with them.

---

## Recommendations

### For Users Choosing Models

1. **Best Overall:** gpt-oss-120b for highest quality, but be prepared for higher costs and occasional timeouts
2. **Best Value:** claude-sonnet-4.5 for excellent quality at 1/10th the cost
3. **Fastest Iteration:** gpt-4o for quick prototypes, but verify execution manually

### For Benchmark Improvements

1. Add more Python-heavy cases to better differentiate models
2. Consider adding a "cost-adjusted score" metric
3. Track token efficiency (score per 1K tokens)
4. Add streaming support to reduce perceived latency

---

## Appendix: Evaluation Configuration

```
Timeout: 20 minutes per case per model
Max Turns: 50 per model
Judge Panel: claude-opus-4.5, gpt-4o, gemini-3-flash
Validation: Python syntax + runtime, HTML browser validation
Scoring: V2 weighted dimensions with execution gate
```

---

## Historical Results (V1 Reference)

> **Note:** V1 used 6 dimensions including Elegance with different weights.
> V2 rebalanced to 5 dimensions with execution gate.

Previous V1 benchmark leaders (for reference):
1. openai/gpt-5.1-codex-max: 87.4
2. claude-opus-4.5: 85.8
3. z-ai/glm-4.7: 85.3

---

*Report generated by Vibe Code Bench V2*
*Multi-judge arbitration with execution validation*
