import os
import re
import html

# Configuration
SLIDES_DIR = "slides"
OUTPUT_FILE = "report.html"

def natural_sort_key(s):
    """
    Sorts strings containing numbers naturally (e.g., slide1, slide2, slide10).
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def ensure_dummy_data():
    """
    Creates sample slides if the directory doesn't exist.
    """
    if not os.path.exists(SLIDES_DIR):
        print(f"Creating '{SLIDES_DIR}' directory with sample data...")
        os.makedirs(SLIDES_DIR)
        
        samples = [
            ("slide1.txt", "Q1 Financial Overview\n\nRevenue has increased by 20% year-over-year. Our operating margins have stabilized at 15%. Key drivers include the new subscription model and reduced overhead costs."),
            ("slide2.txt", "Product Roadmap 2024\n\n- Q1: Launch Mobile App v2.0\n- Q2: Integrate AI Chatbot\n- Q3: Enterprise API Release\n\nFocus remains on user retention and stickiness."),
            ("slide3.txt", "Marketing Strategy\n\nWe are shifting focus from paid ads to organic content marketing. Influencer partnerships have shown a 3x ROI compared to traditional display ads.\n\nBudget allocation: 40% Content, 30% Influencers, 30% Events."),
            ("slide4.txt", "Team Expansion\n\nHiring priorities:\n1. Senior Backend Engineers\n2. Product Managers\n3. UX Designers\n\nTarget headcount by end of year: 150 employees."),
            ("slide10.txt", "Appendix: Risk Factors\n\n- Market volatility\n- Supply chain disruptions\n- Regulatory changes in the EU region\n\nMitigation strategies are outlined in the attached documentation.")
        ]
        
        for filename, content in samples:
            with open(os.path.join(SLIDES_DIR, filename), "w", encoding="utf-8") as f:
                f.write(content)

def read_slides():
    """
    Reads all .txt files from the slides directory.
    Returns a list of dicts: {'filename': str, 'title': str, 'content': str, 'summary': str}
    """
    files = [f for f in os.listdir(SLIDES_DIR) if f.endswith(".txt")]
    files.sort(key=natural_sort_key)
    
    slides = []
    
    for filename in files:
        path = os.path.join(SLIDES_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            raw_content = f.read().strip()
            
        # Heuristic: Title is filename (cleaner) or first line? Let's use filename for ID, first line for display title if looks like one.
        # Actually, let's just use the filename as the formal ID, and the first non-empty line as the Title.
        
        lines = [l for l in raw_content.split('\n') if l.strip()]
        
        title = filename
        body = raw_content
        summary_text = ""
        
        if lines:
            # Use first line as title if it's short, otherwise filename
            if len(lines[0]) < 50:
                title = lines[0]
                # If we used the first line as title, maybe we keep it in body or remove? 
                # Let's keep the body as is for fidelity.
            
            # Summary: First 2 lines or first 200 chars
            summary_text = " ".join(lines[:2])
            if len(summary_text) > 150:
                summary_text = summary_text[:147] + "..."
        
        slides.append({
            "id": filename,
            "display_title": title,
            "content": body,
            "summary": summary_text
        })
        
    return slides

def generate_html(slides):
    """
    Constructs the HTML report.
    """
    
    # Generate Summary Section HTML
    summary_items_html = ""
    for slide in slides:
        summary_items_html += f"""
        <li class="summary-item">
            <span class="summary-ref">{html.escape(slide['id'])}</span>
            <span class="summary-text">{html.escape(slide['summary'])}</span>
        </li>
        """

    # Generate TOC HTML
    toc_html = ""
    for slide in slides:
        toc_html += f"""
        <a href="#{slide['id']}" class="toc-link">
            {html.escape(slide['display_title'])}
        </a>
        """

    # Generate Slides HTML
    slides_html = ""
    for slide in slides:
        # Convert newlines to <br> or wrap paragraphs
        # Simple approach: split by double newline for paragraphs
        paragraphs = slide['content'].split('\n\n')
        formatted_content = ""
        for p in paragraphs:
            if p.strip():
                # Check if it looks like a list
                if "\n-" in p or p.strip().startswith("-"):
                    # Basic list formatting
                    lines = p.split('\n')
                    list_items = ""
                    for line in lines:
                        clean_line = line.strip()
                        if clean_line.startswith("-"):
                            clean_line = clean_line[1:].strip()
                        list_items += f"<li>{html.escape(clean_line)}</li>"
                    formatted_content += f"<ul>{list_items}</ul>"
                else:
                    formatted_content += f"<p>{html.escape(p)}</p>"

        slides_html += f"""
        <div id="{slide['id']}" class="card slide-card">
            <div class="card-header">
                <h2 class="card-title">{html.escape(slide['display_title'])}</h2>
                <span class="card-meta">{html.escape(slide['id'])}</span>
            </div>
            <div class="card-body">
                {formatted_content}
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
            --bg-color: #f4f6f8;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --accent-color: #3182ce;
            --card-bg: #ffffff;
            --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: var(--font-family);
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 40px;
        }}

        .container {{
            max_width: 900px;
            margin: 0 auto;
        }}

        /* Header & Controls */
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: var(--text-primary);
        }}

        .btn {{
            background-color: var(--text-primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s ease, background-color 0.2s;
            font-size: 0.9rem;
        }}

        .btn:hover {{
            background-color: #000;
            transform: translateY(-1px);
        }}

        /* Sections */
        .section-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-secondary);
            margin-bottom: 15px;
            font-weight: 700;
        }}

        /* Summary Box */
        .summary-box {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 40px;
            border-left: 5px solid var(--accent-color);
        }}

        .summary-list {{
            list-style: none;
        }}

        .summary-item {{
            margin-bottom: 12px;
            display: flex;
            gap: 15px;
        }}

        .summary-ref {{
            font-family: monospace;
            background: #edf2f7;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--text-secondary);
            height: fit-content;
            white-space: nowrap;
        }}

        .summary-text {{
            color: var(--text-primary);
        }}

        /* TOC */
        .toc {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 50px;
        }}

        .toc-link {{
            text-decoration: none;
            background: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            color: var(--text-secondary);
            border: 1px solid #e2e8f0;
            transition: all 0.2s;
            font-weight: 500;
        }}

        .toc-link:hover {{
            border-color: var(--accent-color);
            color: var(--accent-color);
            box-shadow: var(--shadow-sm);
        }}

        /* Cards */
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: var(--shadow-md);
            padding: 40px;
            margin-bottom: 30px;
            transition: transform 0.2s;
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .card:hover {{
            transform: translateY(-2px);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #edf2f7;
        }}

        .card-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .card-meta {{
            font-size: 0.85rem;
            color: #a0aec0;
            font-family: monospace;
        }}

        .card-body p {{
            margin-bottom: 1em;
            color: var(--text-secondary);
        }}

        .card-body ul {{
            margin-bottom: 1em;
            padding-left: 20px;
            color: var(--text-secondary);
        }}
        
        .card-body li {{
            margin-bottom: 0.5em;
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 60px;
            color: #cbd5e0;
            font-size: 0.9rem;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background-color: white;
                padding: 0;
            }}

            .container {{
                max-width: 100%;
                margin: 0;
            }}

            .no-print {{
                display: none !important;
            }}

            .card {{
                box-shadow: none;
                border: 1px solid #e2e8f0;
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            .summary-box {{
                box-shadow: none;
                border: 1px solid #e2e8f0;
                border-left: 5px solid var(--accent-color);
            }}
            
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Slide Report</h1>
        <button class="btn no-print" onclick="window.print()">Print to PDF</button>
    </header>

    <div class="section-title">Executive Summary</div>
    <div class="summary-box">
        <ul class="summary-list">
            {summary_items_html}
        </ul>
    </div>

    <div class="section-title no-print">Table of Contents</div>
    <nav class="toc no-print">
        {toc_html}
    </nav>

    <div class="section-title">Slide Details</div>
    <div class="slides-container">
        {slides_html}
    </div>

    <footer>
        Generated automatically by SlideReporter
    </footer>
</div>

</body>
</html>
    """
    return html_template

def main():
    ensure_dummy_data()
    
    print("Reading slides...")
    slides = read_slides()
    
    if not slides:
        print("No .txt files found in slides/ directory.")
        return

    print(f"Found {len(slides)} slides. Generating report...")
    html_content = generate_html(slides)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Success! Report generated at: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()