import os
import glob
import html
import datetime

def generate_report(directory="."):
    # 1. Gather all .txt files and sort them numerically if possible
    files = glob.glob(os.path.join(directory, "*.txt"))
    # Sort files naturally (e.g., slide1, slide2, slide10)
    files.sort(key=lambda f: [int(c) if c.isdigit() else c.lower() for c in os.path.split(f)[1].replace('.txt', '').split('slide')])

    slides_data = []
    for file_path in files:
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            title = lines[0] if lines else filename
            summary_snippet = lines[1] if len(lines) > 1 else (lines[0][:100] + "..." if lines else "")
            
            slides_data.append({
                'id': filename.replace('.', '_'),
                'title': title,
                'content': content,
                'summary': summary_snippet
            })

    # 2. Build HTML
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
            --text-muted: #64748b;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --border: #e2e8f0;
        }}

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
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
            text-align: center;
            margin-bottom: 60px;
        }}

        h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 10px; color: #0f172a; }}
        .meta {{ color: var(--text-muted); font-size: 0.9rem; }}

        .actions {{
            display: flex;
            justify-content: center;
            margin-bottom: 40px;
            gap: 10px;
        }}

        button {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.2s;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        }}

        button:hover {{ opacity: 0.9; }}
        button:active {{ transform: scale(0.98); }}

        /* Table of Contents */
        .toc {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }}

        .toc h2 {{ margin-top: 0; font-size: 1.25rem; color: var(--primary); }}
        .toc ul {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }}
        .toc a {{ text-decoration: none; color: var(--text-main); font-size: 0.95rem; transition: color 0.2s; }}
        .toc a:hover {{ color: var(--primary); }}

        /* Executive Summary Section */
        .exec-summary {{
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
            border-left: 5px solid var(--primary);
            padding: 30px;
            border-radius: 0 16px 16px 0;
            margin-bottom: 60px;
            box-shadow: var(--shadow);
        }}
        .exec-summary h2 {{ margin-top: 0; }}
        .summary-item {{ margin-bottom: 15px; font-size: 0.95rem; }}
        .summary-item span {{ font-weight: 600; color: var(--primary); margin-right: 8px; }}

        /* Slide Cards */
        .slide-card {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }}

        .slide-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 4px;
            background: var(--primary);
        }}

        .slide-card h3 {{
            margin-top: 0;
            font-size: 1.75rem;
            color: #0f172a;
            border-bottom: 1px solid var(--border);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}

        .slide-content {{
            white-space: pre-wrap;
            color: #334155;
            font-size: 1.1rem;
        }}

        /* Print Styles */
        @media print {{
            body {{ padding: 0; background: white; }}
            .actions, .toc {{ display: none; }}
            .slide-card {{
                box-shadow: none;
                border: 1px solid #eee;
                page-break-after: always;
                margin-bottom: 0;
            }}
            .container {{ max-width: 100%; }}
            .exec-summary {{ box-shadow: none; border: 1px solid #eee; page-break-after: auto; }}
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Presentation Insights</h1>
        <div class="meta">Generated on {datetime.datetime.now().strftime("%B %d, %Y")} • {len(slides_data)} Slides Analyzed</div>
    </header>

    <div class="actions">
        <button onclick="window.print()">Print to PDF</button>
    </div>

    <section class="toc">
        <h2>Table of Contents</h2>
        <ul>
            {"".join(f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>' for s in slides_data)}
        </ul>
    </section>

    <section class="exec-summary">
        <h2>Executive Summary</h2>
        {"".join(f'<div class="summary-item"><span>{i+1}.</span> {html.escape(s["summary"])}</div>' for i, s in enumerate(slides_data))}
    </section>

    <main>
        {"".join(f'''
        <div class="slide-card" id="{s["id"]}">
            <h3>{html.escape(s["title"])}</h3>
            <div class="slide-content">{html.escape(s["content"])}</div>
        </div>
        ''' for s in slides_data)}
    </main>
</div>

</body>
</html>
"""
    
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"Successfully generated report.html with {len(slides_data)} slides.")

if __name__ == "__main__":
    # Create dummy files if none exist for demonstration
    if not glob.glob("*.txt"):
        print("No .txt files found. Creating sample slides...")
        samples = {
            "slide1.txt": "Project Kickoff\nIntroduction to the new Q4 initiative.\nGoals include 20% growth and market expansion.",
            "slide2.txt": "Market Analysis\nCurrent trends show a shift toward AI-driven automation.\nCompetitors are lagging in user experience.",
            "slide3.txt": "Financial Overview\nBudget allocation is finalized.\nMarketing: $50k, Development: $120k, Ops: $30k.",
            "slide4.txt": "Timeline & Next Steps\nPhase 1 starts Monday.\nFinal delivery expected by December 15th."
        }
        for name, content in samples.items():
            with open(name, "w") as f:
                f.write(content)
                
    generate_report()