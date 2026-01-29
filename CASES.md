# Evaluation Cases

This document describes all evaluation cases in the Vibe Code Bench benchmark. Each case tests an LLM's ability to build a complete, working application from a natural language prompt.

**Fast Suite (High-Signal Subset):**
This optional mode runs a smaller set of cases and a reduced test allowlist
to speed up evaluation while preserving differentiation.

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

**Constraints for all cases:**
- No package installations (`pip`, `npm`, etc.)
- Python stdlib only, or vanilla HTML/CSS/JS
- Single-file outputs preferred

---

## Tier 1: Simple Web Applications (Cases 1-15)

Expected score: 85-95 for frontier models. These establish a baseline.

### Case 01: Pomodoro Timer

**Goal:** Build a productivity timer implementing the Pomodoro Technique.

**Requirements:**
- 25-minute work sessions, 5-minute breaks
- Visual countdown with progress indicator
- Audio notification when timer completes
- Start/Pause/Reset controls
- Session counter (work sessions completed)
- Automatic switching between work and break
- Tomato-red theme aesthetic

**Output:** Single HTML file

---

### Case 02: Quiz App

**Goal:** Build an interactive quiz application.

**Requirements:**
- Multiple choice questions (4 options each)
- At least 5 sample questions built-in
- Score tracking (correct/total)
- Immediate feedback on answer selection
- Final results screen with percentage
- "Try Again" functionality
- Clean, engaging design

**Output:** Single HTML file

---

### Case 03: Calculator

**Goal:** Build a fully functional calculator.

**Requirements:**
- Basic operations: +, -, ×, ÷
- Decimal support
- Clear and backspace
- Keyboard input support
- Calculation history display
- Percentage calculations
- Responsive button grid layout

**Output:** Single HTML file

---

### Case 04: Notes App

**Goal:** Build a note-taking application with persistence.

**Requirements:**
- Create, edit, delete notes
- localStorage persistence
- Search/filter functionality
- Timestamps on notes
- Markdown support (optional)
- Clean, minimal interface
- Mobile-responsive

**Output:** Single HTML file

---

### Case 05: Weather Dashboard

**Goal:** Build a weather display with mock data.

**Requirements:**
- Display current conditions (temp, humidity, wind)
- 5-day forecast view
- Weather icons (can use emoji or CSS)
- Multiple city selection (mock data for 3-5 cities)
- Responsive card-based layout
- Smooth transitions between cities
- No external API calls required

**Output:** Single HTML file

---

### Case 06: Kanban Board

**Goal:** Build a task management board.

**Requirements:**
- Three columns: To Do, In Progress, Done
- Add new cards with title/description
- Drag-and-drop between columns
- Delete cards
- localStorage persistence
- Card editing
- Visual feedback during drag

**Output:** Single HTML file

---

### Case 07: Stopwatch & Timer

**Goal:** Build a dual-mode time tracking tool.

**Requirements:**
- Stopwatch mode: start, stop, lap, reset
- Timer mode: set custom duration, countdown
- Lap time recording with splits
- Audio alert when timer completes
- Large, readable display
- Clean toggle between modes
- Pause/resume functionality

**Output:** Single HTML file

---

### Case 08: Typing Speed Test

**Goal:** Build a WPM measurement application.

**Requirements:**
- Sample text paragraphs to type
- Real-time WPM calculation
- Accuracy percentage
- Visual highlighting of current position
- Error indication (wrong characters)
- Results summary at completion
- Multiple difficulty levels or texts

**Output:** Single HTML file

---

### Case 09: Expense Tracker

**Goal:** Build a personal finance tracker.

**Requirements:**
- Add expenses with amount, category, date
- Category breakdown (food, transport, etc.)
- Monthly summary view
- Visual chart (pie or bar)
- Delete/edit entries
- localStorage persistence
- Budget vs actual comparison

**Output:** Single HTML file

---

### Case 10: Memory Card Game

**Goal:** Build a matching pairs game.

**Requirements:**
- Grid of face-down cards (4x4 or larger)
- Flip animation on click
- Match detection and removal
- Move counter
- Timer
- Win condition with celebration
- Restart functionality

**Output:** Single HTML file

