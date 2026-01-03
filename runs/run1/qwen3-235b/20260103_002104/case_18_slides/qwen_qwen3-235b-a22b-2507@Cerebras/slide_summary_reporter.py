import os
import re
from typing import List, Tuple

def read_slides(directory: str) -> List[Tuple[str, str]]:
    """Read all .txt files from directory and return list of (title, content)."""
    slides = []
    # Get all .txt files and sort them to ensure order (slide1, slide2, etc.)
    txt_files = sorted([
        f for f in os.listdir(directory)
        if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f))
    ], key=lambda x: natural_sort_key(x))
    
    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        # Use filename (without extension) as title
        title = os.path.splitext(filename)[0].replace('_', ' ').title()
        slides.append((title, content))
    
    return slides

def natural_sort_key(text: str) -> List:
    """Key function for natural sorting (slide10 comes after slide2)."""
    def convert(c):
        return int(c) if c.isdigit() else c.lower()
    return [convert(c) for c in re.split('([0-9]+)', text)]

def generate_summary(slides: List[Tuple[str, str]], line_limit: int = 3) -> str:
    """Generate a summary by taking first few lines from each slide."""
    summary_lines = []
    for title, content in slides:
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        relevant_lines = lines[:line_limit]
        if relevant_lines:
            snippet = ' '.join(relevant_lines)
            # Trim long snippets
            if len(snippet) > 120:
                snippet = snippet[:117] + '...'
            summary_lines.append(f"<strong>{title}:</strong> {snippet}")
    
    return "<br>".join(summary_lines)

