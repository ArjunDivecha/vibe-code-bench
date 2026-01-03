import argparse
import datetime
import html
import os
import re
import sys
from typing import List, Dict


def natural_key(s: str):
    """
    Turn a string into a list of strings and ints to allow natural sorting.
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def collect_slides(directory: str) -> List[Dict]:
    slides = []
    for name in os.listdir(directory):
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        slides.append({
            "filename": name,
            "title": os.path.splitext(name)[0],
            "lines": lines,
        })
    slides.sort(key=lambda x: natural_key(x["filename"]))
    return slides


def format_slide_content(lines: List[str]) -> str:
    parts = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if in_list:
                parts.append("</ul>")
                in_list = False
            continue
        if stripped.startswith(("-", "*", "•")):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            item_text = stripped.lstrip("-*• ").strip()
            parts.append(f"<li>{html.escape(item_text)}</li>")
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{html.escape(stripped)}</p>")
    if in_list:
        parts.append("</ul>")
    if not parts:
        parts.append("<p><em>(No content)</em></p>")
    return "\n".join(parts)


def build_summary(slides: List[Dict], lines_per_slide: int) -> str:
    bullets = []
    for idx, slide in enumerate(slides, start=1):
        non_empty = [ln.strip() for ln in slide["lines"] if ln.strip()]
        snippet = " / ".join(non_empty[:lines_per_slide]) if non_empty else "(No text)"
        bullets.append(f"""
        <li>
            <span class="pill">Slide {idx}</span>
            <strong>{html.escape(slide['title'])}:</strong>
            <span class="muted">{html.escape(snippet)}</span>
        </li>
        """)
    return "\n".join(bullets)


def generate_report(slides: List[Dict], output_path: str, summary_lines: int):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_html = build_summary(slides, summary_lines)
    toc_entries = []
    cards_html = []
    for idx, slide in enumerate(slides, start=1):
        slide_id = f"slide-{idx}"
        toc_entries.append(f'<li><a href="#{slide_id}">Slide {idx}: {html.escape(slide["title"])}</a></li>')
        content_html = format_slide_content(slide["lines"])
        cards_html.append(f"""
        <article class="card" id="{slide_id}">
            <div class="card-header">
                <div class="eyebrow">Slide {idx}</div>
                <h2>{html.escape(slide["title"])}</h2>
            </div>
            <div class="card-body">
                {content_html}
            </div>
        </article>
        """)
    html_output = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Slide Summary Report</title>
<style>
:root {{
    --bg: #f7f8fb;
    --card: #ffffff;
    --text: #1f2937;
    --muted: #6b7280;
    --accent: #6366f1;
    --accent-2: #14b8a6;
    --border: #e5e7eb;
    --shadow: 0 10px 40px rgba(15, 23, 42, 0.12);
    --radius: 14px;
}}
* {{
    box-sizing: border-box;
}}
body {{
    margin: 0;
    padding: 0 0 48px;
    font-family: "Segoe UI", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    background: radial-gradient(circle at 10% 20%, rgba(99,102,241,0.10), transparent 25%),
                radial-gradient(circle at 80% 10%, rgba(20,184,166,0.12), transparent 25%),
                var(--bg);
    color: var(--text);
    line-height: 1.6;
}}
header {{
    position: sticky;
    top: 0;
    z-index: 10;
    backdrop-filter: blur(10px);
    background: rgba(247, 248, 251, 0.9);
    border-bottom: 1px solid rgba(255,255,255,0.6);
    box-shadow: 0 10px 30px rgba(15,23,42,0.04);
}}
.wrapper {{
    max-width: 1080px;
    margin: 0 auto;
    padding: 20px 22px 0;
}}
.hero {{
    padding: 26px 0 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}}
.hero h1 {{
    margin: 0;
    font-size: 28px;
    letter-spacing: -0.01em;
}}
.meta {{
    color: var(--muted);
    font-size: 14px;
}}
button#print {{
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: white;
    border: none;
    border-radius: 999px;
    padding: 12px 18px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(99,102,241,0.25);
    transition: transform 0.15s ease, box-shadow 0.2s ease;
}}
button#print:hover {{
    transform: translateY(-1px);
    box-shadow: 0 14px 40px rgba(99,102,241,0.35);
}}
section {{
    margin: 18px 0;
}}
.panel {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    box-shadow: var(--shadow);
}}
.panel h3 {{
    margin: 0 0 10px;
    font-size: 18px;
}}
.summary-list, .toc-list {{
    margin: 0;
    padding-left: 18px;
}
.summary-list li {{
    margin-bottom: 8px;
    line-height: 1.5;
}}
.summary-list .pill {{
    display: inline-block;
    background: rgba(99,102,241,0.12);
    color: var(--accent);
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-right: 8px;
}}
.summary-list .muted {{
    color: var(--muted);
}}
.toc-list li {{
    margin-bottom: 6px;
}}
.toc-list a {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
}}
.toc-list a:hover {{
    text-decoration: underline;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 18px;
    margin-top: 16px;
}}
.card {{
    background: var(--card);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 18px;
    padding: 18px 20px 20px;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    break-inside: avoid;
    page-break-inside: avoid;
}}
.card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 18px 45px rgba(15,23,42,0.14);
}}
.card-header {{
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
    margin-bottom: 10px;
}}
.card-header h2 {{
    margin: 6px 0 0;
    font-size: 20px;
}}
.card .eyebrow {{
    text-transform: uppercase;
    font-size: 12px;
    letter-spacing: 0.08em;
    color: var(--muted);
    font-weight: 700;
}}
.card-body p {{
    margin: 0 0 8px;
}}
.card-body ul {{
    margin: 0 0 8px 18px;
    padding: 0;
}
.card-body li {{
    margin: 4px 0;
}}
.empty {{
    text-align: center;
    padding: 40px;
    color: var(--muted);
}}
@media print {{
    body {{
        background: white;
    }}
    header, button#print {{
        display: none !important;
    }}
    .card {{
        box-shadow: none;
        border: 1px solid #d1d5db;
    }}
    .wrapper {{
        padding: 0 12px;
    }}
}}
</style>
</head>
<body>
<header>
    <div class="wrapper hero">
        <div>
            <h1>Slide Summary Report</h1>
            <div class="meta">Generated: {now} · Slides: {len(slides)}</div>
        </div>
        <button id="print" onclick="window.print()">Print to PDF</button>
    </div>
</header>
<main class="wrapper">
    <section class="panel" id="summary">
        <h3>Summary</h3>
        <ol class="summary-list">
            {summary_html}
        </ol>
    </section>

    <section class="panel" id="toc">
        <h3>Table of Contents</h3>
        <ol class="toc-list">
            {"".join(toc_entries)}
        </ol>
    </section>

    <section aria-label="Slides">
        <div class="grid">
            {"".join(cards_html)}
        </div>
    </section>
</main>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a premium HTML summary report from .txt slide files."
    )
    parser.add_argument(
        "-i", "--input", default=".", help="Directory containing .txt slide files (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output", default="report.html", help="Output HTML file path (default: report.html)"
    )
    parser.add_argument(
        "--summary-lines",
        type=int,
        default=2,
        help="Number of non-empty lines per slide to include in the summary (default: 2)",
    )
    args = parser.parse_args(argv)

    slides = collect_slides(args.input)
    if not slides:
        sys.stderr.write(f"No .txt slides found in {os.path.abspath(args.input)}\n")
        return 1

    generate_report(slides, args.output, args.summary_lines)
    print(f"Report generated: {os.path.abspath(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())