---

### Case 11: Color Palette Generator

**Goal:** Build a color palette creation tool.

**Requirements:**
- Generate 5-color palettes randomly
- Click to copy hex code
- Lock individual colors
- Spacebar to regenerate unlocked
- Show hex + RGB values
- Save favorite palettes to localStorage
- Smooth color transitions

**Output:** Single HTML file

---

### Case 12: Habit Tracker

**Goal:** Build a daily habit tracking app.

**Requirements:**
- Add/remove habits
- Daily check-off for each habit
- Calendar/grid view of past 30 days
- Streak counter per habit
- Completion percentage
- localStorage persistence
- Motivating visual design

**Output:** Single HTML file

---

### Case 13: Password Generator

**Goal:** Build a secure password creation tool.

**Requirements:**
- Length slider (8-32 characters)
- Toggle options: uppercase, lowercase, numbers, symbols
- Password strength meter
- Copy to clipboard button
- Generate multiple passwords at once
- History of recent passwords
- Regenerate on button click

**Output:** Single HTML file

---

### Case 14: Unit Converter

**Goal:** Build a multi-category conversion tool.

**Requirements:**
- Categories: Length, Weight, Temperature, Volume, Time
- Multiple units per category
- Real-time conversion as you type
- Swap button to reverse direction
- Show conversion formula used
- Quick-access common conversions
- Clean, responsive layout

**Output:** Single HTML file

---

### Case 15: Markdown Editor

**Goal:** Build a split-pane markdown editor.

**Requirements:**
- Left pane: markdown input
- Right pane: live HTML preview
- Support: headers, bold, italic, lists, links, code blocks, blockquotes
- Save/load from localStorage
- Export as HTML button
- Dark mode toggle
- Synced scrolling (optional)

**Output:** Single HTML file

---

## Tier 2: Developer Tools (Cases 16-20)

### Case 16: Repository Stats Infographic

**Goal:** Build a Python tool that scans a codebase and generates a visual HTML report.

**Requirements:**
- Recursively scan current directory
- Calculate: file count by extension, total lines, largest files, directory depth
- Generate beautiful HTML infographic
- Use inline SVG for charts (pie chart, bar chart)
- Dark mode aesthetic with vibrant colors
- Title: "Codebase Fingerprint"

**Output:** Python script → HTML file

**Constraints:** Python stdlib only (os, pathlib, json, etc.)

---

### Case 17: Legal Case Search Workspace

**Goal:** Build a professional legal research interface.

**Requirements:**
- Search bar for case queries
- Results list with: case title, court, date, preview snippet
- Detail view (split pane or modal)
- Summary tab and Full Text tab
- "Extract Entities" button (simulated highlighting)
- Notes sidebar with localStorage
- Professional dark mode ("legal" aesthetic)

**Output:** Single HTML file with 10-15 mock cases

---

### Case 18: Slide Summary Reporter

**Goal:** Build a Python tool that converts text slides to an HTML report.

**Requirements:**
- Read all `.txt` files from a directory (slide1.txt, slide2.txt, etc.)
- Generate HTML report with each slide as a "card"
- Auto-generate Table of Contents
- Summary section combining first lines
- Premium CSS (typography, shadows, spacing)
- Print-friendly with page breaks
- "Print to PDF" button

**Output:** Python script → HTML file

**Constraints:** Python stdlib only

---

### Case 19: Project Control Center

**Goal:** Build a high-end dashboard that looks like a native desktop app.

**Requirements:**
- Glassmorphism aesthetic (blur, transparency)
- Vertical sidebar with navigation
- Widgets: Active Projects (with progress bars), Recent Activity (timeline), Quick Links (icon grid), Task List (checkboxes)
- Sidebar switches views without page reload
- "New Project" modal
- localStorage for tasks
- Smooth micro-animations

**Output:** Single HTML file

---

### Case 20: Log Analytics Dashboard

**Goal:** Build a Python tool that analyzes logs and serves a dashboard.

**Requirements:**
- Check for `server.log`; if missing, generate 1000 fake log lines
- Parse log levels: INFO, WARN, ERROR, CRITICAL
- Calculate: percentage by level, errors per hour, common messages
- Launch local HTTP server (using `http.server`)
- Serve interactive dashboard with SVG charts
- Searchable table of CRITICAL errors
- Filter by log level

