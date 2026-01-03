#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads text files from a directory and generates a beautiful HTML report.
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime


def read_slide_files(directory):
    """Read all .txt files from the directory and return sorted list."""
    txt_files = sorted(glob.glob(os.path.join(directory, "*.txt")))
    slides = []
    
    for filepath in txt_files:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append({
                'filename': filename,
                'title': filename.replace('.txt', '').replace('_', ' ').title(),
                'content': content
            })
    
    return slides


def extract_summary(content, max_lines=2):
    """Extract first few lines from content for summary."""
    lines = content.split('\n')
    summary_lines = [line.strip() for line in lines[:max_lines] if line.strip()]
    return ' '.join(summary_lines)


def generate_html(slides, output_path='report.html'):
    """Generate the HTML report from slide data."""
    
    # Generate Table of Contents
    toc_items = []
    for i, slide in enumerate(slides, 1):
        safe_id = re.sub(r'[^a-zA-Z0-9-]', '-', slide['filename']).lower()
        toc_items.append(f'<li><a href="#{safe_id}">{i}. {slide["title"]}</a></li>')
    
    # Generate Summary
    summary_items = []
    for slide in slides:
        summary = extract_summary(slide['content'])
        safe_id = re.sub(r'[^a-zA-Z0-9-]', '-', slide['filename']).lower()
        summary_items.append(f'''
            <div class="summary-item">
                <strong><a href="#{safe_id}">{slide['title']}</a>:</strong>
                <span>{summary}</span>
            </div>
        ''')
    
    # Generate Slide Cards
    slide_cards = []
    for slide in slides:
        safe_id = re.sub(r'[^a-zA-Z0-9-]', '-', slide['filename']).lower()
        formatted_content = format_slide_content(slide['content'])
        slide_cards.append(f'''
            <div class="slide-card" id="{safe_id}">
                <div class="slide-header">
                    <span class="slide-number">Slide {slides.index(slide) + 1}</span>
                    <h2 class="slide-title">{slide['title']}</h2>
                </div>
                <div class="slide-content">
                    {formatted_content}
                </div>
            </div>
        ''')
    
    # HTML Template
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* CSS Variables */
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            --radius: 12px;
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}

        /* Reset & Base */
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: var(--font-sans);
            background: var(--bg-body);
            color: var(--text-primary);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* Container */
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 48px;
            padding-bottom: 32px;
            border-bottom: 1px solid var(--border);
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 12px;
        }}

        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 1.125rem;
            font-weight: 400;
        }}

        .header .meta {{
            margin-top: 16px;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* Print Button */
        .print-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 24px;
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-md);
        }}

        .print-btn:hover {{
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }}

        .print-btn:active {{
            transform: translateY(0);
        }}

        .print-btn svg {{
            width: 18px;
            height: 18px;
        }}

        /* Sections */
        .section {{
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 32px;
            margin-bottom: 32px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border);
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            margin-bottom: 24px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .section-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: var(--primary);
            border-radius: 2px;
        }}

        /* Table of Contents */
        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 12px;
        }}

        .toc-list li {{
            margin: 0;
        }}

        .toc-list a {{
            display: block;
            padding: 12px 16px;
            background: var(--bg-body);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .toc-list a:hover {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            transform: translateX(4px);
        }}

        /* Summary Section */
        .summary-grid {{
            display: grid;
            gap: 16px;
        }}

        .summary-item {{
            padding: 16px;
            background: var(--bg-body);
            border-radius: 8px;
            border-left: 3px solid var(--primary);
        }}

        .summary-item strong {{
            display: block;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .summary-item strong a {{
            color: inherit;
            text-decoration: none;
        }}

        .summary-item strong a:hover {{
            text-decoration: underline;
        }}

        .summary-item span {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}

        /* Slide Cards */
        .slide-card {{
            background: var(--bg-card);
            border-radius: var(--radius);
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border);
            margin-bottom: 32px;
            overflow: hidden;
            page-break-inside: avoid;
        }}

        .slide-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            padding: 24px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .slide-number {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            backdrop-filter: blur(10px);
        }}

        .slide-title {{
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.025em;
        }}

        .slide-content {{
            padding: 32px;
            color: var(--text-secondary);
            white-space: pre-wrap;
            line-height: 1.8;
        }}

        .slide-content p {{
            margin-bottom: 16px;
        }}

        .slide-content p:last-child {{
            margin-bottom: 0;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 64px;
            padding-top: 32px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                color: black;
            }}

            .container {{
                max-width: 100%;
                padding: 0;
            }}

            .print-btn {{
                display: none;
            }}

            .section {{
                box-shadow: none;
                border: 1px solid #ccc;
                page-break-inside: avoid;
            }}

            .slide-card {{
                box-shadow: none;
                border: 1px solid #ccc;
                page-break-inside: avoid;
                margin-bottom: 24px;
            }}

            .slide-header {{
                background: #f0f0f0 !important;
                color: black !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .slide-number {{
                background: #ddd !important;
                color: black !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .slide-title {{
                color: black !important;
            }}

            .header h1 {{
                background: none;
                -webkit-text-fill-color: black;
                color: black;
            }}

            .toc-list a {{
                border: 1px solid #ccc;
                color: black;
            }}

            .toc-list a:hover {{
                background: none;
                color: black;
                transform: none;
            }}

            .summary-item {{
                border-left-color: #333;
            }}

            a {{
                text-decoration: none;
                color: black;
            }}
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            .container {{
                padding: 24px 16px;
            }}

            .header h1 {{
                font-size: 1.875rem;
            }}

            .section {{
                padding: 24px;
            }}

            .slide-header {{
                padding: 20px;
                flex-direction: column;
                align-items: flex-start;
            }}

            .slide-content {{
                padding: 24px;
            }}

            .toc-list {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of presentation slides</p>
            <p class="meta">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} • {len(slides)} slides</p>
            <button class="print-btn" onclick="window.print()">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Print to PDF
            </button>
        </header>

        <section class="section">
            <h2 class="section-title">Table of Contents</h2>
            <ul class="toc-list">
                {''.join(toc_items)}
            </ul>
        </section>

        <section class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="summary-grid">
                {''.join(summary_items)}
            </div>
        </section>

        <section class="slides-container">
            <h2 class="section-title" style="margin-bottom: 32px;">Slide Details</h2>
            {''.join(slide_cards)}
        </section>

        <footer class="footer">
            <p>Slide Summary Report • Generated with Python</p>
        </footer>
    </div>
</body>
</html>'''
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return output_path


def format_slide_content(content):
    """Format slide content into paragraphs."""
    paragraphs = content.split('\n\n')
    formatted = []
    for para in paragraphs:
        para = para.strip()
        if para:
            # Convert single line breaks to <br>, double breaks become separate paragraphs
            lines = para.split('\n')
            single_line = ' '.join(line.strip() for line in lines if line.strip())
            if single_line:
                formatted.append(f'<p>{single_line}</p>')
    return ''.join(formatted)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate a beautiful HTML report from slide text files.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing slide .txt files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output',
        default='report.html',
        help='Output HTML file path (default: report.html)'
    )
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found.")
        return 1
    
    # Read slides
    slides = read_slide_files(args.directory)
    
    if not slides:
        print(f"No .txt files found in '{args.directory}'")
        return 1
    
    # Generate report
    output_path = generate_html(slides, args.output)
    
    print(f"✓ Generated report: {output_path}")
    print(f"  - {len(slides)} slides processed")
    print(f"  - Open {output_path} in your browser to view")
    
    return 0


if __name__ == '__main__':
    exit(main())