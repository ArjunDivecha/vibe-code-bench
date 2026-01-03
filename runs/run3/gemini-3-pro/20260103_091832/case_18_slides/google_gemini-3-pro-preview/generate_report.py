import os
import re
import html
import sys

# Configuration
INPUT_DIR = 'slides'
OUTPUT_FILE = 'report.html'

def natural_sort_key(s):
    """
    Sorts strings containing numbers naturally (e.g., slide1, slide2, slide10).
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def read_slides(directory):
    """
    Reads all .txt files from the directory, sorted naturally.
    Returns a list of dicts: {'filename': str, 'title': str, 'content': str, 'summary': str}
    """
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)

    files = [f for f in os.listdir(directory) if f.lower().endswith('.txt')]
    files.sort(key=natural_sort_key)

    slides = []
    for filename in files:
        path = os.path.join(directory, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_text = f.read().strip()
                
            lines = raw_text.split('\n')
            # Assume first non-empty line is title, rest is content
            title = lines[0] if lines else "Untitled Slide"
            
            # Summary is the first 2-3 meaningful lines
            summary_lines = [l for l in lines if l.strip()][:3]
            summary_text = " ".join(summary_lines)
            
            slides.append({
                'id': filename.replace('.', '_'),
                'filename': filename,
                'title': title,
                'content': raw_text,
                'summary_excerpt': summary_text
            })
        except Exception as e:
            print(f"Skipping {filename}: {e}")

    return slides

def generate_html(slides):
    """
    Constructs the HTML report with embedded CSS.
    """
    
    # -- HTML Components --
    
    toc_items = "".join([
        f'<li><a href="#{s["id"]}"><span class="toc-num">{i+1}</span> {html.escape(s["title"])}</a></li>'
        for i, s in enumerate(slides)
    ])

    summary_paragraphs = "".join([
        f'<p><strong>{html.escape(s["title"])}:</strong> {html.escape(s["summary_excerpt"])}...</p>'
        for s in slides
    ])

    slide_cards = ""
    for i, s in enumerate(slides):
        # Format content: preserve newlines, maybe make bullet points look nice
        safe_content = html.escape(s['content'])
        # rigorous formatting for display
        formatted_content = safe_content.replace('\n', '<br>')
        
        slide_cards += f"""
        <article id="{s['id']}" class="slide-card">
            <div class="card-header">
                <span class="slide-number">Slide {i+1}</span>
                <h3>{html.escape(s['title'])}</h3>
            </div>
            <div class="card-body">
                {formatted_content}
            </div>
            <div class="card-footer">
                <span class="filename">{html.escape(s['filename'])}</span>
            </div>
        </article>
        """

    # -- CSS Styles --
    css = """
    :root {
        --bg-color: #f8f9fa;
        --card-bg: #ffffff;
        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --accent: #4f46e5;
        --accent-hover: #4338ca;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    * { box-sizing: border-box; }

    body {
        font-family: var(--font-sans);
        background-color: var(--bg-color);
        color: var(--text-primary);
        line-height: 1.6;
        margin: 0;
        padding: 0;
        -webkit-font-smoothing: antialiased;
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 40px 20px;
    }

    /* Header */
    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 20px;
    }

    h1 {
        font-size: 2.25rem;
        font-weight: 800;
        color: #111827;
        margin: 0;
        letter-spacing: -0.025em;
    }

    .btn-print {
        background-color: var(--accent);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.2s;
        box-shadow: var(--shadow-sm);
    }

    .btn-print:hover {
        background-color: var(--accent-hover);
    }

    /* Sections */
    section {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 30px;
        box-shadow: var(--shadow-md);
    }

    h2 {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 20px;
        color: #2d3748;
        border-bottom: 1px solid #edf2f7;
        padding-bottom: 10px;
    }

    /* TOC */
    .toc-list {
        list-style: none;
        padding: 0;
        columns: 2;
    }
    
    .toc-list li {
        margin-bottom: 8px;
    }

    .toc-list a {
        text-decoration: none;
        color: var(--text-secondary);
        font-weight: 500;
        transition: color 0.2s;
        display: flex;
        align-items: center;
    }

    .toc-list a:hover {
        color: var(--accent);
    }

    .toc-num {
        background: #edf2f7;
        color: #4a5568;
        font-size: 0.8rem;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 10px;
        font-weight: 700;
    }

    /* Summary */
    .summary-content p {
        margin-bottom: 12px;
        color: #4a5568;
    }
    
    .summary-content strong {
        color: #2d3748;
    }

    /* Slide Cards */
    .slide-card {
        background: var(--card-bg);
        border-radius: 12px;
        box-shadow: var(--shadow-md);
        margin-bottom: 40px;
        overflow: hidden;
        border: 1px solid #edf2f7;
        transition: transform 0.2s, box-shadow 0.2s;
        page-break-inside: avoid; /* Print CSS */
    }

    .slide-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    .card-header {
        background: #f7fafc;
        padding: 20px 30px;
        border-bottom: 1px solid #edf2f7;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .card-header h3 {
        margin: 0;
        font-size: 1.25rem;
        color: #2d3748;
    }

    .slide-number {
        text-transform: uppercase;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: #a0aec0;
    }

    .card-body {
        padding: 30px;
        font-size: 1.05rem;
        color: #2d3748;
        white-space: pre-wrap; /* Preserve text formatting */
    }

    .card-footer {
        background: #fafafa;
        padding: 10px 30px;
        border-top: 1px solid #edf2f7;
        text-align: right;
    }

    .filename {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-size: 0.8rem;
        color: #a0aec0;
    }

    /* Print CSS */
    @media print {
        body {
            background-color: white;
            color: black;
        }
        .container {
            width: 100%;
            max-width: none;
            padding: 0;
            margin: 0;
        }
        .btn-print {
            display: none;
        }
        .slide-card {
            box-shadow: none;
            border: 1px solid #ccc;
            break-inside: avoid;
            margin-bottom: 20px;
        }
        header {
            border-bottom: none;
            margin-bottom: 20px;
        }
        section {
            box-shadow: none;
            border: none;
            padding: 0;
        }
    }
    """

    # -- HTML Assembly --
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Slide Summary Report</h1>
            <button class="btn-print" onclick="window.print()">Print to PDF</button>
        </header>

        <section id="toc">
            <h2>Table of Contents</h2>
            <ul class="toc-list">
                {toc_items}
            </ul>
        </section>

        <section id="summary">
            <h2>Executive Summary</h2>
            <div class="summary-content">
                {summary_paragraphs}
            </div>
        </section>

        <main>
            {slide_cards}
        </main>
        
        <script>
            // Simple JS to add a nice fade-in effect on load
            document.addEventListener('DOMContentLoaded', () => {{
                document.body.style.opacity = 0;
                document.body.style.transition = 'opacity 0.5s ease';
                requestAnimationFrame(() => {{
                    document.body.style.opacity = 1;
                }});
            }});
        </script>
    </div>
</body>
</html>
"""
    return html_content

def main():
    print("Reading slides...")
    slides = read_slides(INPUT_DIR)
    
    if not slides:
        print("No slides found. Make sure .txt files exist in the 'slides' directory.")
        return

    print(f"Found {len(slides)} slides. Generating report...")
    report_html = generate_html(slides)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report_html)

    print(f"Success! Report generated at: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()