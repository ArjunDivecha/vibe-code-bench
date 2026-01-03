import os
import glob
import re
import html

def generate_report(directory="."):
    # 1. Gather and sort files
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    txt_files.sort(key=lambda f: [int(d) if d.isdigit() else d for d in re.split(r'(\d+)', f)])

    slides = []
    for file_path in txt_files:
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            title = lines[0] if lines else "Untitled Slide"
            body = "\n".join(lines[1:]) if len(lines) > 1 else ""
            summary_snippet = lines[0] if lines else ""
            
            slides.append({
                'id': re.sub(r'\W+', '', filename),
                'filename': filename,
                'title': title,
                'body': body,
                'snippet': summary_snippet
            })

    # 2. HTML Template
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --radius: 12px;
        }}

        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
        }}

        h1 {{ font-size: 2.5rem; font-weight: 800; margin: 0; color: #0f172a; }}
        
        .btn-print {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }}

        .btn-print:hover {{ opacity: 0.9; }}

        /* Sections */
        .section-card {{
            background: var(--bg-card);
            padding: 30px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            margin-bottom: 30px;
        }}

        h2 {{ color: var(--primary); border-left: 4px solid var(--primary); padding-left: 15px; margin-top: 0; }}

        /* TOC */
        .toc-list {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; }}
        .toc-list a {{ text-decoration: none; color: var(--text-main); font-weight: 500; }}
        .toc-list a:hover {{ color: var(--primary); }}

        /* Summary */
        .summary-grid {{ display: flex; flex-direction: column; gap: 8px; }}
        .summary-item {{ font-size: 0.95rem; color: var(--text-muted); display: flex; }}
        .summary-item b {{ color: var(--text-main); margin-right: 10px; min-width: 100px; }}

        /* Slide Cards */
        .slide-card {{
            background: var(--bg-card);
            padding: 40px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            margin-bottom: 40px;
            position: relative;
            border-top: 5px solid var(--primary);
        }}

        .slide-meta {{ font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 10px; }}
        .slide-title {{ font-size: 1.75rem; margin: 0 0 20px 0; font-weight: 700; }}
        .slide-content {{ white-space: pre-wrap; color: #334155; font-size: 1.1rem; }}

        /* Printing */
        @media print {{
            body {{ padding: 0; background: white; }}
            .btn-print, .toc-section {{ display: none; }}
            .slide-card {{
                box-shadow: none;
                border: 1px solid #eee;
                page-break-after: always;
                margin-bottom: 0;
            }}
            .container {{ max-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Presentation Report</h1>
            <button class="btn-print" onclick="window.print()">Print to PDF</button>
        </header>

        <section class="section-card toc-section">
            <h2>Table of Contents</h2>
            <ul class="toc-list">
                {toc_html}
            </ul>
        </section>

        <section class="section-card">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                {summary_html}
            </div>
        </section>

        <div class="slides-container">
            {slides_html}
        </div>
    </div>
</body>
</html>"""

    # 3. Generate HTML snippets
    toc_items = []
    summary_items = []
    slide_cards = []

    for s in slides:
        # TOC
        toc_items.append(f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>')
        
        # Summary
        summary_items.append(
            f'<div class="summary-item"><b>{html.escape(s["filename"])}:</b> {html.escape(s["snippet"])}</div>'
        )
        
        # Slide Card
        slide_cards.append(f"""
        <article class="slide-card" id="{s["id"]}">
            <div class="slide-meta">{html.escape(s["filename"])}</div>
            <h3 class="slide-title">{html.escape(s["title"])}</h3>
            <div class="slide-content">{html.escape(s["body"])}</div>
        </article>
        """)

    # 4. Write file
    final_html = html_template.format(
        toc_html="".join(toc_items),
        summary_html="".join(summary_items),
        slides_html="".join(slide_cards)
    )

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"Successfully generated report.html with {len(slides)} slides.")

if __name__ == "__main__":
    # Create dummy data if no txt files exist for demonstration
    if not glob.glob("*.txt"):
        print("No .txt files found. Creating sample files...")
        samples = {
            "slide1.txt": "Project Overview\\nThis project aims to revolutionize how we generate reports using Python. We focus on simplicity and premium aesthetics.",
            "slide2.txt": "Market Analysis\\nTargeting enterprise clients who value clean data presentation. Current market gap identified in automated slide extraction.",
            "slide3.txt": "Technical Stack\\n- Python 3 Standard Library\\n- Modern CSS3 (Grid/Flexbox)\\n- No external dependencies.",
            "slide4.txt": "Next Steps\\nFinalize the PDF export functionality and deploy to production within the next quarter."
        }
        for name, content in samples.items():
            with open(name, "w") as f:
                f.write(content.replace("\\n", "\n"))

    generate_report()