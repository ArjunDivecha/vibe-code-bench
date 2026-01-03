import os
import glob
import re

def read_slides(directory):
    """Read all .txt files in the directory and return sorted list of (filename, content)"""
    slide_files = glob.glob(os.path.join(directory, "*.txt"))
    slides = []
    
    # Sort files naturally (slide1.txt, slide2.txt, ..., slide10.txt)
    def natural_sort_key(filename):
        return [int(text) if text.isdigit() else text.lower() 
                for text in re.split(r'(\d+)', os.path.basename(filename))]
    
    slide_files.sort(key=natural_sort_key)
    
    for filepath in slide_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append((os.path.basename(filepath), content))
    
    return slides

def generate_summary(slides, lines_per_slide=3):
    """Generate a summary by taking first few lines from each slide"""
    summary_lines = []
    for filename, content in slides:
        content_lines = content.split('\n')
        # Take first few lines, but not more than available
        excerpt = '\n'.join(content_lines[:lines_per_slide])
        summary_lines.append(excerpt)
    
    return '\n\n---\n\n'.join(summary_lines)

def generate_toc(slides):
    """Generate table of contents HTML"""
    toc_html = '<div class="toc">\n<h2>Table of Contents</h2>\n<ul>\n'
    for i, (filename, _) in enumerate(slides, 1):
        slide_title = filename.replace('.txt', '').replace('_', ' ').title()
        toc_html += f'  <li><a href="#slide-{i}">{slide_title}</a></li>\n'
    toc_html += '</ul>\n</div>\n'
    return toc_html

def generate_slide_cards(slides):
    """Generate HTML cards for each slide"""
    cards_html = '<div class="slides-container">\n'
    for i, (filename, content) in enumerate(slides, 1):
        slide_title = filename.replace('.txt', '').replace('_', ' ').title()
        cards_html += f'''<div class="slide-card" id="slide-{i}">
  <div class="slide-header">
    <h3>{slide_title}</h3>
  </div>
  <div class="slide-content">
    <pre>{content}</pre>
  </div>
</div>
'''
    cards_html += '</div>\n'
    return cards_html

def create_html_report(summary, toc, slide_cards, output_file='report.html'):
    """Create the complete HTML report"""
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
            --secondary: #f8fafc;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
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
            color: var(--text);
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
            
            .toc {{
                break-after: page;
            }}
        }}
        
        header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: white;
            border-radius: 12px;
            box-shadow: var(--shadow);
        }}
        
        h1 {{
            color: var(--primary);
            margin-bottom: 1rem;
            font-weight: 700;
            font-size: 2.5rem;
        }}
        
        .print-button {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
            box-shadow: var(--shadow);
        }}
        
        .print-button:hover {{
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        .summary {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
        }}
        
        .summary h2 {{
            color: var(--primary);
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }}
        
        .summary-content {{
            white-space: pre-wrap;
            font-family: inherit;
            color: var(--text-light);
            line-height: 1.7;
        }}
        
        .toc {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
        }}
        
        .toc h2 {{
            color: var(--primary);
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .toc li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .toc li:last-child {{
            border-bottom: none;
        }}
        
        .toc a {{
            text-decoration: none;
            color: var(--text);
            font-weight: 500;
            transition: color 0.2s;
        }}
        
        .toc a:hover {{
            color: var(--primary);
        }}
        
        .slides-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 2rem;
        }}
        
        @media (max-width: 600px) {{
            .slides-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .slide-card {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }}
        
        .slide-header {{
            background: var(--primary);
            color: white;
            padding: 1.25rem;
        }}
        
        .slide-header h3 {{
            font-weight: 600;
            font-size: 1.25rem;
        }}
        
        .slide-content {{
            padding: 1.5rem;
        }}
        
        .slide-content pre {{
            white-space: pre-wrap;
            font-family: inherit;
            margin: 0;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Slide Summary Report</h1>
        <button class="print-button" onclick="window.print()">Print to PDF</button>
    </header>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-content">{summary}</div>
    </div>
    
    {toc}
    
    {slide_cards}
    
    <script>
        // Smooth scrolling for TOC links
        document.querySelectorAll('.toc a').forEach(anchor => {{
            anchor.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """Main function to generate the report"""
    # Get current directory if no argument provided
    directory = input("Enter directory path (or press Enter for current directory): ").strip()
    if not directory:
        directory = "."
    
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return
    
    slides = read_slides(directory)
    
    if not slides:
        print("No .txt files found in the directory")
        return
    
    summary = generate_summary(slides)
    toc = generate_toc(slides)
    slide_cards = generate_slide_cards(slides)
    
    create_html_report(summary, toc, slide_cards)
    print("Report generated successfully as 'report.html'")

if __name__ == "__main__":
    main()