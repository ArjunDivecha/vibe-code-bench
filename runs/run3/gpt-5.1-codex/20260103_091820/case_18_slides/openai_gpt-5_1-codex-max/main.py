import os
import sys
import glob
import html
from datetime import datetime
from typing import List, Dict


def read_slides(directory: str) -> List[Dict]:
    pattern = os.path.join(directory, "*.txt")
    files = sorted(glob.glob(pattern))
    slides = []
    for idx, path in enumerate(files, start=1):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            # Skip unreadable files but note the error
            content = f"Unable to read file: {exc}"
        lines = content.splitlines()
        # Extract first non-empty lines for summary
        summary_lines = []
        for line in lines:
            if line.strip():
                summary_lines.append(line.strip())
            if len(summary_lines) >= 2:
                break
        if not summary_lines and lines:
            summary_lines = lines[:2]
        base = os.path.basename(path)
        name = os.path.splitext(base)[0]
        title = name.replace("_", " ").replace("-", " ").title()
        slides.append(
            {
                "id": f"slide-{idx}",
                "index": idx,
                "file": base,
                "title": title,
                "content": content,
                "summary": summary_lines,
            }
        )
    return slides


def build_summary(slides: List[Dict]) -> str:
    if not slides:
        return "<p>No slides found to summarize.</p>"
    items = []
    for slide in slides:
        snippet = " — ".join(html.escape(line) for line in slide["summary"]) or "No content"
        items.append(
            f'<li><span class="badge">Slide {slide["index"]}</span>'
            f'<strong>{html.escape(slide["title"])}</strong><div class="snippet">{snippet}</div></li>'
        )
    return "<ul class=\"summary-list\">" + "".join(items) + "</ul>"


def build_toc(slides: List[Dict]) -> str:
    if not slides:
        return "<p>No entries.</p>"
    items = []
    for slide in slides:
        items.append(
            f'<li><a href="#{slide["id"]}">'
            f'<span class="toc-index">{slide["index"]:02d}</span>'
            f'{html.escape(slide["title"])}'
            f'</a></li>'
        )
    return "<ol class=\"toc-list\">" + "".join(items) + "</ol>"


def build_slide_cards(slides: List[Dict]) -> str:
    if not slides:
        return "<div class=\"empty\">No slides to display.</div>"
    cards = []
    for slide in slides:
        safe_content = html.escape(slide["content"])
        cards.append(
            f'''
            <section class="slide-card" id="{slide["id"]}">
                <div class="slide-head">
                    <div>
                        <div class="pill">Slide {slide["index"]}</div>
                        <h3>{html.escape(slide["title"])}</h3>
                        <div class="file-name">{html.escape(slide["file"])}</div>
                    </div>
                    <a class="back-to-top" href="#top">Back to top ↑</a>
                </div>
                <pre class="slide-body">{safe_content}</pre>
            </section>
            '''
        )
    return "\n".join(cards)


