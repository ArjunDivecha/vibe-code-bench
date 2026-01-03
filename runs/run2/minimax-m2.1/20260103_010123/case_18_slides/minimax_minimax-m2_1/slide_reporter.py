#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads text files representing slides and generates a beautiful HTML report.
"""

import os
import glob
import re
from pathlib import Path
from html import escape


def natural_sort_key(s):
    """Sort files naturally by extracting numbers."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def read_slide_files(directory):
    """Read all .txt files from the directory and return sorted list of (filename, content)."""
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    txt_files = sorted(txt_files, key=natural_sort_key)
    
    slides = []
    for filepath in txt_files:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        slides.append((filename, content))
    
    return slides


def extract_title(content):
    """Extract title from slide content (first non-empty line)."""
    lines = content.strip().split('\n')
    for line in lines:
        if line.strip():
            return line.strip()
    return "Untitled Slide"


def extract_summary_lines(content, num_lines=3):
    """Extract first few non-empty lines for summary."""
    lines = content.strip().split('\n')
    summary_lines = []
    for line in lines:
        if line.strip():
            summary_lines.append(line.strip())
            if len(summary_lines) >= num_lines:
                break
    return summary_lines


def generate_html_report(slides, output_path):
    """Generate the premium HTML report."""
    
    # Generate Table of Contents
    toc_html = ""
    for i, (filename, content) in enumerate(slides, 1):
        title = extract_title(content)
        toc_html += f'<li><a href="#slide-{i}"><span class="toc-number">{i}</span><span class="toc-title">{escape(title)}</span></a></li>'
    
    # Generate Summary Section
    summary_html = '<div class="summary-grid">'
    for i, (filename, content) in enumerate(slides, 1):
        title = extract_title(content)
        summary_lines = extract_summary_lines(content, 2)
        summary_html += f'''
        <div class="summary-item">
            <div class="summary-slide-num">{i}</div>
            <div class="summary-content">
                <h4>{escape(title)}</h4>
                <p>{" ".join([escape(line) for line in summary_lines])}</p>
            </div>
        </div>
        '''
    summary_html += '</div>'
    
    # Generate Slide Cards
    cards_html = ""
    for i, (filename, content) in enumerate(slides, 1):
        title = extract_title(content)
        lines = content.strip().split('\n')
        formatted_content = ""
        for line in lines:
            line = escape(line)
            if line.strip():
                if line.startswith('#'):
                    # Header
                    level = min(line.count('#'), 3)
                    formatted_content += f'<h{level+1}>{line.lstrip("#").strip()}</h{level+1}>'
                elif line.startswith('-') or line.startswith('*'):
                    # Bullet point
                    formatted_content += f'<li>{line.lstrip("- *").strip()}</li>'
                else:
                    # Paragraph
                    formatted_content += f'<p>{line}</p>'
            else:
                formatted_content += '<br>'
        
        cards_html += f'''
        <div class="slide-card" id="slide-{i}">
            <div class="slide-header">
                <span class="slide-number">{i}</span>
                <span class="slide-filename">{escape(filename)}</span>
            </div>
            <div class="slide-content">
                <h2 class="slide-title">{escape(title)}</h2>
                <div class="slide-body">
                    {formatted_content}
                </div>
            </div>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* ========================================
           PREMIUM TYPOGRAPHY & CSS VARIABLES
           ======================================== */
        :root {{
            --primary-color: #1a365d;
            --secondary-color: #2c5282;
            --accent-color: #4a7c59;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --text-muted: #718096;
            --bg-primary: #ffffff;
            --bg-secondary: #f7fafc;
            --bg-tertiary: #edf2f7;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 40px rgba(0,0,0,0.12);
            --shadow-xl: 0 20px 60px rgba(0,0,0,0.15);
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        /* ========================================
           BASE STYLES
           ======================================== */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            font-size: 16px;
            line-height: 1.7;
            color: var(--text-primary);
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 100%);
            min-height: 100vh;
        }}

        /* ========================================
           CONTAINER
           ======================================== */
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        /* ========================================
           HEADER
           ======================================== */
        .report-header {{
            text-align: center;
            margin-bottom: 48px;
            padding: 48px 40px;
            background: var(--bg-primary);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        }}

        .report-header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }}

        .report-header .subtitle {{
            font-size: 1.1rem;
            color: var(--text-secondary);
            font-weight: 400;
        }}

        .report-meta {{
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: center;
            gap: 32px;
            font-size: 0.9rem;
            color: var(--text-muted);
        }}

        /* ========================================
           PRINT BUTTON
           ======================================== */
        .print-btn {{
            position: fixed;
            bottom: 32px;
            right: 32px;
            padding: 16px 28px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
        }}

        .print-btn:hover {{
            transform: translateY(-3px) scale(1.02);
            box-shadow: var(--shadow-xl);
        }}

        .print-btn svg {{
            width: 20px;
            height: 20px;
        }}

        /* ========================================
           TABLE OF CONTENTS
           ======================================== */
        .toc-section {{
            background: var(--bg-primary);
            border-radius: var(--radius-lg);
            padding: 32px;
            margin-bottom: 32px;
            box-shadow: var(--shadow-md);
        }}

        .toc-section h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .toc-section h3::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: var(--accent-color);
            border-radius: 2px;
        }}

        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }}

        .toc-list li a {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 18px;
            background: var(--bg-secondary);
            border-radius: var(--radius-md);
            text-decoration: none;
            color: var(--text-primary);
            font-weight: 500;
            transition: var(--transition);
        }}

        .toc-list li a:hover {{
            background: var(--primary-color);
            color: white;
            transform: translateX(4px);
        }}

        .toc-number {{
            width: 32px;
            height: 32px;
            background: var(--bg-tertiary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            color: var(--primary-color);
            transition: var(--transition);
        }}

        .toc-list li a:hover .toc-number {{
            background: rgba(255,255,255,0.2);
            color: white;
        }}

        .toc-title {{
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* ========================================
           SUMMARY SECTION
           ======================================== */
        .summary-section {{
            background: linear-gradient(135deg, #2d3748 0%, #1a365d 100%);
            border-radius: var(--radius-lg);
            padding: 40px;
            margin-bottom: 32px;
            color: white;
        }}

        .summary-section h3 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 28px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .summary-section h3::before {{
            content: '📋';
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}

        .summary-item {{
            background: rgba(255,255,255,0.1);
            border-radius: var(--radius-md);
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: var(--transition);
        }}

        .summary-item:hover {{
            background: rgba(255,255,255,0.15);
            transform: translateY(-2px);
        }}

        .summary-slide-num {{
            display: inline-block;
            width: 28px;
            height: 28px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .summary-content h4 {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #e2e8f0;
        }}

        .summary-content p {{
            font-size: 0.9rem;
            color: #a0aec0;
            line-height: 1.6;
        }}

        /* ========================================
           SLIDE CARDS
           ======================================== */
        .slides-container {{
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}

        .slide-card {{
            background: var(--bg-primary);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            overflow: hidden;
            transition: var(--transition);
            page-break-inside: avoid;
        }}

        .slide-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }}

        .slide-header {{
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
        }}

        .slide-number {{
            width: 36px;
            height: 36px;
            background: var(--primary-color);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1rem;
        }}

        .slide-filename {{
            font-size: 0.85rem;
            color: var(--text-muted);
            font-family: 'Monaco', 'Menlo', monospace;
        }}

        .slide-content {{
            padding: 32px;
        }}

        .slide-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--accent-color);
        }}

        .slide-body {{
            color: var(--text-secondary);
            line-height: 1.8;
        }}

        .slide-body h1,
        .slide-body h2,
        .slide-body h3,
        .slide-body h4 {{
            color: var(--text-primary);
            margin-top: 20px;
            margin-bottom: 12px;
        }}

        .slide-body h1 {{ font-size: 1.5rem; }}
        .slide-body h2 {{ font-size: 1.3rem; }}
        .slide-body h3 {{ font-size: 1.1rem; }}
        .slide-body h4 {{ font-size: 1rem; }}

        .slide-body p {{
            margin-bottom: 12px;
        }}

        .slide-body li {{
            margin-left: 24px;
            margin-bottom: 8px;
        }}

        /* ========================================
           FOOTER
           ======================================== */
        .report-footer {{
            text-align: center;
            padding: 32px;
            color: var(--text-muted);
            font-size: 0.9rem;
        }}

        /* ========================================
           PRINT STYLES
           ======================================== */
        @media print {{
            body {{
                background: white;
                font-size: 12pt;
            }}

            .print-btn {{
                display: none !important;
            }}

            .container {{
                max-width: 100%;
                padding: 20px;
            }}

            .report-header {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            .toc-section {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            .summary-section {{
                background: #f5f5f5;
                color: black;
                border: 1px solid #ddd;
            }}

            .summary-content h4 {{
                color: black;
            }}

            .summary-content p {{
                color: #333;
            }}

            .slide-card {{
                box-shadow: none;
                border: 1px solid #ddd;
                margin-bottom: 20px;
            }}

            .slide-card:hover {{
                transform: none;
            }}

            .slide-header {{
                background: #f5f5f5;
            }}

            /* Page break settings */
            .report-header {{
                page-break-after: avoid;
            }}

            .toc-section {{
                page-break-after: avoid;
            }}

            .summary-section {{
                page-break-inside: avoid;
            }}

            .slide-card {{
                page-break-inside: avoid;
                page-break-after: avoid;
            }}

            a {{
                text-decoration: none;
                color: black;
            }}
        }}

        /* ========================================
           RESPONSIVE
           ======================================== */
        @media (max-width: 768px) {{
            .report-header h1 {{
                font-size: 1.8rem;
            }}

            .summary-grid {{
                grid-template-columns: 1fr;
            }}

            .toc-list {{
                grid-template-columns: 1fr;
            }}

            .report-meta {{
                flex-direction: column;
                gap: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Report Header -->
        <header class="report-header">
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of all slides</p>
            <div class="report-meta">
                <span>📁 {len(slides)} Slides</span>
                <span>📅 Generated on {os.popen('date +"%B %d, %Y"').read().strip()}</span>
            </div>
        </header>

        <!-- Table of Contents -->
        <section class="toc-section">
            <h3>Table of Contents</h3>
            <ul class="toc-list">
                {toc_html}
            </ul>
        </section>

        <!-- Summary Section -->
        <section class="summary-section">
            <h3>Executive Summary</h3>
            {summary_html}
        </section>

        <!-- Slides Container -->
        <div class="slides-container">
            {cards_html}
        </div>

        <!-- Footer -->
        <footer class="report-footer">
            <p>Report generated by Slide Summary Reporter</p>
        </footer>
    </div>

    <!-- Print Button -->
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print to PDF
    </button>
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report generated successfully: {output_path}")
    print(f"📊 Total slides processed: {len(slides)}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate a beautiful HTML report from slide text files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python slide_reporter.py                    # Use current directory
  python slide_reporter.py ./my_slides        # Specify directory
  python slide_reporter.py -o custom.html    # Custom output filename
        '''
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing .txt slide files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output',
        default='report.html',
        help='Output HTML filename (default: report.html)'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"❌ Error: Directory not found: {args.directory}")
        return
    
    # Read slides and generate report
    slides = read_slide_files(args.directory)
    
    if not slides:
        print(f"❌ Error: No .txt files found in directory: {args.directory}")
        return
    
    output_path = os.path.join(args.directory, args.output) if os.path.dirname(args.output) == '' else args.output
    generate_html_report(slides, output_path)


if __name__ == '__main__':
    main()