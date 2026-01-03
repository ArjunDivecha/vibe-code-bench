import os
import glob
from pathlib import Path

def read_slide_files(directory):
    """Read all .txt files from the given directory and return their content."""
    slides = []
    slide_files = sorted(glob.glob(os.path.join(directory, "*.txt")), 
                        key=lambda x: int(''.join(filter(str.isdigit, Path(x).stem)) or 0))
    
    for file_path in slide_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append({
                'filename': os.path.basename(file_path),
                'content': content,
                'title': content.split('\n')[0] if content else ''
            })
    return slides

def generate_summary(slides, lines_per_slide=3):
    """Generate a summary by taking the first few lines from each slide."""
    summary_lines = []
    for slide in slides:
        content_lines = slide['content'].split('\n')
        # Take first few lines, but avoid duplicating the title
        start_index = 1 if len(content_lines) > 1 and content_lines[0] == slide['title'] else 0
        summary_lines.extend(content_lines[start_index:start_index + lines_per_slide])
    return '\n'.join(summary_lines)

def generate_toc(slides):
    """Generate HTML for the table of contents."""
    toc_html = '<div class="toc">\n<h2>Table of Contents</h2>\n<ul>\n'
    for i, slide in enumerate(slides, 1):
        toc_html += f'  <li><a href="#slide-{i}">{slide["title"] or f"Slide {i}"}</a></li>\n'
    toc_html += '</ul>\n</div>\n'
    return toc_html

def generate_slide_cards(slides):
    """Generate HTML for slide cards."""
    cards_html = '<div class="slides">\n'
    for i, slide in enumerate(slides, 1):
        cards_html += f'''<div class="card" id="slide-{i}">
  <div class="card-header">
    <h3>{slide["title"] or f"Slide {i}"}</h3>
  </div>
  <div class="card-content">
    <pre>{slide["content"]}</pre>
  </div>
</div>\n'''
    cards_html += '</div>\n'
    return cards_html

def generate_html_report(slides, output_file='report.html'):
    """Generate the complete HTML report."""
    summary = generate_summary(slides)
    toc = generate_toc(slides)
    cards = generate_slide_cards(slides)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary: #4361ee;
            --secondary: #3f37c9;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --light-gray: #e9ecef;
            --border-radius: 8px;
            --box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 2rem;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background-color: #f5f7fb;
            padding: var(--spacing-md);
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        @media print {{
            body {{
                padding: 0;
                background-color: white;
            }}
            
            .no-print {{
                display: none;
            }}
            
            .card {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}
            
            .toc {{
                break-after: page;
            }}
        }}
        
        header {{
            text-align: center;
            margin-bottom: var(--spacing-lg);
            padding: var(--spacing-lg) 0;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
        }}
        
        h1, h2, h3 {{
            margin-bottom: var(--spacing-md);
            font-weight: 600;
        }}
        
        h1 {{
            font-size: 2.5rem;
        }}
        
        h2 {{
            font-size: 1.8rem;
            color: var(--secondary);
        }}
        
        h3 {{
            font-size: 1.4rem;
        }}
        
        .summary {{
            background-color: white;
            padding: var(--spacing-lg);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            margin-bottom: var(--spacing-lg);
            border-left: 4px solid var(--success);
        }}
        
        .summary pre {{
            white-space: pre-wrap;
            font-family: inherit;
            font-size: 1rem;
        }}
        
        .toc {{
            background-color: white;
            padding: var(--spacing-lg);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            margin-bottom: var(--spacing-lg);
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .toc li {{
            padding: var(--spacing-sm) 0;
            border-bottom: 1px solid var(--light-gray);
        }}
        
        .toc li:last-child {{
            border-bottom: none;
        }}
        
        .toc a {{
            text-decoration: none;
            color: var(--primary);
            font-weight: 500;
            transition: color 0.2s;
        }}
        
        .toc a:hover {{
            color: var(--secondary);
        }}
        
        .slides {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: var(--spacing-lg);
        }}
        
        .card {{
            background-color: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }}
        
        .card-header {{
            padding: var(--spacing-md) var(--spacing-lg);
            background-color: var(--primary);
            color: white;
        }}
        
        .card-content {{
            padding: var(--spacing-lg);
        }}
        
        .card-content pre {{
            white-space: pre-wrap;
            font-family: inherit;
            font-size: 0.95rem;
        }}
        
        .print-button {{
            position: fixed;
            bottom: var(--spacing-lg);
            right: var(--spacing-lg);
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: background-color 0.2s, transform 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .print-button:hover {{
            background-color: var(--secondary);
            transform: scale(1.1);
        }}
        
        @media (max-width: 768px) {{
            .slides {{
                grid-template-columns: 1fr;
            }}
            
            body {{
                padding: var(--spacing-sm);
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Slide Summary Report</h1>
        <p>Comprehensive overview of all presentation slides</p>
    </header>
    
    <main>
        <section class="summary no-print">
            <h2>Executive Summary</h2>
            <pre>{summary}</pre>
        </section>
        
        {toc}
        
        {cards}
    </main>
    
    <button class="print-button no-print" onclick="window.print()" title="Print Report">
        🖨️
    </button>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """Main function to generate the slide summary report."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate a slide summary report from text files')
    parser.add_argument('directory', help='Directory containing slide text files')
    parser.add_argument('-o', '--output', default='report.html', help='Output HTML file name')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        return
    
    slides = read_slide_files(args.directory)
    
    if not slides:
        print("Warning: No .txt files found in the directory.")
        return
    
    generate_html_report(slides, args.output)
    print(f"Report generated successfully: {args.output}")

if __name__ == '__main__':
    main()