def build_report(slides: List[Dict], output_path: str):
    now = datetime.now().strftime("%B %d, %Y • %I:%M %p")
    total = len(slides)
    summary_html = build_summary(slides)
    toc_html = build_toc(slides)
    slides_html = build_slide_cards(slides)
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Slide Summary Report</title>
<style>
:root {{
    --bg: #f4f6fb;
    --card: #ffffff;
    --primary: #1d4ed8;
    --primary-soft: rgba(29, 78, 216, 0.08);
    --text: #0f172a;
    --muted: #6b7280;
    --shadow: 0 15px 35px rgba(0,0,0,0.07);
    --radius: 18px;
    --maxw: 1100px;
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 0 16px 60px;
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 100%);
    color: var(--text);
}}
a {{ color: var(--primary); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
#top {{ position: absolute; top: 0; }}
.container {{ max-width: var(--maxw); margin: 0 auto; }}
.hero {{
    position: sticky;
    top: 0;
    backdrop-filter: blur(8px);
    background: rgba(255, 255, 255, 0.8);
    padding: 18px;
    z-index: 10;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}}
.hero-inner {{
    display: flex;
    align-items: center;
    gap: 16px;
}}
.hero-title {{
    font-size: 28px;
    font-weight: 800;
    margin: 0;
}}
.subtitle {{
    margin: 4px 0 0 0;
    color: var(--muted);
    font-weight: 500;
}}
.print-btn {{
    margin-left: auto;
    border: none;
    padding: 12px 16px;
    border-radius: 12px;
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: #fff;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25);
    transition: transform 0.15s ease, box-shadow 0.2s ease;
}}
.print-btn:hover {{
    transform: translateY(-1px);
    box-shadow: 0 15px 30px rgba(37, 99, 235, 0.35);
}}
.section {{
    margin: 26px auto;
    padding: 22px 24px;
    background: var(--card);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    border: 1px solid rgba(0,0,0,0.04);
}}
.section h2 {{
    margin-top: 0;
    font-size: 20px;
    letter-spacing: -0.01em;
}}
.meta {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    color: var(--muted);
    font-size: 14px;
}}
.badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: var(--primary-soft);
    color: var(--primary);
    border-radius: 999px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.summary-list {{
    list-style: none;
    padding-left: 0;
    margin: 12px 0 0 0;
    display: grid;
    gap: 12px;
}
.summary-list li {{
    padding: 14px 16px;
    border-radius: 12px;
    background: linear-gradient(135deg, #f8fafc, #eef2ff);
    border: 1px solid rgba(37,99,235,0.08);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);
}}
.summary-list .snippet {{
    color: var(--muted);
    margin-top: 4px;
}}
.toc-list {{
    counter-reset: toc;
    list-style: none;
    padding-left: 0;
    display: grid;
    gap: 8px;
    margin: 0;
}}
.toc-list li {{
    padding: 10px 12px;
    border-radius: 10px;
    transition: background 0.15s ease;
}}
.toc-list li:hover {{
    background: rgba(37, 99, 235, 0.08);
}}
.toc-index {{
    display: inline-flex;
    width: 32px;
    height: 32px;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: var(--primary-soft);
    color: var(--primary);
    font-weight: 700;
    margin-right: 10px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.85);
}}
.slide-card {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 18px 20px;
    margin: 18px 0;
    box-shadow: var(--shadow);
    border: 1px solid rgba(0,0,0,0.04);
    break-inside: avoid;
    page-break-inside: avoid;
}}
.slide-head {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
}}
.slide-head h3 {{
    margin: 2px 0 2px 0;
    font-size: 20px;
}}
.pill {{
    display: inline-flex;
    padding: 6px 10px;
    border-radius: 999px;
    background: var(--primary-soft);
    color: var(--primary);
    font-weight: 700;
    font-size: 12px;
}}
.file-name {{
    color: var(--muted);
    font-size: 13px;
}}
.back-to-top {{
    margin-left: auto;
    color: var(--muted);
    font-weight: 600;
    font-size: 13px;
}}
.slide-body {{
    white-space: pre-wrap;
    background: #0b1021;
    color: #e5e7eb;
    border-radius: 12px;
    padding: 14px;
    margin: 0;
    font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 14px;
    line-height: 1.55;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}}
.empty {{
    padding: 20px;
    text-align: center;
    color: var(--muted);
}}
@media print {{
    body {{
        background: #fff;
        padding: 0;
    }}
    .hero, .print-btn, .back-to-top {{
        display: none !important;
    }}
    .section, .slide-card {{
        box-shadow: none;
        border: 1px solid #e5e7eb;
        page-break-inside: avoid;
    }}
    .slide-card {{
        margin: 0 0 14px 0;
    }}
}}
</style>
</head>
<body>
<a id="top"></a>
<div class="hero">
  <div class="container hero-inner">
    <div>
      <div class="hero-title">Slide Summary Report</div>
      <div class="subtitle">Generated {now} · {total} slide{'s' if total != 1 else ''}</div>
    </div>
    <button class="print-btn" onclick="window.print()">Print to PDF</button>
  </div>
</div>

<div class="container">
  <section class="section" id="summary">
    <div class="meta">
      <span class="badge">Summary</span>
      <span>Collected from first lines of every slide.</span>
    </div>
    <h2>Highlights</h2>
    {summary_html}
  </section>

  <section class="section" id="toc">
    <div class="meta">
      <span class="badge">Table of Contents</span>
      <span>Jump directly to any slide.</span>
    </div>
    {toc_html}
  </section>

  <section class="slides">
    {slides_html}
  </section>
</div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"Report created: {output_path}")


def main():
    args = sys.argv[1:]
    slides_dir = args[0] if args else os.getcwd()
    output = args[1] if len(args) > 1 else os.path.join(slides_dir, "report.html")
    if not os.path.isdir(slides_dir):
        print(f"Directory not found: {slides_dir}", file=sys.stderr)
        sys.exit(1)
    slides = read_slides(slides_dir)
    build_report(slides, output)


if __name__ == "__main__":
    main()