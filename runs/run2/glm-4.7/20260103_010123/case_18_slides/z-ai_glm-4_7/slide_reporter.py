#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report.
"""

import os
import re
from pathlib import Path
from datetime import datetime


def read_slide_files(directory):
    """Read all .txt files from the specified directory."""
    slides = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    # Get all .txt files and sort them naturally
    txt_files = sorted(directory_path.glob("*.txt"), key=natural_sort_key)
    
    for filepath in txt_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            slides.append({
                'filename': filepath.name,
                'title': filepath.stem.replace('_', ' ').replace('-', ' ').title(),
                'content': content.strip(),
                'lines': content.strip().split('\n')
            })
    
    return slides


def natural_sort_key(path):
    """Sort paths naturally (slide1, slide2, slide10 instead of slide1, slide10, slide2)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', path.name)]


def generate_summary(slides, lines_per_slide=3):
    """Generate a summary combining the first few lines of each slide."""
    summary_parts = []
    
    for slide in slides:
        preview_lines = [line.strip() for line in slide['lines'][:lines_per_slide] if line.strip()]
        if preview_lines:
            summary_parts.append(f"<strong>{slide['title']}:</strong> {' '.join(preview_lines)}")
    
    return summary_parts


def escape_html(text):
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def generate_html_report(slides, output_path='report.html'):
    """Generate a beautiful HTML report from slides."""
    
    summary_items = generate_summary(slides)
    
    html_template = f"""<!DOCTYPE html>
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
            --accent: #0ea5e9;
            --background: #f8fafc;
            --surface: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--background);
            color: var(--text-primary);
            line-height: 1.7;
            padding: 2rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        /* Header */
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border);
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 400;
        }}

        .date {{
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}

        /* Print Button */
        .print-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-md);
            margin-top: 1.5rem;
        }}

        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}

        .print-btn:active {{
            transform: translateY(0);
        }}

        .print-btn svg {{
            width: 18px;
            height: 18px;
        }}

        /* Section Styles */
        section {{
            background: var(--surface);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}

        .section-icon {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}

        h2 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        /* Table of Contents */
        .toc-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 0.75rem;
        }}

        .toc-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            background: var(--background);
            border-radius: 10px;
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}

        .toc-item:hover {{
            background: var(--primary);
            color: white;
            transform: translateX(4px);
        }}

        .toc-number {{
            width: 24px;
            height: 24px;
            background: var(--primary);
            color: white;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .toc-item:hover .toc-number {{
            background: white;
            color: var(--primary);
        }}

        /* Summary Section */
        .summary-content {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #bae6fd;
        }}

        .summary-item {{
            padding: 0.75rem 0;
            border-bottom: 1px dashed #bae6fd;
        }}

        .summary-item:last-child {{
            border-bottom: none;
        }}

        .summary-item strong {{
            color: var(--primary-dark);
        }}

        /* Slide Cards */
        .slides-grid {{
            display: grid;
            gap: 1.5rem;
        }}

        .slide-card {{
            background: var(--surface);
            border-radius: 16px;
            padding: 1.75rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            page-break-inside: avoid;
        }}

        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            border-color: var(--accent);
        }}

        .slide-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .slide-badge {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 1rem;
        }}

        .slide-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .slide-filename {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}

        .slide-content {{
            color: var(--text-secondary);
            white-space: pre-wrap;
            line-height: 1.8;
            padding-left: 3.25rem;
        }}

        .slide-content p {{
            margin-bottom: 0.5rem;
        }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }}

        .empty-state svg {{
            width: 64px;
            height: 64px;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* Print Styles */
        @media print {{
            body {{
                padding: 0;
                background: white;
            }}

            .container {{
                max-width: 100%;
            }}

            .print-btn {{
                display: none;
            }}

            section {{
                box-shadow: none;
                border: 1px solid #ccc;
                page-break-inside: avoid;
            }}

            .slide-card {{
                box-shadow: none;
                border: 1px solid #ddd;
                page-break-inside: avoid;
            }}

            .slide-card:hover {{
                box-shadow: none;
            }}

            h1 {{
                -webkit-text-fill-color: var(--primary);
                background: none;
                color: var(--primary);
            }}

            .summary-content {{
                background: #f5f5f5;
                border-color: #ddd;
            }}
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            body {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 1.75rem;
            }}

            section {{
                padding: 1.5rem;
            }}

            .toc-list {{
                grid-template-columns: 1fr;
            }}

            .slide-content {{
                padding-left: 0;
                margin-top: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Generated from {len(slides)} slide files</p>
            <p class="date">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <button class="print-btn" onclick="window.print()">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Print to PDF
            </button>
        </header>

        {f'''
        <section id="summary">
            <div class="section-header">
                <div class="section-icon">📋</div>
                <h2>Executive Summary</h2>
            </div>
            <div class="summary-content">
                {''.join(f'<div class="summary-item">{escape_html(item)}</div>' for item in summary_items)}
            </div>
        </section>
        ''' if summary_items else ''}

        {f'''
        <section id="toc">
            <div class="section-header">
                <div class="section-icon">📑</div>
                <h2>Table of Contents</h2>
            </div>
            <div class="toc-list">
                {''.join(f'''
                <a href="#slide-{i+1}" class="toc-item">
                    <span class="toc-number">{i+1}</span>
                    <span>{escape_html(slide["title"])}</span>
                </a>
                ''' for i, slide in enumerate(slides))}
            </div>
        </section>
        ''' if slides else ''}

        <section id="slides">
            <div class="section-header">
                <div class="section-icon">📄</div>
                <h2>Slide Details</h2>
            </div>
            <div class="slides-grid">
                {''.join(f'''
                <div class="slide-card" id="slide-{i+1}">
                    <div class="slide-header">
                        <div class="slide-badge">{i+1}</div>
                        <div>
                            <div class="slide-title">{escape_html(slide["title"])}</div>
                            <div class="slide-filename">{escape_html(slide["filename"])}</div>
                        </div>
                    </div>
                    <div class="slide-content">{escape_html(slide["content"])}</div>
                </div>
                ''' for i, slide in enumerate(slides))}
            </div>
            {'''
            <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No slide files found in the directory.</p>
            </div>
            ''' if not slides else ''}
        </section>

        <footer>
            <p>Slide Summary Report • Generated {datetime.now().strftime('%B %d, %Y')}</p>
        </footer>
    </div>

    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return output_path


def main():
    """Main entry point for the slide reporter."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate a beautiful HTML report from slide text files.'
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
        help='Output HTML file path (default: report.html)'
    )
    
    args = parser.parse_args()
    
    try:
        print(f"📂 Reading slide files from: {args.directory}")
        slides = read_slide_files(args.directory)
        print(f"📄 Found {len(slides)} slide file(s)")
        
        output_path = generate_html_report(slides, args.output)
        print(f"✅ Report generated: {output_path}")
        print(f"🌐 Open the file in your browser to view the report")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())