def generate_html_report(slides: List[Tuple[str, str]], output_file: str):
    """Generate a beautiful HTML report with TOC, summary, and styled cards."""
    
    # Generate TOC
    toc_items = [
        f'<li><a href="#slide-{i+1}">{title}</a></li>'
        for i, (title, _) in enumerate(slides)
    ]
    toc_html = "<ul>\n" + "\n".join(toc_items) + "\n</ul>"
    
    # Generate summary
    summary_html = generate_summary(slides)
    
    # Generate slide cards
    slide_cards = []
    for i, (title, content) in enumerate(slides):
        # Preserve line breaks in content
        content_formatted = content.replace('\n', '<br>')
        card = f"""
        <div class="slide-card" id="slide-{i+1}">
            <h2>{title}</h2>
            <div class="content">
                {content_formatted}
            </div>
        </div>
        """
        slide_cards.append(card)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --bg-light: #f8f9fa;
            --bg-white: #ffffff;
            --primary: #4a6fa5;
            --primary-dark: #3a5a8c;
            --gray-dark: #343a40;
            --gray: #6c757d;
            --shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            --radius: 12px;
            --transition: all 0.3s ease;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: var(--gray-dark);
            background-color: var(--bg-light);
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}

        @media print {{
            body {{
                padding: 0;
                background: white;
            }}
            .no-print {{
                display: none !important;
            }}
            .slide-card {{
                page-break-inside: avoid;
                break-inside: avoid;
                margin-bottom: 1rem;
            }}
            h1, h2 {{
                break-after: avoid;
            }}
            pre {{
                break-inside: avoid;
            }}
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid #eee;
        }}

        h1 {{
            color: var(--primary-dark);
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }}

        .subtitle {{
            color: var(--gray);
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }}

        .actions {{
            margin: 1.5rem 0;
            text-align: center;
        }}

        .btn-print {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 28px;
            font-size: 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(74, 111, 165, 0.3);
            transition: var(--transition);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .btn-print:hover {{
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(74, 111, 165, 0.4);
        }}

        .section {{
            background: var(--bg-white);
            padding: 2rem;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            margin-bottom: 2.5rem;
            overflow: hidden;
        }}

        .section h2 {{
            color: var(--primary-dark);
            margin-bottom: 1.2rem;
            font-size: 1.6rem;
            font-weight: 600;
            border-bottom: 2px solid var(--bg-light);
            padding-bottom: 0.5rem;
            display: inline-block;
        }}

        .toc-container ul {{
            list-style: none;
            columns: 2;
            gap: 2rem;
        }}

        .toc-container li {{
            margin-bottom: 0.8rem;
            break-inside: avoid;
        }}

        .toc-container a {{
            text-decoration: none;
            color: var(--primary);
            font-weight: 500;
            font-size: 1.05rem;
            transition: var(--transition);
            position: relative;
        }}

        .toc-container a::before {{
            content: '›';
            margin-right: 8px;
            opacity: 0.7;
            font-weight: bold;
        }}

        .toc-container a:hover {{
            color: var(--primary-dark);
            transform: translateX(4px);
        }}

        .summary-content {{
            line-height: 2;
            color: var(--gray);
            padding-left: 0.5rem;
        }}

        .slide-card {{
            background: var(--bg-white);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 2.2rem;
            margin-bottom: 2.5rem;
            transition: var(--transition);
            border: 1px solid rgba(0, 0, 0, 0.05);
            break-inside: avoid;
        }}

        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
        }}

        .slide-card h2 {{
            color: var(--primary-dark);
            margin-bottom: 1.3rem;
            font-size: 1.8rem;
            font-weight: 600;
            position: relative;
            padding-bottom: 0.5rem;
        }}

        .slide-card h2::after {{
            content: '';
            position: absolute;
            left: 0;
            bottom: 0;
            width: 60px;
            height: 3px;
            background: var(--primary);
            border-radius: 3px;
        }}

        .slide-card .content {{
            color: var(--gray-dark);
            line-height: 1.8;
            font-size: 1.1rem;
        }}

        .slide-card pre {{
            background: #f1f3f5;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #e0e0e0;
            margin: 1rem 0;
            font-family: 'Cascadia Code', 'Courier New', monospace;
            font-size: 0.95rem;
        }}

        blockquote {{
            border-left: 4px solid var(--primary);
            color: var(--gray);
            padding-left: 1.2rem;
            margin: 1.5rem 0;
            font-style: italic;
        }}

        code {{
            background: #f1f3f5;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Cascadia Code', 'Courier New', monospace;
            font-size: 0.9em;
            color: #d73a49;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            header {{
                margin-bottom: 2rem;
            }}
            h1 {{
                font-size: 2rem;
            }}
            .section {{
                padding: 1.5rem;
            }}
            .toc-container ul {{
                columns: 1;
            }}
            .slide-card {{
                padding: 1.5rem;
            }}
            .slide-card h2 {{
                font-size: 1.5rem;
            }}
            .slide-card .content {{
                font-size: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Slide Summary Report</h1>
        <p class="subtitle">Generated from text slide files</p>
    </header>

    <div class="actions no-print">
        <button class="btn-print" onclick="window.print()">🖨️ Print to PDF</button>
    </div>

    <div class="section">
        <h2>Table of Contents</h2>
        <div class="toc-container">
            {toc_html}
        </div>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="summary-content">
            {summary_html}
        </div>
    </div>

    {''.join(slide_cards)}

    <div class="actions no-print" style="margin-top: 3rem; text-align: center; color: #999; font-size: 0.9rem;">
        <p>End of Report</p>
    </div>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Report generated: {output_file}")
    print(f"📁 Contains {len(slides)} slides")
    print("💡 Tip: Open the HTML file and click 'Print to PDF' to generate a PDF.")

def main():
    # Use current directory as default
    directory = "."
    output_file = "report.html"
    
    print("🔍 Searching for slide files...")
    slides = read_slides(directory)
    
    if not slides:
        print("❌ No .txt files found in the directory.")
        print("📌 Please add text files like 'slide1.txt', 'slide2.txt', etc.")
        return
    
    print(f"📄 Found {len(slides)} slides. Generating HTML report...")
    generate_html_report(slides, output_file)

if __name__ == "__main__":
    main()