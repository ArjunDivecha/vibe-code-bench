#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report
"""

import os
import sys
from pathlib import Path
import re

def natural_sort_key(filename):
    """Sort filenames naturally (slide1, slide2, ..., slide10, slide11)"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', filename)]

def read_slides(directory='.'):
    """Read all .txt files from the directory"""
    path = Path(directory)
    slides = []
    
    # Find all .txt files
    txt_files = sorted(path.glob('*.txt'), key=lambda x: natural_sort_key(x.name))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # Only add non-empty files
                    slides.append({
                        'filename': txt_file.name,
                        'title': txt_file.stem.replace('_', ' ').title(),
                        'content': content
                    })
        except Exception as e:
            print(f"Warning: Could not read {txt_file}: {e}", file=sys.stderr)
    
    return slides

def get_summary_lines(content, num_lines=2):
    """Extract first N non-empty lines from content"""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    return ' '.join(lines[:num_lines])

def escape_html(text):
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def generate_html(slides):
    """Generate the complete HTML report"""
    
    # Generate summary section
    summary_items = []
    for i, slide in enumerate(slides, 1):
        summary_text = get_summary_lines(slide['content'])
        summary_items.append(f'''
            <div class="summary-item">
                <span class="summary-number">{i}</span>
                <span class="summary-text">{escape_html(summary_text)}</span>
            </div>
        ''')
    
    # Generate table of contents
    toc_items = []
    for i, slide in enumerate(slides, 1):
        toc_items.append(f'''
            <li><a href="#slide-{i}">{escape_html(slide['title'])}</a></li>
        ''')
    
    # Generate slide cards
    slide_cards = []
    for i, slide in enumerate(slides, 1):
        # Convert content to HTML paragraphs
        paragraphs = [f'<p>{escape_html(para.strip())}</p>' 
                     for para in slide['content'].split('\n\n') if para.strip()]
        
        # If no paragraph breaks, split by single newlines
        if len(paragraphs) <= 1:
            paragraphs = [f'<p>{escape_html(line)}</p>' 
                         for line in slide['content'].split('\n') if line.strip()]
        
        content_html = '\n'.join(paragraphs)
        
        slide_cards.append(f'''
        <div class="slide-card" id="slide-{i}">
            <div class="slide-header">
                <span class="slide-number">Slide {i}</span>
                <h2 class="slide-title">{escape_html(slide['title'])}</h2>
            </div>
            <div class="slide-content">
                {content_html}
            </div>
            <div class="slide-footer">
                <span class="slide-source">{escape_html(slide['filename'])}</span>
            </div>
        </div>
        ''')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* Reset and Base Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --accent-color: #3b82f6;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --text-light: #9ca3af;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-card: #ffffff;
            --border-color: #e5e7eb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 1rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-secondary);
            border-radius: 16px;
            box-shadow: var(--shadow-xl);
            overflow: hidden;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
            position: relative;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}
        
        .header p {{
            font-size: 1.125rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .print-button {{
            position: absolute;
            top: 2rem;
            right: 2rem;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .print-button:hover {{
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        /* Content Area */
        .content {{
            padding: 3rem 2rem;
            background: var(--bg-primary);
        }}
        
        /* Summary Section */
        .summary-section {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-lg);
            border-left: 6px solid #f59e0b;
        }}
        
        .summary-section h2 {{
            color: #92400e;
            font-size: 1.75rem;
            margin-bottom: 1.5rem;
            font-weight: 700;
        }}
        
        .summary-item {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            align-items: flex-start;
        }}
        
        .summary-number {{
            background: #f59e0b;
            color: white;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
            box-shadow: var(--shadow-md);
        }}
        
        .summary-text {{
            color: #78350f;
            line-height: 1.8;
            flex: 1;
        }}
        
        /* Table of Contents */
        .toc-section {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-lg);
            border-left: 6px solid var(--primary-color);
        }}
        
        .toc-section h2 {{
            color: var(--text-primary);
            font-size: 1.75rem;
            margin-bottom: 1.5rem;
            font-weight: 700;
        }}
        
        .toc-section ul {{
            list-style: none;
            display: grid;
            gap: 0.75rem;
        }}
        
        .toc-section li {{
            position: relative;
            padding-left: 1.5rem;
        }}
        
        .toc-section li::before {{
            content: "→";
            position: absolute;
            left: 0;
            color: var(--primary-color);
            font-weight: 700;
        }}
        
        .toc-section a {{
            color: var(--text-primary);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            display: inline-block;
        }}
        
        .toc-section a:hover {{
            color: var(--primary-color);
            transform: translateX(4px);
        }}
        
        /* Slides Section */
        .slides-section {{
            margin-top: 3rem;
        }}
        
        .section-title {{
            font-size: 2rem;
            color: var(--text-primary);
            margin-bottom: 2rem;
            font-weight: 700;
            text-align: center;
        }}
        
        /* Slide Cards */
        .slide-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-4px);
        }}
        
        .slide-header {{
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .slide-number {{
            display: inline-block;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 0.375rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            box-shadow: var(--shadow-md);
        }}
        
        .slide-title {{
            font-size: 1.75rem;
            color: var(--text-primary);
            font-weight: 700;
            margin-top: 0.5rem;
        }}
        
        .slide-content {{
            color: var(--text-secondary);
            line-height: 1.8;
            font-size: 1.0625rem;
        }}
        
        .slide-content p {{
            margin-bottom: 1rem;
        }}
        
        .slide-content p:last-child {{
            margin-bottom: 0;
        }}
        
        .slide-footer {{
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
        }}
        
        .slide-source {{
            color: var(--text-light);
            font-size: 0.875rem;
            font-style: italic;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
            font-size: 0.875rem;
            background: var(--bg-secondary);
        }}
        
        /* Print Styles */
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
            
            .header {{
                background: var(--primary-color);
                page-break-after: avoid;
            }}
            
            .summary-section,
            .toc-section {{
                page-break-inside: avoid;
                break-inside: avoid;
                page-break-after: always;
                break-after: page;
            }}
            
            .slide-card {{
                page-break-inside: avoid;
                break-inside: avoid;
                page-break-after: always;
                break-after: page;
                box-shadow: none;
                border: 1px solid var(--border-color);
            }}
            
            .slide-card:hover {{
                transform: none;
                box-shadow: none;
            }}
            
            .footer {{
                page-break-before: avoid;
            }}
            
            a {{
                color: inherit;
                text-decoration: none;
            }}
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.875rem;
            }}
            
            .print-button {{
                position: static;
                display: block;
                margin: 1rem auto 0;
            }}
            
            .content {{
                padding: 2rem 1rem;
            }}
            
            .slide-card {{
                padding: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Slide Summary Report</h1>
            <p>Generated from {len(slides)} slides</p>
            <button class="print-button" onclick="window.print()">🖨️ Print to PDF</button>
        </div>
        
        <div class="content">
            <!-- Summary Section -->
            <div class="summary-section">
                <h2>📋 Executive Summary</h2>
                {''.join(summary_items)}
            </div>
            
            <!-- Table of Contents -->
            <div class="toc-section">
                <h2>📑 Table of Contents</h2>
                <ul>
                    {''.join(toc_items)}
                </ul>
            </div>
            
            <!-- Slides Section -->
            <div class="slides-section">
                <h3 class="section-title">📄 Detailed Slides</h3>
                {''.join(slide_cards)}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Slide Summary Reporter | Total Slides: {len(slides)}</p>
        </div>
    </div>
</body>
</html>'''
    
    return html

def main():
    """Main function"""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    print(f"Reading slides from: {directory}")
    
    # Read slides
    slides = read_slides(directory)
    
    if not slides:
        print("Error: No .txt files found in the directory!")
        sys.exit(1)
    
    print(f"Found {len(slides)} slides")
    
    # Generate HTML
    html_content = generate_html(slides)
    
    # Write to file
    output_file = 'report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Report generated: {output_file}")
    print(f"  Open it in a browser and click 'Print to PDF' to save as PDF")

if __name__ == '__main__':
    main()