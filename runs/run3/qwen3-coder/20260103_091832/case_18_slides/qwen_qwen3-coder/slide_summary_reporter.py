import os
import sys
import glob
from pathlib import Path

def read_slide_files(directory):
    """Read all .txt files in the directory and return their content."""
    slides = []
    slide_files = sorted(glob.glob(os.path.join(directory, "*.txt")))
    
    for file_path in slide_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append({
                'filename': os.path.basename(file_path),
                'content': content,
                'preview': ' '.join(content.split()[:30]) + '...' if len(content.split()) > 30 else content
            })
    
    return slides

def generate_summary(slides, lines_per_slide=3):
    """Generate a summary by taking the first few lines from each slide."""
    summary_lines = []
    for slide in slides:
        content_lines = slide['content'].split('\n')
        first_lines = content_lines[:lines_per_slide]
        summary_lines.extend(first_lines)
    
    return '\n'.join(summary_lines)

def generate_toc(slides):
    """Generate table of contents HTML."""
    toc_html = '<ul>\n'
    for i, slide in enumerate(slides, 1):
        toc_html += f'  <li><a href="#slide-{i}">{slide["filename"]}</a></li>\n'
    toc_html += '</ul>\n'
    return toc_html

def generate_slide_cards(slides):
    """Generate HTML cards for each slide."""
    cards_html = ''
    for i, slide in enumerate(slides, 1):
        cards_html += f'''
    <div class="slide-card" id="slide-{i}">
      <div class="slide-header">
        <h2>{slide["filename"]}</h2>
      </div>
      <div class="slide-content">
        <pre>{slide["content"]}</pre>
      </div>
    </div>
'''
    return cards_html

def create_html_report(slides, output_file='report.html'):
    """Create the complete HTML report."""
    summary = generate_summary(slides)
    toc = generate_toc(slides)
    slide_cards = generate_slide_cards(slides)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #f8fafc;
            --text-color: #0f172a;
            --border-color: #cbd5e1;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: #f1f5f9;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        @media print {{
            body {{
                padding: 0;
                background-color: white;
            }}
            
            .print-button {{
                display: none;
            }}
            
            .slide-card {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}
            
            .summary-section, .toc-section {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            color: var(--text-color);
        }}
        
        .print-button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 0.5rem;
            cursor: pointer;
            box-shadow: var(--shadow);
            transition: all 0.2s ease;
            margin-top: 1rem;
        }}
        
        .print-button:hover {{
            background-color: #1d4ed8;
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        .print-button:active {{
            transform: translateY(0);
        }}
        
        .summary-section, .toc-section {{
            background: white;
            border-radius: 0.75rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
        }}
        
        .summary-section h2, .toc-section h2 {{
            font-size: 1.75rem;
            margin-bottom: 1.25rem;
            color: var(--primary-color);
        }}
        
        .summary-content {{
            background-color: var(--secondary-color);
            padding: 1.5rem;
            border-radius: 0.5rem;
            border-left: 4px solid var(--primary-color);
            white-space: pre-wrap;
            font-family: inherit;
        }}
        
        .toc-section ul {{
            list-style-type: none;
            padding: 0;
        }}
        
        .toc-section li {{
            margin-bottom: 0.75rem;
            padding: 0.75rem;
            border-radius: 0.375rem;
            transition: background-color 0.2s;
        }}
        
        .toc-section li:hover {{
            background-color: var(--secondary-color);
        }}
        
        .toc-section a {{
            text-decoration: none;
            color: var(--text-color);
            font-weight: 500;
            display: block;
            font-size: 1.1rem;
        }}
        
        .toc-section a:hover {{
            color: var(--primary-color);
        }}
        
        .slides-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 2rem;
        }}
        
        @media (max-width: 768px) {{
            .slides-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .slide-card {{
            background: white;
            border-radius: 0.75rem;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .slide-header {{
            background-color: var(--primary-color);
            color: white;
            padding: 1.5rem;
        }}
        
        .slide-header h2 {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        .slide-content {{
            padding: 1.5rem;
        }}
        
        .slide-content pre {{
            white-space: pre-wrap;
            font-family: inherit;
            line-height: 1.7;
            color: #334155;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Slide Summary Report</h1>
        <button class="print-button" onclick="window.print()">Print to PDF</button>
    </header>
    
    <section class="summary-section">
        <h2>Summary</h2>
        <div class="summary-content">{summary}</div>
    </section>
    
    <section class="toc-section">
        <h2>Table of Contents</h2>
        {toc}
    </section>
    
    <main class="slides-container">
        {slide_cards}
    </main>
    
    <script>
        // Smooth scrolling for TOC links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    window.scrollTo({{
                        top: target.offsetTop - 20,
                        behavior: 'smooth'
                    }});
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python slide_summary_reporter.py <directory_path>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    
    slides = read_slide_files(directory)
    
    if not slides:
        print("No .txt files found in the directory")
        sys.exit(1)
    
    create_html_report(slides)
    print(f"Report generated successfully: report.html")

if __name__ == "__main__":
    main()