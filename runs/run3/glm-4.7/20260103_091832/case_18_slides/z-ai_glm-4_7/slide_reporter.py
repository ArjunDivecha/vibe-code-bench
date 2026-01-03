#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads all .txt files in a directory and creates a beautiful HTML report.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime


def read_slides(directory):
    """Read all .txt files from the directory, sorted by filename."""
    slides = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    # Get all .txt files and sort them naturally
    txt_files = sorted(directory_path.glob("*.txt"), key=natural_sort_key)
    
    for filepath in txt_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first line or use filename
        lines = content.strip().split('\n')
        title = lines[0].strip() if lines else filepath.stem
        body = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        slides.append({
            'filename': filepath.name,
            'title': title,
            'content': content,
            'body': body,
            'first_lines': '\n'.join(lines[:3]) if len(lines) > 3 else content
        })
    
    return slides


def natural_sort_key(path):
    """Sort paths naturally (slide1, slide2, slide10 instead of slide1, slide10, slide2)."""
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', path.name)]


def generate_summary(slides):
    """Generate a summary combining first few lines of every slide."""
    if not slides:
        return "No slides found."
    
    summary_parts = []
    for i, slide in enumerate(slides, 1):
        first_lines = slide['first_lines'].strip()
        summary_parts.append(f"**Slide {i}:** {first_lines}")
    
    return '\n\n'.join(summary_parts)


def generate_html(slides, output_path="report.html"):
    """Generate the HTML report."""
    summary_text = generate_summary(slides)
    
    # Convert markdown-style bold to HTML
    summary_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', summary_text)
    summary_html = summary_html.replace('\n\n', '</p><p>').replace('\n', '<br>')
    
    # Generate TOC
    toc_items = []
    for i, slide in enumerate(slides, 1):
        anchor = f"slide-{i}"
        toc_items.append(f'<a href="#{anchor}" class="toc-item">Slide {i}: {escape_html(slide["title"])}</a>')
    
    # Generate slide cards
    slide_cards = []
    for i, slide in enumerate(slides, 1):
        anchor = f"slide-{i}"
        content_html = escape_html(slide['content']).replace('\n', '<br>')
        
        card = f'''
        <div class="slide-card" id="{anchor}">
            <div class="slide-header">
                <span class="slide-number">Slide {i}</span>
                <span class="slide-filename">{escape_html(slide['filename'])}</span>
            </div>
            <h2 class="slide-title">{escape_html(slide['title'])}</h2>
            <div class="slide-content">{content_html}</div>
        </div>
        '''
        slide_cards.append(card)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: var(--text);
            line-height: 1.7;
            min-height: 100vh;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        /* Header */
        header {{
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.6s ease-out;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }}

        .subtitle {{
            color: var(--text-light);
            font-size: 1.1rem;
            font-weight: 400;
        }}

        /* Print Button */
        .print-btn {{
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}

        .print-btn:active {{
            transform: translateY(0);
        }}

        .print-btn svg {{
            width: 20px;
            height: 20px;
        }}

        /* Section Styles */
        section {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            animation: fadeInUp 0.6s ease-out;
            animation-fill-mode: both;
        }}

        section:nth-child(2) {{ animation-delay: 0.1s; }}
        section:nth-child(3) {{ animation-delay: 0.2s; }}
        section:nth-child(4) {{ animation-delay: 0.3s; }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .section-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 2px;
        }}

        /* Table of Contents */
        .toc {{
            display: grid;
            gap: 0.75rem;
        }}

        .toc-item {{
            display: flex;
            align-items: center;
            padding: 1rem 1.25rem;
            background: var(--bg);
            border-radius: 12px;
            text-decoration: none;
            color: var(--text);
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}

        .toc-item:hover {{
            background: white;
            border-color: var(--primary);
            box-shadow: var(--shadow-md);
            transform: translateX(4px);
        }}

        .toc-item::before {{
            content: '→';
            margin-right: 0.75rem;
            color: var(--primary);
            opacity: 0;
            transition: opacity 0.2s ease;
        }}

        .toc-item:hover::before {{
            opacity: 1;
        }}

        /* Summary Section */
        .summary-content {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            font-size: 1rem;
            color: var(--text);
            border-left: 4px solid var(--primary);
        }}

        .summary-content strong {{
            color: var(--primary-dark);
            font-weight: 700;
        }}

        /* Slide Cards */
        .slides-container {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .slide-card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            page-break-inside: avoid;
        }}

        .slide-card:hover {{
            box-shadow: var(--shadow-lg);
            border-color: var(--primary);
        }}

        .slide-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .slide-number {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .slide-filename {{
            color: var(--text-light);
            font-size: 0.85rem;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            background: var(--bg);
            padding: 0.35rem 0.75rem;
            border-radius: 8px;
        }}

        .slide-title {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 1.25rem;
            line-height: 1.3;
        }}

        .slide-content {{
            color: var(--text);
            font-size: 1.05rem;
            line-height: 1.8;
            white-space: pre-wrap;
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        /* Animations */
        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                max-width: 100%;
            }}

            .print-btn {{
                display: none;
            }}

            section {{
                box-shadow: none;
                border: 1px solid var(--border);
                page-break-inside: avoid;
                margin-bottom: 1rem;
            }}

            .slide-card {{
                box-shadow: none;
                border: 1px solid var(--border);
                page-break-inside: avoid;
                page-break-after: always;
            }}

            .slide-card:last-child {{
                page-break-after: auto;
            }}

            h1 {{
                -webkit-text-fill-color: var(--primary-dark);
                background: none;
            }}

            .summary-content {{
                background: white;
                border: 1px solid var(--border);
            }}
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            h1 {{
                font-size: 1.75rem;
            }}

            .print-btn {{
                top: 1rem;
                right: 1rem;
                padding: 0.6rem 1rem;
                font-size: 0.85rem;
            }}

            section {{
                padding: 1.5rem;
            }}

            .slide-card {{
                padding: 1.5rem;
            }}

            .slide-title {{
                font-size: 1.35rem;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print to PDF
    </button>

    <div class="container">
        <header>
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </header>

        <section>
            <h2 class="section-title">Table of Contents</h2>
            <div class="toc">
                {''.join(toc_items)}
            </div>
        </section>

        <section>
            <h2 class="section-title">Summary</h2>
            <div class="summary-content">
                <p>{summary_html}</p>
            </div>
        </section>

        <section class="slides-section">
            <h2 class="section-title">Slides ({len(slides)})</h2>
            <div class="slides-container">
                {''.join(slide_cards)}
            </div>
        </section>

        <footer>
            <p>Slide Summary Report • {len(slides)} slides • Generated by Slide Reporter</p>
        </footer>
    </div>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path


def escape_html(text):
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


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
    
    try:
        print(f"Reading slides from: {args.directory}")
        slides = read_slides(args.directory)
        print(f"Found {len(slides)} slide(s)")
        
        if not slides:
            print("Warning: No .txt files found in the directory.")
            return
        
        output_path = generate_html(slides, args.output)
        print(f"✓ Report generated: {output_path}")
        print(f"  Open {output_path} in your browser to view the report.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()