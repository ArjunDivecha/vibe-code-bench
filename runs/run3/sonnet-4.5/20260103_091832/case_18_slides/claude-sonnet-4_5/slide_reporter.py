#!/usr/bin/env python3
"""
Slide Summary Reporter
Generates a beautiful HTML report from slide text files
"""

import os
import re
from pathlib import Path


def natural_sort_key(filename):
    """Sort filenames naturally (slide1, slide2, ..., slide10, slide11)"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', filename)]


def read_slides(directory='.'):
    """Read all .txt files from directory and return sorted list of slides"""
    slides = []
    
    # Get all .txt files
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    txt_files.sort(key=natural_sort_key)
    
    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # Only add non-empty slides
                    slides.append({
                        'filename': filename,
                        'content': content,
                        'lines': content.split('\n')
                    })
        except Exception as e:
            print(f"Warning: Could not read {filename}: {e}")
    
    return slides


def generate_html(slides):
    """Generate beautiful HTML report"""
    
    # Generate Table of Contents
    toc_items = []
    for i, slide in enumerate(slides, 1):
        title = slide['lines'][0] if slide['lines'] else slide['filename']
        toc_items.append(f'<li><a href="#slide-{i}">{i}. {html_escape(title)}</a></li>')
    
    toc_html = '\n'.join(toc_items)
    
    # Generate Summary (first 2 lines of each slide)
    summary_items = []
    for i, slide in enumerate(slides, 1):
        preview_lines = slide['lines'][:2]
        preview = ' '.join(preview_lines)
        if len(preview) > 150:
            preview = preview[:147] + '...'
        summary_items.append(f'<div class="summary-item"><strong>Slide {i}:</strong> {html_escape(preview)}</div>')
    
    summary_html = '\n'.join(summary_items)
    
    # Generate Slide Cards
    cards_html = []
    for i, slide in enumerate(slides, 1):
        title = slide['lines'][0] if slide['lines'] else slide['filename']
        content_lines = slide['lines'][1:] if len(slide['lines']) > 1 else []
        
        content_html = '<br>'.join([html_escape(line) for line in content_lines])
        
        card = f'''
        <div class="slide-card" id="slide-{i}">
            <div class="slide-header">
                <div class="slide-number">Slide {i}</div>
                <div class="slide-filename">{html_escape(slide['filename'])}</div>
            </div>
            <h2 class="slide-title">{html_escape(title)}</h2>
            <div class="slide-content">{content_html}</div>
        </div>
        '''
        cards_html.append(card)
    
    slides_html = '\n'.join(cards_html)
    
    # Complete HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* === RESET & BASE === */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --text: #1e293b;
            --text-light: #64748b;
            --bg: #ffffff;
            --bg-gray: #f8fafc;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 1rem;
        }}
        
        /* === CONTAINER === */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg);
            border-radius: 24px;
            box-shadow: var(--shadow-xl);
            overflow: hidden;
        }}
        
        /* === HEADER === */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 3rem 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}
        
        .header .subtitle {{
            font-size: 1.125rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .print-button {{
            margin-top: 1.5rem;
            padding: 0.75rem 2rem;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .print-button:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}
        
        /* === CONTENT === */
        .content {{
            padding: 3rem;
        }}
        
        /* === SECTION === */
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section-title {{
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .section-title::before {{
            content: '';
            width: 4px;
            height: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }}
        
        /* === TABLE OF CONTENTS === */
        .toc {{
            background: var(--bg-gray);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--shadow-sm);
        }}
        
        .toc ul {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 0.75rem;
        }}
        
        .toc li {{
            background: white;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}
        
        .toc li:hover {{
            transform: translateX(4px);
            box-shadow: var(--shadow);
        }}
        
        .toc a {{
            display: block;
            padding: 0.875rem 1.25rem;
            color: var(--text);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s ease;
        }}
        
        .toc a:hover {{
            color: var(--primary);
        }}
        
        /* === SUMMARY === */
        .summary {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 16px;
            padding: 2rem;
            border-left: 4px solid #f59e0b;
        }}
        
        .summary-item {{
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(245, 158, 11, 0.2);
            line-height: 1.5;
        }}
        
        .summary-item:last-child {{
            border-bottom: none;
        }}
        
        .summary-item strong {{
            color: #92400e;
            font-weight: 600;
        }}
        
        /* === SLIDE CARDS === */
        .slides {{
            display: grid;
            gap: 2rem;
        }}
        
        .slide-card {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-4px);
        }}
        
        .slide-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--bg-gray);
        }}
        
        .slide-number {{
            font-size: 0.875rem;
            font-weight: 700;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 0.375rem 1rem;
            border-radius: 20px;
            letter-spacing: 0.025em;
        }}
        
        .slide-filename {{
            font-size: 0.875rem;
            color: var(--text-light);
            font-family: 'Monaco', 'Courier New', monospace;
        }}
        
        .slide-title {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 1.25rem;
            line-height: 1.2;
        }}
        
        .slide-content {{
            font-size: 1.0625rem;
            color: var(--secondary);
            line-height: 1.8;
        }}
        
        /* === PRINT STYLES === */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                border-radius: 0;
            }}
            
            .print-button {{
                display: none;
            }}
            
            .slide-card {{
                page-break-inside: avoid;
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
                margin-bottom: 1rem;
            }}
            
            .section {{
                page-break-after: avoid;
                break-after: avoid;
            }}
            
            .section-title {{
                page-break-after: avoid;
                break-after: avoid;
            }}
            
            .toc {{
                page-break-after: always;
                break-after: page;
            }}
            
            .summary {{
                page-break-after: always;
                break-after: page;
            }}
        }}
        
        /* === RESPONSIVE === */
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            .header {{
                padding: 2rem 1.5rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                padding: 1.5rem;
            }}
            
            .section-title {{
                font-size: 1.5rem;
            }}
            
            .toc ul {{
                grid-template-columns: 1fr;
            }}
            
            .slide-card {{
                padding: 1.5rem;
            }}
            
            .slide-title {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Slide Summary Report</h1>
            <div class="subtitle">Generated from {len(slides)} slide(s)</div>
            <button class="print-button" onclick="window.print()">🖨️ Print to PDF</button>
        </div>
        
        <div class="content">
            <!-- Table of Contents -->
            <section class="section">
                <h2 class="section-title">Table of Contents</h2>
                <div class="toc">
                    <ul>
                        {toc_html}
                    </ul>
                </div>
            </section>
            
            <!-- Summary -->
            <section class="section">
                <h2 class="section-title">Summary</h2>
                <div class="summary">
                    {summary_html}
                </div>
            </section>
            
            <!-- Slides -->
            <section class="section">
                <h2 class="section-title">Slides</h2>
                <div class="slides">
                    {slides_html}
                </div>
            </section>
        </div>
    </div>
</body>
</html>'''
    
    return html


def html_escape(text):
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def main():
    """Main function"""
    import sys
    
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    print(f"Reading slides from: {directory}")
    slides = read_slides(directory)
    
    if not slides:
        print("Error: No .txt files found in directory!")
        sys.exit(1)
    
    print(f"Found {len(slides)} slide(s)")
    
    # Generate HTML
    html = generate_html(slides)
    
    # Write to file
    output_file = 'report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_file}")
    print(f"   Open it in a browser and use the 'Print to PDF' button!")


if __name__ == '__main__':
    main()