import os
import re
import html
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Configuration
SUMMARY_LINES_PER_SLIDE = 2  # number of non-empty lines to pull from each slide for the summary
REPORT_FILENAME = "report.html"


def natural_key(s: str):
    """
    Sort helper that handles numbers in filenames naturally (slide2 before slide10).
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def read_slide_files(directory: Path) -> List[Tuple[str, str]]:
    """
    Read all .txt files in the directory and return list of (filename, content), sorted naturally.
    """
    slides = []
    for entry in directory.iterdir():
        if entry.is_file() and entry.suffix.lower() == ".txt":
            try:
                content = entry.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Fallback to default encoding if UTF-8 fails
                content = entry.read_text(errors="replace")
            slides.append((entry.name, content))

    slides.sort(key=lambda x: natural_key(x[0]))
    return slides


def summarize_slide(content: str, max_lines: int) -> str:
    """
    Grab the first non-empty lines up to max_lines for the summary.
    """
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    snippet = lines[:max_lines]
    return " — ".join(snippet)


def slide_to_html(content: str) -> str:
    """
    Convert slide text into HTML paragraphs, preserving blank lines as spacing.
    """
    parts = []
    for block in content.split("\n\n"):
        cleaned = block.strip("\n")
        if not cleaned.strip():
            continue
        escaped = html.escape(cleaned)
        # Replace single newlines inside block with <br> for nicer formatting
        escaped = "<br>".join(escaped.splitlines())
        parts.append(f"<p>{escaped}</p>")
    return "\n".join(parts) if parts else "<p class=\"muted\">(No content)</p>"


def generate_report(slides: List[Tuple[str, str]], output_path: Path):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_items = []
    toc_items = []
    cards = []

    for idx, (filename, content) in enumerate(slides, start=1):
        slide_id = f"slide-{idx}"
        title = Path(filename).stem
        snippet = summarize_slide(content, SUMMARY_LINES_PER_SLIDE)
        summary_html = html.escape(snippet) if snippet else "(no summary available)"
        summary_items.append(f'<li><a href="#{slide_id}"><strong>{html.escape(title)}</strong></a> — {summary_html}</li>')
        toc_items.append(f'<li><a href="#{slide_id}">{idx}. {html.escape(title)}</a></li>')
        cards.append(
            f"""
            <section class="slide-card" id="{slide_id}">
                <div class="card-header">
                    <div class="pill">Slide {idx}</div>
                    <h2>{html.escape(title)}</h2>
                </div>
                <div class="card-body">
                    {slide_to_html(content)}
                </div>
            </section>
            """
        )

    if not slides:
        summary_html = "<p>No slide files were found.</p>"
        toc_html = "<p class=\"muted\">Add .txt files to generate a report.</p>"
    else:
        summary_html = "<ul class=\"summary-list\">\n" + "\n".join(summary_items) + "\n</ul>"
        toc_html = "<ol class=\"toc-list\">\n" + "\n".join(toc_items) + "\n</ol>"

    html_content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Slide Summary Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
    --bg: #0f1116;
    --panel: #161a22;
    --panel-2: #1f2532;
    --accent: #7dd3fc;
    --accent-2: #a855f7;
    --text: #e9edf5;
    --muted: #9aa3b5;
    --border: #232a39;
    --shadow: 0 20px 60px rgba(0,0,0,0.35);
    --radius: 18px;
    --font: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    padding: 32px;
    font-family: var(--font);
    background: radial-gradient(circle at 20% 20%, rgba(168,85,247,0.12), transparent 35%),
                radial-gradient(circle at 80% 0%, rgba(125,211,252,0.12), transparent 28%),
                linear-gradient(135deg, #0d1117 0%, #0b1020 100%);
    color: var(--text);
    line-height: 1.6;
}}

header {{
    max-width: 1100px;
    margin: 0 auto 28px;
    padding: 24px 28px;
    background: rgba(22,26,34,0.92);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    backdrop-filter: blur(10px);
}}

h1 {{
    margin: 0 0 8px;
    font-size: 28px;
    letter-spacing: -0.02em;
}}

.meta {{
    color: var(--muted);
    font-size: 14px;
}}

.actions {{
    display: flex;
    gap: 12px;
    margin-top: 16px;
}}

button#print-btn {{
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: #0b1020;
    border: none;
    padding: 12px 16px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 15px;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(168,85,247,0.35);
    transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
}}
button#print-btn:hover {{
    transform: translateY(-1px);
    filter: brightness(1.05);
    box-shadow: 0 12px 35px rgba(125,211,252,0.35);
}}
button#print-btn:active {{
    transform: translateY(0);
}}

.section {{
    max-width: 1100px;
    margin: 0 auto 22px;
    background: rgba(15,17,22,0.85);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 24px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(6px);
}}

.section h2 {{
    margin-top: 0;
    letter-spacing: -0.01em;
}}

.summary-list, .toc-list {{
    margin: 12px 0 0;
    padding-left: 20px;
}}

.summary-list li {{
    margin-bottom: 8px;
}}

.summary-list a, .toc-list a {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
}}
.summary-list a:hover, .toc-list a:hover {{
    color: var(--accent-2);
}}

.main-grid {{
    max-width: 1100px;
    margin: 0 auto 40px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 18px;
}}

.slide-card {{
    background: linear-gradient(145deg, var(--panel), var(--panel-2));
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
    page-break-inside: avoid;
}}

.slide-card::before {{
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 20% 20%, rgba(125,211,252,0.08), transparent 55%),
                radial-gradient(circle at 80% 10%, rgba(168,85,247,0.12), transparent 50%);
    opacity: 0.9;
    pointer-events: none;
}}

.slide-card .card-header {{
    position: relative;
    z-index: 2;
}}

.slide-card h2 {{
    margin: 6px 0 10px;
    font-size: 20px;
    letter-spacing: -0.01em;
}}

.slide-card .pill {{
    display: inline-flex;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(125,211,252,0.12);
    border: 1px solid rgba(125,211,252,0.3);
    color: var(--accent);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
}}

.card-body {{
    position: relative;
    z-index: 2;
    color: #f5f7fb;
}}

.card-body p {{
    margin: 0 0 10px;
    line-height: 1.55;
}}

p.muted, .muted {{
    color: var(--muted);
}}

@media print {{
    body {{
        background: white;
        color: #111;
        padding: 0;
    }}
    header, .section {{
        box-shadow: none;
        background: white;
        border: none;
    }}
    .slide-card {{
        page-break-inside: avoid;
        break-inside: avoid;
        box-shadow: none;
        background: white;
        border: 1px solid #ddd;
    }}
    button#print-btn, .actions {{
        display: none !important;
    }}
}}
</style>
</head>
<body>
<header>
    <h1>Slide Summary Report</h1>
    <div class="meta">Generated: {generated_at} — Files scanned: {len(slides)}</div>
    <div class="actions">
        <button id="print-btn" onclick="window.print()">Print to PDF</button>
    </div>
</header>

<section class="section" id="summary">
    <h2>Summary Highlights</h2>
    {summary_html}
</section>

<section class="section" id="toc">
    <h2>Table of Contents</h2>
    {toc_html}
</section>

<div class="main-grid">
    {"".join(cards) if cards else ""}
</div>

<script>
// Smooth scroll for in-page links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
    anchor.addEventListener('click', function (e) {{
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {{
            e.preventDefault();
            target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
    }});
}});
</script>
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Report created: {output_path}")


def main():
    cwd = Path(os.getcwd())
    slides = read_slide_files(cwd)
    output_path = cwd / REPORT_FILENAME
    generate_report(slides, output_path)


if __name__ == "__main__":
    main()