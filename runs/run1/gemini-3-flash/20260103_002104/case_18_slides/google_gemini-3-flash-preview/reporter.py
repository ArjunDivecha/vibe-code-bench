import os
import re
import html
import glob
from datetime import datetime

def generate_report(directory_path="."):
    # 1. Gather all .txt files and sort them numerically/alphabetically
    files = glob.glob(os.path.join(directory_path, "*.txt"))
    # Custom sort to handle slide1.txt, slide10.txt correctly
    files.sort(key=lambda f: [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', f)])

    slides_data = []
    
    for file_path in files:
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            title = lines[0] if lines else "Untitled Slide"
            body = "\n".join(lines[1:]) if len(lines) > 1 else ""
            summary_snippet = lines[0] if lines else ""
            
            slides_data.append({
                'id': re.sub(r'\W+', '', filename),
                'filename': filename,
                'title': title,
                'body': body,
                'summary': summary_snippet
            })

    if not slides_data:
        print("No .txt files found in the directory.")
        return

    # 2. Build the HTML content
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        }}

        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-main);
            background-color: var(--bg-body);
            margin: 0;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 60px;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 10px;
            color: #0f172a;
        }}

        .meta {{
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Action Buttons */
        .actions {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 40px;
        }}

        button {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: var(--shadow);
        }}

        button:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}

        /* Sections */
        section {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }}

        h2 {{
            font-size: 1.5rem;
            margin-top: 0;
            border-bottom: 2px solid var(--border);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        /* Table of Contents */
        .toc-list {{
            list-style: none;
            padding: 0;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
        }}

        .toc-list a {{
            text-decoration: none;
            color: var(--primary);
            font-weight: 500;
            display: block;
            padding: 8px 12px;
            border-radius: 6px;
            transition: background 0.2s;
        }}

        .toc-list a:hover {{
            background: #eff6ff;
        }}

        /* Executive Summary */
        .summary-grid {{
            display: grid;
            gap: 15px;
        }}

        .summary-item {{
            display: flex;
            gap: 15px;
            font-size: 0.95rem;
        }}

        .summary-item .num {{
            font-weight: 800;
            color: var(--primary);
            min-width: 25px;
        }}

        /* Slide Cards */
        .slide-card {{
            page-break-inside: avoid;
            margin-bottom: 50px;
        }}

        .slide-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 20px;
        }}

        .slide-title {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #0f172a;
            margin: 0;
        }}

        .slide-id {{
            font-family: monospace;
            color: var(--text-muted);
            font-size: 0.8rem;
        }}

        .slide-content {{
            white-space: pre-wrap;
            color: #334155;
            font-size: 1.1rem;
            background: #f1f5f9;
            padding: 25px;
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }}

        /* Print Styles */
        @media print {{
            body {{ background: white; padding: 0; }}
            .actions, .toc-section {{ display: none; }}
            section {{ 
                box-shadow: none; 
                border: none; 
                padding: 0;
                margin-bottom: 60px;
            }}
            .slide-card {{ 
                page-break-after: always; 
                padding-top: 40px;
            }}
            .container {{ max-width: 100%; }}
            .slide-content {{ border: 1px solid #eee; background: white; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Presentation Report</h1>
            <div class="meta">Generated on {datetime.now().strftime('%B %d, %Y')} &bull; {len(slides_data)} Slides</div>
        </header>

        <div class="actions">
            <button onclick="window.print()">Print to PDF</button>
        </div>

        <section class="toc-section">
            <h2>Table of Contents</h2>
            <ul class="toc-list">
                {"".join([f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>' for s in slides_data])}
            </ul>
        </section>

        <section id="executive-summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                {"".join([f'<div class="summary-item"><span class="num">{i+1}.</span> <span>{html.escape(s["summary"])}</span></div>' for i, s in enumerate(slides_data)])}
            </div>
        </section>

        <div class="slides-container">
            {"".join([f'''
            <section class="slide-card" id="{s["id"]}">
                <div class="slide-header">
                    <h3 class="slide-title">{html.escape(s["title"])}</h3>
                    <span class="slide-id">{html.escape(s["filename"])}</span>
                </div>
                <div class="slide-content">{html.escape(s["body"])}</div>
            </section>
            ''' for s in slides_data])}
        </div>
    </div>
</body>
</html>
"""
    
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"Successfully generated report.html with {len(slides_data)} slides.")

if __name__ == "__main__":
    # Create dummy data if no txt files exist for demonstration
    existing_txt = glob.glob("*.txt")
    if not existing_txt:
        print("No .txt files found. Creating sample files...")
        samples = {
            "slide1.txt": "Project Introduction\nThis presentation covers the quarterly roadmap.\nWe aim to increase efficiency by 20%.\nKey stakeholders are aligned.",
            "slide2.txt": "Market Analysis\nCompetitors are moving towards AI-driven solutions.\nOur market share remains stable at 15%.\nOpportunities identified in the APAC region.",
            "slide3.txt": "Financial Outlook\nRevenue is up 5% year-over-year.\nOperating costs have decreased due to remote work policies.\nDividend payout scheduled for Q4.",
            "slide4.txt": "Conclusion & Next Steps\nFinalize the budget by next Friday.\nKick off the 'Alpha' project.\nSchedule a follow-up meeting with the engineering team."
        }
        for name, content in samples.items():
            with open(name, "w") as f:
                f.write(content)
    
    generate_report()