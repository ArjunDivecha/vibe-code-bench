#!/usr/bin/env python3
"""
Slide Summary Reporter

Reads .txt files in a directory, builds a premium-looking HTML report with:
- Summary section aggregating key lines from each slide
- Table of contents with links
- Individual slide cards with clean typography
- Print to PDF button (window.print)
Usage:
    python slide_reporter.py               # scans current directory
    python slide_reporter.py /path/to/dir  # scans provided directory
"""
import sys
import os
import re
import datetime
from html import escape
from typing import List, Dict, Tuple


def natural_key(text: str) -> List:
    """Split text into list of ints and strs to support natural sorting."""
    parts = re.split(r'(\d+)', text)
    key = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p.lower())
    return key


def collect_slides(folder: str) -> List[Dict[str, str]]:
    slides = []
    for entry in os.listdir(folder):
        if not entry.lower().endswith(".txt"):
            continue
        path = os.path.join(folder, entry)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        lines = [line.strip() for line in content.splitlines()]
        title = next((ln for ln in lines if ln), os.path.splitext(entry)[0])
        slides.append({
            "filename": entry,
            "path": path,
            "title": title,
            "content": content
        })
    slides.sort(key=lambda s: natural_key(s["filename"]))
    return slides


def make_summary(lines: List[str], max_lines: int = 2, max_chars: int = 220) -> str:
    """Build a compact summary snippet from the first non-empty lines."""
    filtered = [ln for ln in lines if ln.strip()]
    snippet_lines = filtered[:max_lines]
    snippet = " — ".join(snippet_lines)
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1].rstrip() + "…"
    return snippet if snippet else "(No content)"


def build_html(slides: List[Dict[str, str]], generated_on: str) -> str:
    summary_items = []
    for idx, slide in enumerate(slides, 1):
        lines = slide["content"].splitlines()
        snippet = make_summary(lines)
        summary_items.append((idx, slide["title"], snippet))

    toc_items = [(idx, slide["title"]) for idx, slide in enumerate(slides, 1)]

    slide_cards = []
    for idx, slide in enumerate(slides, 1):
        slide_html = f"""
        <section class="card" id="slide-{idx}">
            <div class="card-header">
                <div class="chip">Slide {idx}</div>
                <div class="filename">{escape(slide["filename"])}</div>
            </div>
            <h2>{escape(slide["title"])}</h2>
            <pre>{escape(slide["content"])}</pre>
        </section>
        """
        slide_cards.append(slide_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Slide Summary Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {{
    --bg: #f4f6fb;
    --card-bg: #ffffff;
    --primary: #1f4b99;
    --accent: #7b5bff;
    --muted: #5f6b81;
    --shadow: 0 16px 40px rgba(0,0,0,0.08);
    --radius: 16px;
    --mono: "SFMono-Regular", "Menlo", "Consolas", "Liberation Mono", monospace;
    --sans: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}}

* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 0;
    font-family: var(--sans);
    color: #1f2a44;
    background: radial-gradient(circle at 20% 20%, rgba(123,91,255,0.08), transparent 40%),
                radial-gradient(circle at 80% 10%, rgba(31,75,153,0.08), transparent 35%),
                var(--bg);
}}
.wrapper {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 32px 20px 64px 20px;
}}
header {{
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
}}
h1 {{
    margin: 0;
    font-size: 32px;
    letter-spacing: -0.5px;
}}
button#print {{
    background: linear-gradient(135deg, var(--primary), var(--accent));
    border: none;
    color: white;
    padding: 12px 18px;
    border-radius: 12px;
    font-size: 15px;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(31,75,153,0.25);
    transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.2s ease;
}
button#print:hover {{ transform: translateY(-2px); box-shadow: 0 16px 34px rgba(31,75,153,0.35); }}
button#print:active {{ transform: translateY(0); opacity: 0.9; }}
.meta {{
    color: var(--muted);
    font-size: 14px;
    margin-top: 4px;
}}
.panel {{
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 20px;
    box-shadow: var(--shadow);
    margin-bottom: 18px;
}}
.panel h2 {{
    margin-top: 0;
    color: var(--primary);
    font-size: 20px;
    letter-spacing: -0.2px;
}}
.panel ul {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.panel ul li {{
    padding: 10px 12px;
    border-radius: 12px;
    transition: background 0.15s ease;
}}
.panel ul li:hover {{ background: rgba(31,75,153,0.07); }}
.panel a {{
    text-decoration: none;
    color: inherit;
    font-weight: 600;
}}
.panel .snippet {{
    color: var(--muted);
    font-weight: 400;
    display: block;
    margin-top: 4px;
    line-height: 1.4;
}}
.card {{
    background: var(--card-bg);
    border-radius: 18px;
    padding: 22px 22px 26px 22px;
    margin: 22px 0;
    box-shadow: var(--shadow);
    page-break-inside: avoid;
    break-inside: avoid;
}}
.card-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    color: var(--muted);
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}}
.chip {{
    background: rgba(123,91,255,0.1);
    color: var(--accent);
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.4px;
}}
.filename {{ font-family: var(--mono); }}
.card h2 {{
    margin: 8px 0 12px 0;
    font-size: 22px;
    color: #0f1933;
}}
pre {{
    background: #0b1224;
    color: #e6ecff;
    border-radius: 14px;
    padding: 16px;
    overflow-x: auto;
    font-family: var(--mono);
    font-size: 14px;
    line-height: 1.55;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
}}
.summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 10px;
}}
.summary-item {{
    background: rgba(255,255,255,0.7);
    border-radius: 12px;
    padding: 14px;
    border: 1px solid rgba(31,75,153,0.08);
}}
.summary-item .label {{
    font-size: 12px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.3px;
}}
.summary-item .text {{
    margin-top: 6px;
    font-weight: 600;
    line-height: 1.4;
}}
@media print {{
    body {{ background: white; }}
    button#print {{ display: none; }}
    .wrapper {{ padding: 0; }}
    .card {{ box-shadow: none; border: 1px solid #ddd; page-break-inside: avoid; break-inside: avoid; }}
    .panel {{ box-shadow: none; border: 1px solid #ddd; }}
}}
</style>
</head>
<body>
<div class="wrapper">
    <header>
        <div>
            <h1>Slide Summary Report</h1>
            <div class="meta">Generated on {escape(generated_on)} • {len(slides)} slides</div>
        </div>
        <button id="print" onclick="window.print()">Print to PDF</button>
    </header>

    <div class="panel" id="summary">
        <h2>Summary Snapshot</h2>
        <div class="summary-grid">
            {''.join(f'<div class="summary-item"><div class="label">Slide {idx}: {escape(title)}</div><div class="text">{escape(snippet)}</div></div>' for idx, title, snippet in summary_items)}
        </div>
    </div>

    <div class="panel" id="toc">
        <h2>Table of Contents</h2>
        <ul>
            {''.join(f'<li><a href="#slide-{idx}">Slide {idx}: {escape(title)}</a></li>' for idx, title in toc_items)}
        </ul>
    </div>

    {''.join(slide_cards)}
</div>
</body>
</html>
"""
    return html


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a directory", file=sys.stderr)
        sys.exit(1)

    slides = collect_slides(folder)
    if not slides:
        print("No .txt slide files found in the directory.", file=sys.stderr)
        sys.exit(1)

    generated_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = build_html(slides, generated_on)
    out_path = os.path.join(folder, "report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report created: {out_path}")


if __name__ == "__main__":
    main()