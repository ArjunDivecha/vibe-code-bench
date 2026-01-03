import os
import re
import html
import datetime

# --- Configuration ---
OUTPUT_FILE = "report.html"
TITLE = "Slide Summary Report"

# --- HTML Template Parts ---

CSS = """
:root {
    --bg-color: #f8fafc;
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --accent-color: #3b82f6;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

* { box-sizing: border-box; }

body {
    font-family: var(--font-family);
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.6;
    margin: 0;
    padding: 40px;
    -webkit-font-smoothing: antialiased;
}

.container {
    max-width: 900px;
    margin: 0 auto;
}

header {
    margin-bottom: 40px;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

h1 {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    margin: 0;
    color: var(--text-primary);
}

.meta {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 5px;
}

.btn-print {
    background-color: var(--text-primary);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-print:hover {
    background-color: var(--accent-color);
}

section {
    margin-bottom: 50px;
}

h2 {
    font-size: 1.5rem;
    color: var(--text-primary);
    margin-bottom: 20px;
    border-left: 4px solid var(--accent-color);
    padding-left: 12px;
}

/* Summary Box */
.summary-box {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 30px;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
}

.summary-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.summary-list li {
    padding: 10px 0;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    gap: 15px;
}

.summary-list li:last-child {
    border-bottom: none;
}

.summary-marker {
    color: var(--accent-color);
    font-weight: bold;
    min-width: 20px;
}

/* TOC */
.toc {
    background: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    border: 1px solid var(--border-color);
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
    columns: 2;
}

.toc a {
    text-decoration: none;
    color: var(--accent-color);
    font-weight: 500;
    display: block;
    padding: 4px 0;
}

.toc a:hover {
    text-decoration: underline;
}

/* Slide Cards */
.slide-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 40px;
    margin-bottom: 40px;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
    page-break-inside: avoid;
    break-inside: avoid;
}

.slide-header {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--border-color);
}

.slide-title {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
}

.slide-id {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
    margin-bottom: 5px;
    display: block;
}

.slide-content {
    font-size: 1.1rem;
    color: var(--text-secondary);
    white-space: pre-wrap;
}

footer {
    text-align: center;
    color: var(--text-secondary);
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
    font-size: 0.9rem;
}

/* Print Styles */
@media print {
    body {
        background: white;
        padding: 0;
        color: black;
    }
    .container {
        max-width: 1000px;
        width: 100%;
    }
    .btn-print {
        display: none;
    }
    .slide-card, .summary-box, .toc {
        box-shadow: none;
        border: 1px solid #ccc;
        margin-bottom: 30px;
    }
    h2 {
        border-left-color: #000;
    }
    a {
        text-decoration: none;
        color: black;
    }
    .slide-card {
        page-break-after: always;
    }
    .slide-card:last-child {
        page-break-after: auto;
    }
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{title}</h1>
                <div class="meta">Generated on {date} &bull; {count} Slides processed</div>
            </div>
            <button class="btn-print" onclick="window.print()">Print to PDF</button>
        </header>

        <section id="executive-summary">
            <h2>Executive Summary</h2>
            <div class="summary-box">
                <p style="margin-bottom: 20px; color: var(--text-secondary);">
                    The following is a consolidated summary of the key points extracted from the slide deck.
                </p>
                <ul class="summary-list">
                    {summary_items}
                </ul>
            </div>
        </section>

        <section id="toc">
            <h2>Table of Contents</h2>
            <div class="toc">
                <ul>
                    {toc_items}
                </ul>
            </div>
        </section>

        <section id="slides">
            {slide_cards}
        </section>

        <footer>
            <p>Generated by Slide Summary Reporter Tool</p>
        </footer>
    </div>
</body>
</html>
"""

# --- Logic ---

def natural_sort_key(s):
    """
    Sorts strings containing numbers naturally (e.g., slide2 comes before slide10).
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def get_slide_files(directory="."):
    """Returns a sorted list of .txt files in the directory."""
    files = [f for f in os.listdir(directory) if f.endswith(".txt")]
    files.sort(key=natural_sort_key)
    return files

def parse_slide(filename):
    """Reads a file and returns a dict with title, content, and summary text."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            raw_content = f.read().strip()
    except Exception as e:
        return None

    if not raw_content:
        return {
            'id': filename,
            'title': "Empty Slide",
            'content': "",
            'summary': "No content available."
        }

    lines = [line.strip() for line in raw_content.split('\n') if line.strip()]
    
    # Heuristic: First line is title
    title = lines[0]
    
    # Content is everything else
    content_lines = lines[1:] if len(lines) > 1 else []
    content_text = "\n".join(content_lines)
    
    # Summary: Take the first available content line, or title if no content
    summary = content_lines[0] if content_lines else title

    return {
        'id': filename,
        'title': title,
        'content': content_text,
        'summary': summary
    }

def main():
    print(f"Scanning directory: {os.getcwd()}")
    files = get_slide_files()
    
    if not files:
        print("No .txt files found. Please run setup_demo_data.py first or add .txt files.")
        return

    print(f"Found {len(files)} slide files.")
    
    slides_data = []
    for f in files:
        data = parse_slide(f)
        if data:
            slides_data.append(data)

    # Build HTML parts
    summary_items = ""
    toc_items = ""
    slide_cards = ""

    for i, slide in enumerate(slides_data):
        slide_num = i + 1
        safe_id = f"slide-{slide_num}"
        
        # Summary Item
        summary_items += f"""
        <li>
            <span class="summary-marker">{slide_num}.</span>
            <span><strong>{html.escape(slide['title'])}:</strong> {html.escape(slide['summary'])}</span>
        </li>
        """
        
        # TOC Item
        toc_items += f'<li><a href="#{safe_id}">{slide_num}. {html.escape(slide["title"])}</a></li>'
        
        # Slide Card
        slide_cards += f"""
        <div class="slide-card" id="{safe_id}">
            <div class="slide-header">
                <span class="slide-id">Slide {slide_num} &bull; {html.escape(slide['id'])}</span>
                <h3 class="slide-title">{html.escape(slide['title'])}</h3>
            </div>
            <div class="slide-content">{html.escape(slide['content'])}</div>
        </div>
        """

    # Final Assembly
    final_html = HTML_TEMPLATE.format(
        title=TITLE,
        css=CSS,
        date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        count=len(slides_data),
        summary_items=summary_items,
        toc_items=toc_items,
        slide_cards=slide_cards
    )

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Success! Report generated at: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()