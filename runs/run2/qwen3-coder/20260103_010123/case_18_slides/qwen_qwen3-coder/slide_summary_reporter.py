import os
import sys
from pathlib import Path

def read_slides(directory):
    """Read all .txt files from the given directory and return their content."""
    slides = []
    slide_files = sorted(Path(directory).glob("slide*.txt"))
    
    for slide_file in slide_files:
        with open(slide_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append({
                'filename': slide_file.name,
                'content': content
            })
    return slides

def generate_summary(slides, lines_per_slide=3):
    """Generate a summary by taking the first few lines of each slide."""
    summary_lines = []
    for slide in slides:
        content_lines = slide['content'].split('\n')
        first_lines = content_lines[:lines_per_slide]
        summary_lines.extend(first_lines)
    return '\n'.join(summary_lines)

def generate_toc(slides):
    """Generate table of contents HTML."""
    toc_entries = []
    for i, slide in enumerate(slides, 1):
        title = slide['filename'].replace('.txt', '').replace('-', ' ').title()
        toc_entries.append(f'<li><a href="#slide-{i}">{title}</a></li>')
    return '\n'.join(toc_entries)

def generate_slide_cards(slides):
    """Generate HTML cards for each slide."""
    cards = []
    for i, slide in enumerate(slides, 1):
        title = slide['filename'].replace('.txt', '').replace('-', ' ').title()
        card = f'''
        <div class="slide-card" id="slide-{i}">
            <h2>{title}</h2>
            <pre>{slide['content']}</pre>
        </div>'''
        cards.append(card)
    return '\n'.join(cards)

def create_html_report(summary, toc, slide_cards, output_file):
    """Create the complete HTML report."""
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #f3f4f6;
            --text: #1f2937;
            --text-light: #6b7280;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --border-radius: 8px;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background-color: #ffffff;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        @media print {{
            body {{
                padding: 0;
                max-width: 100%;
            }}
            
            .no-print {{
                display: none;
            }}
            
            .slide-card {{
                break-inside: avoid;
                margin-bottom: 2rem;
            }}
            
            pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            color: var(--text);
        }}
        
        .summary-box {{
            background-color: var(--secondary);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 2rem 0;
            box-shadow: var(--shadow);
        }}
        
        .summary-box h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .summary-box pre {{
            font-family: inherit;
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        
        .toc-box {{
            background-color: white;
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 2rem 0;
            box-shadow: var(--shadow);
            border: 1px solid #e5e7eb;
        }}
        
        .toc-box h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .toc-box ul {{
            list-style-type: none;
            padding-left: 1rem;
        }}
        
        .toc-box li {{
            margin-bottom: 0.5rem;
            padding: 0.5rem;
            border-radius: 4px;
        }}
        
        .toc-box li:hover {{
            background-color: var(--secondary);
        }}
        
        .toc-box a {{
            text-decoration: none;
            color: var(--text);
            font-weight: 500;
            display: block;
            padding: 0.25rem 0;
        }}
        
        .toc-box a:hover {{
            color: var(--primary);
        }}
        
        .slide-card {{
            background-color: white;
            border-radius: var(--border-radius);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid #e5e7eb;
            page-break-inside: avoid;
        }}
        
        .slide-card h2 {{
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            color: var(--primary);
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--secondary);
        }}
        
        pre {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-size: 1rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            background-color: #f9fafb;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            border: 1px solid #e5e7eb;
            overflow-x: auto;
        }}
        
        .print-button {{
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: var(--border-radius);
            cursor: pointer;
            box-shadow: var(--shadow);
            transition: background-color 0.2s, transform 0.1s;
            margin: 1rem 0 2rem;
        }}
        
        .print-button:hover {{
            background-color: var(--primary-dark);
            transform: translateY(-2px);
        }}
        
        .print-button:active {{
            transform: translateY(0);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .slide-card {{
                padding: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Slide Summary Report</h1>
        <button class="print-button no-print" onclick="window.print()">Print to PDF</button>
    </header>
    
    <div class="summary-box">
        <h2>Summary</h2>
        <pre>{summary}</pre>
    </div>
    
    <div class="toc-box">
        <h2>Table of Contents</h2>
        <ul>
            {toc}
        </ul>
    </div>
    
    <main>
        {slide_cards}
    </main>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    if len(sys.argv) != 2:
        print("Usage: python slide_summary_reporter.py <slides_directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    
    slides = read_slides(directory)
    
    if not slides:
        print("No slide files found in directory")
        sys.exit(1)
    
    summary = generate_summary(slides)
    toc = generate_toc(slides)
    slide_cards = generate_slide_cards(slides)
    
    create_html_report(summary, toc, slide_cards, 'report.html')
    print("Report generated successfully as 'report.html'")

if __name__ == "__main__":
    main()