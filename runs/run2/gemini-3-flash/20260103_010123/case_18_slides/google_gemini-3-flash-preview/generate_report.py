import os
import re
import glob
import html

def get_slide_data():
    """Reads all .txt files in the current directory and extracts content."""
    slides = []
    # Find all .txt files, sorted numerically/alphabetically
    files = sorted(glob.glob("slide*.txt"), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    
    # If no slide*.txt files are found, just take any .txt files
    if not files:
        files = sorted(glob.glob("*.txt"))

    for filename in files:
        if filename == "requirements.txt": continue
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                title = lines[0] if lines else "Untitled Slide"
                body = "\n".join(lines[1:]) if len(lines) > 1 else ""
                summary_snippet = lines[0] if lines else ""
                
                slides.append({
                    "id": os.path.splitext(filename)[0],
                    "filename": filename,
                    "title": title,
                    "body": body,
                    "summary": summary_snippet
                })
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    return slides

def generate_html(slides):
    """Generates the premium HTML string."""
    
    toc_html = "".join([f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>' for s in slides])
    
    summary_items = "".join([f'<li><strong>{html.escape(s["title"])}:</strong> {html.escape(s["summary"])}</li>' for s in slides])

    cards_html = ""
    for s in slides:
        body_paragraphs = "".join([f'<p>{html.escape(p)}</p>' for p in s["body"].split('\n') if p.strip()])
        cards_html += f"""
        <div class="slide-card" id="{s["id"]}">
            <div class="slide-header">
                <span class="slide-meta">{html.escape(s["filename"])}</span>
                <h2>{html.escape(s["title"])}</h2>
            </div>
            <div class="slide-body">
                {body_paragraphs}
            </div>
        </div>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --text-main: #1e293b;
            --text-light: #64748b;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }}

        @media print {{
            .no-print {{ display: none !important; }}
            body {{ background: white !important; padding: 0 !important; }}
            .slide-card {{ 
                break-inside: avoid; 
                box-shadow: none !important; 
                border: 1px solid #eee !important;
                margin-bottom: 20px !important;
            }}
            .page-break {{ page-break-before: always; }}
        }}

        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-main);
            background-color: var(--bg);
            margin: 0;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 50px;
        }}

        h1 {{ font-size: 2.5rem; font-weight: 800; letter-spacing: -0.025em; margin-bottom: 10px; }}
        
        .btn-print {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            margin-top: 10px;
        }}
        .btn-print:hover {{ opacity: 0.9; }}

        .section-box {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }}

        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 20px;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Table of Contents */
        .toc-list {{
            column-count: 2;
            list-style: none;
            padding: 0;
        }}
        .toc-list li {{ margin-bottom: 8px; }}
        .toc-list a {{
            color: var(--text-main);
            text-decoration: none;
            font-size: 0.95rem;
        }}
        .toc-list a:hover {{ color: var(--primary); text-decoration: underline; }}

        /* Executive Summary */
        .summary-list {{
            padding: 0;
            list-style: none;
        }}
        .summary-list li {{
            margin-bottom: 12px;
            font-size: 0.95rem;
            border-left: 3px solid var(--border);
            padding-left: 15px;
        }}

        /* Slide Cards */
        .slide-card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            position: relative;
        }}

        .slide-meta {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
        }}

        .slide-header h2 {{
            margin: 5px 0 20px 0;
            font-size: 1.75rem;
            color: var(--primary);
        }}

        .slide-body p {{
            margin-bottom: 15px;
            font-size: 1.1rem;
            color: #334155;
        }}

        footer {{
            text-align: center;
            color: var(--text-light);
            font-size: 0.875rem;
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="no-print">
            <h1>Slide Summary Report</h1>
            <button class="btn-print" onclick="window.print()">Print to PDF</button>
        </header>

        <div class="section-box no-print">
            <div class="section-title">Table of Contents</div>
            <ul class="toc-list">
                {toc_html}
            </ul>
        </div>

        <div class="section-box">
            <div class="section-title">Executive Summary</div>
            <ul class="summary-list">
                {summary_items}
            </ul>
        </div>

        <div class="page-break"></div>

        <div class="slides-container">
            {cards_html}
        </div>

        <footer>
            Generated by Slide Summary Reporter &bull; {len(slides)} Slides Processed
        </footer>
    </div>
</body>
</html>
"""
    return html_template

def main():
    print("Scanning directory for slide files...")
    slides = get_slide_data()
    
    if not slides:
        print("No .txt files found. Creating dummy files for demonstration...")
        dummy_content = [
            ("slide1.txt", "Market Overview 2023\nGrowth is expected to hit 15% this year.\nWe are seeing strong demand in the tech sector.\nGlobal expansion remains a priority."),
            ("slide2.txt", "Financial Milestones\nQ3 revenue exceeded $4M.\nOperating margins improved by 5%.\nCash reserves are at an all-time high."),
            ("slide3.txt", "Strategic Goals\nFocus on AI integration across all products.\nReduce customer churn by 10%.\nLaunch the new mobile platform by December.")
        ]
        for name, content in dummy_content:
            with open(name, 'w') as f: f.write(content)
        slides = get_slide_data()

    html_content = generate_html(slides)
    
    output_file = "report.html"
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Success! Report generated: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()