**Output:** Python script that runs a web server

**Constraints:** Python stdlib only (`http.server`, `json`, `collections`)

---

## Tier 2: Complex Applications (Cases 21-25)

These cases require proper architecture and are designed to discriminate between top-tier models.

### Case 21: Spreadsheet

**Goal:** Build a basic spreadsheet with formula support.

**Requirements:**
- 10+ columns (A-J), 20+ rows grid
- Cell selection and editing
- Formula support: `=5+3`, `=A1+B1`, `=SUM(A1:A5)`
- Formula bar showing actual formula
- Cell references that recalculate

**Output:** Single HTML file

---

### Case 22: Flowchart Editor

**Goal:** Build a visual flowchart/diagram editor.

**Requirements:**
- Canvas workspace with shape palette
- Shapes: Rectangle, Diamond, Oval, Parallelogram
- Drag-drop shapes onto canvas
- Connect shapes with arrow lines
- Double-click to edit text labels

**Output:** Single HTML file (SVG or Canvas)

---

### Case 23: Rich Text Editor

**Goal:** Build a WYSIWYG text editor.

**Requirements:**
- Formatting: Bold, Italic, Underline, Headings
- Lists (bullet and numbered)
- Undo/Redo support
- Keyboard shortcuts (Ctrl+B, Ctrl+I)

**Output:** Single HTML file (contenteditable)

---

### Case 24: File Browser

**Goal:** Build a virtual file browser interface.

**Requirements:**
- Folder tree sidebar
- File listing with icons
- Breadcrumb navigation
- Mock file system with nested folders

**Output:** Single HTML file

---

### Case 25: Data Visualization Dashboard

**Goal:** Build an interactive chart dashboard.

**Requirements:**
- Bar chart, Line chart, Pie chart (SVG, no libraries)
- Hover tooltips
- Legend with click-to-filter
- Date range or category filters

**Output:** Single HTML file

---

## Tier 3: Agentic Tasks (Cases 31-35)

These cases test multi-step workflows, tool use, error recovery, and iteration.

### Case 31: API Integration

**Goal:** Build a CLI tool that integrates with the Open-Meteo weather API.

**Requirements:**
- Fetch weather data using urllib (no requests)
- Geocoding to convert city names
- CLI with `current` and `forecast` commands
- Proper error handling

**Output:** Python script (stdlib only)

---

### Case 32: Debug Session

**Goal:** Fix a broken Todo app with 5 bugs.

**Requirements:**
- Identify and fix all bugs
- Document fixes in FIXES.md
- All functionality working after fixes

**Output:** Fixed HTML file + FIXES.md

---

### Case 33: Refactor

**Goal:** Split a monolithic Python script into a proper package.

**Requirements:**
- Create `inventory/` package with modules
- Separate: models, storage, manager, reports, cli
- No functionality changes
- Clean imports, no circular dependencies

**Output:** Python package structure

---

### Case 34: Test-Driven Development

**Goal:** Implement code to make all provided tests pass.

**Requirements:**
- Create `calculator.py` from `test_calculator.py`
- All 10 tests must pass
- Method chaining, error handling

**Output:** Python file passing tests

---

### Case 35: Data Pipeline

**Goal:** Build a multi-step data processing pipeline.

**Requirements:**
- Read CSV, validate, transform, aggregate
- Output: valid_employees.json, invalid_records.json, department_summary.json
- Proper error validation

**Output:** Python script + output files

---

## Scoring Rubric

Each case is scored 0-100 across 5 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Executes | 25% | Does the code run without errors? |
| Features Complete | 30% | Are all specified features implemented? |
| Output Quality | 20% | Does output match expectations? |
| Direction Following | 10% | Did it build exactly what was asked? |
| Code Quality | 15% | Is code readable and well-organized? |

**Execution gate:** If `executes < 3`, total score is capped at 30 points.

**Judging:** Multi-judge arbitration by default (Claude Opus 4.5, GPT-4o, Gemini 3 Flash Preview via OpenRouter). All judges use the same OpenRouter API key.
