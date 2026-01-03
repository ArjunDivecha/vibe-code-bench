import os
import re
from pathlib import Path

def read_slides(directory="."):
    """Read all .txt files from the directory and return a list of (title, content) tuples."""
    slides = []
    for file_path in sorted(Path(directory).glob("slide*.txt")):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Use filename as title, or first line if available
            first_line = content.split('\n')[0] if content else file_path.stem
            title = first_line.strip()
            slides.append((title, content))
    return slides

def generate_summary(slides, line_limit=2):
    """Generate a summary from the first few lines of each slide."""
    summary_lines = []
    for title, content in slides:
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        preview = ' '.join(lines[:line_limit])
        if len(lines) > line_limit:
            preview += '...' if len(preview) > 10 else ''
        summary_lines.append(f"<strong>{title}:</strong> {preview}")
    return "<br>".join(summary_lines)

def generate_toc(slides):
    """Generate HTML for Table of Contents."""
    toc_items = [
        f'<li><a href="#slide-{i+1}">{title}</a></li>'
        for i, (title, _) in enumerate(slides)
    ]
    return "<ol>" + "".join(toc_items) + "</ol>"

def generate_slide_cards(slides):
    """Generate HTML for each slide as a card."""
    cards = []
    for i, (title, content) in enumerate(slides):
        # Preserve line breaks in content
        content_html = content.replace('\n', '<br>')
        card = f"""
<div class="slide-card" id="slide-{i+1}">
    <h2>{title}</h2>
    <div class="content">{content_html}</div>
</div>
        """.strip()
        cards.append(card)
    return "\n".join(cards)

def generate_html_report(slides):
    """Generate full HTML report with premium styling."""
    summary = generate_summary(slides)
    toc = generate_toc(slides)
    cards = generate_slide_cards(slides)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

        :root {{
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --primary: #2c3e50;
            --secondary: #7f8c8d;
            --accent: #3498db;
            --border: #e0e0e0;
            --shadow: rgba(0, 0, 0, 0.1);
            --spacing-sm: 1rem;
            --spacing: 2rem;
            --spacing-lg: 3rem;
            --radius: 12px;
            --transition: all 0.3s ease;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.7;
            color: var(--primary);
            background-color: var(--bg-color);
            padding: var(--spacing);
            max-width: 1000px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: var(--spacing-lg);
            padding-bottom: var(--spacing);
            border-bottom: 1px solid var(--border);
        }}

        h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 2.8rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }}

        .subtitle {{
            color: var(--secondary);
            font-size: 1.1rem;
            font-weight: 400;
            margin-bottom: 1.5rem;
        }}

        .print-btn {{
            display: inline-block;
            background-color: var(--accent);
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 500;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 6px var(--shadow);
            transition: var(--transition);
            font-size: 1rem;
        }}

        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px var(--shadow);
            background-color: #2980b9;
        }}

        main {{
            display: flex;
            flex-direction: column;
            gap: var(--spacing-lg);
        }}

        section {{
            background-color: var(--card-bg);
            padding: var(--spacing);
            border-radius: var(--radius);
            box-shadow: 0 8px 20px var(--shadow);
            transition: var(--transition);
        }}

        section:hover {{
            box-shadow: 0 12px 30px var(--shadow);
            transform: translateY(-2px);
        }}

        h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            margin-bottom: 1rem;
            color: var(--primary);
            position: relative;
            padding-bottom: 0.5rem;
        }}

        h2::after {{
            content: '';
            position: absolute;
            left: 0;
            bottom: 0;
            width: 50px;
            height: 3px;
            background-color: var(--accent);
            border-radius: 2px;
        }}

        .summary {{
            line-height: 2;
            color: var(--secondary);
        }}

        .toc ol {{
            list-style: none;
            counter-reset: item;
            padding-left: 0;
        }}

        .toc li {{
            margin-bottom: 0.8rem;
            counter-increment: item;
            position: relative;
            padding-left: 2rem;
            transition: var(--transition);
        }}

        .toc li::before {{
            content: counter(item);
            position: absolute;
            left: 0;
            top: 0;
            width: 24px;
            height: 24px;
            background-color: var(--accent);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 600;
        }}

        .toc a {{
            text-decoration: none;
            color: var(--primary);
            font-weight: 500;
            transition: var(--transition);
        }}

        .toc a:hover {{
            color: var(--accent);
        }}

        .slide-card {{
            page-break-inside: avoid;
            break-inside: avoid;
            margin-bottom: 3rem;
        }}

        .content {{
            color: var(--secondary);
            font-size: 1.05rem;
            line-height: 1.8;
        }}

        @media print {{
            body {{
                padding: 0;
                margin: 0;
                background: white;
            }}

            .print-btn {{
                display: none;
            }}

            section {{
                box-shadow: none;
                border: 1px solid var(--border);
            }}

            .slide-card {{
                page-break-after: always;
                padding: 0;
                margin: 0;
                border: none;
            }}

            h2::after {{
                display: none;
            }}

            header {{
                border-bottom: 2px solid var(--border);
                margin-bottom: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Slide Summary Report</h1>
        <p class="subtitle">Generated from text files</p>
        <button class="print-btn" onclick="window.print()">🖨️ Print to PDF</button>
    </header>

    <main>
        <section>
            <h2>Executive Summary</h2>
            <div class="summary">
                {summary}
            </div>
        </section>

        <section class="toc">
            <h2>Table of Contents</h2>
            {toc}
        </section>

        {cards}
    </main>

    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    window.scrollTo({{
                        top: target.offsetTop - 100,
                        behavior: 'smooth'
                    }});
                }}
            }});
        }});
    </script>
</body>
</html>"""
    return html

def main():
    # Read slides from current directory
    slides = read_slides(".")
    
    if not slides:
        print("No slide files found (slide*.txt)")
        return

    # Generate HTML
    html_content = generate_html_report(slides)

    # Write to report.html
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Report generated with {len(slides)} slides: report.html")

if __name__ == "__main__":
    main()