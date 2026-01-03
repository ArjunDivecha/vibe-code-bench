#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files representing slides and generates a beautiful HTML report.
"""

import os
import re
import html
import sys
from pathlib import Path


def extract_slide_number(filename):
    """Extract numeric portion from filename for sorting."""
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else 0


def get_first_lines(content, num_lines=3):
    """Get the first few non-empty lines of content."""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    return lines[:num_lines]


def read_slides(directory):
    """Read all .txt files in the directory and return sorted slide data."""
    slides = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    txt_files = list(dir_path.glob('*.txt'))
    
    if not txt_files:
        print(f"Error: No .txt files found in '{directory}'.")
        sys.exit(1)
    
    for filepath in txt_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filename = filepath.name
        title = filepath.stem.replace('_', ' ').replace('-', ' ').title()
        
        slides.append({
            'filename': filename,
            'title': title,
            'content': content,
            'first_lines': get_first_lines(content),
            'sort_key': extract_slide_number(filename)
        })
    
    # Sort by extracted number
    slides.sort(key=lambda x: x['sort_key'])
    return slides


def generate_html(slides, output_path):
    """Generate the HTML report."""
    
    # Build Table of Contents
    toc_items = []
    for i, slide in enumerate(slides, 1):
        slide_id = f"slide-{i}"
        toc_items.append(f'<li><a href="#{slide_id}">{html.escape(slide["title"])}</a></li>')
    
    toc_html = '\n                        '.join(toc_items)
    
    # Build Summary
    summary_items = []
    for slide in slides:
        summary_text = ' '.join(slide['first_lines'])[:150]
        if len(' '.join(slide['first_lines'])) > 150:
            summary_text += '...'
        summary_items.append(f'''
                        <div class="summary-item">
                            <span class="summary-title">{html.escape(slide["title"])}:</span>
                            <span class="summary-text">{html.escape(summary_text)}</span>
                        </div>''')
    
    summary_html = '\n'.join(summary_items)
    
    # Build Slide Cards
    slide_cards = []
    for i, slide in enumerate(slides, 1):
        slide_id = f"slide-{i}"
        content_paragraphs = []
        for para in slide['content'].split('\n\n'):
            if para.strip():
                lines = para.strip().split('\n')
                formatted_lines = '<br>'.join(html.escape(line) for line in lines)
                content_paragraphs.append(f'<p>{formatted_lines}</p>')
        
        content_html = '\n                            '.join(content_paragraphs)
        
        slide_cards.append(f'''
                    <article class="slide-card" id="{slide_id}">
                        <div class="slide-header">
                            <span class="slide-number">{i:02d}</span>
                            <h2 class="slide-title">{html.escape(slide["title"])}</h2>
                        </div>
                        <div class="slide-content">
                            {content_html}
                        </div>
                        <div class="slide-footer">
                            <span class="slide-source">Source: {html.escape(slide["filename"])}</span>
                        </div>
                    </article>''')
    
    slides_html = '\n'.join(slide_cards)
    
    # Complete HTML template
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* CSS Reset & Base */
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        :root {{
            --color-primary: #1a1a2e;
            --color-secondary: #16213e;
            --color-accent: #0f3460;
            --color-highlight: #e94560;
            --color-text: #2d3436;
            --color-text-light: #636e72;
            --color-bg: #f8f9fa;
            --color-white: #ffffff;
            --color-border: #e1e4e8;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.1), 0 6px 12px rgba(0,0,0,0.08);
            --shadow-xl: 0 20px 40px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.08);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --font-sans: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
            --font-serif: 'Georgia', 'Times New Roman', serif;
            --font-mono: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        }}

        html {{
            font-size: 16px;
            scroll-behavior: smooth;
        }}

        body {{
            font-family: var(--font-sans);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--color-text);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* Main Container */
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        /* Header */
        .report-header {{
            text-align: center;
            margin-bottom: 48px;
            padding: 60px 40px;
            background: var(--color-white);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(90deg, var(--color-highlight), #ff6b6b, #feca57, #48dbfb, var(--color-highlight));
            background-size: 200% 100%;
            animation: gradient-shift 3s ease infinite;
        }}

        @keyframes gradient-shift {{
            0%, 100% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
        }}

        .report-header h1 {{
            font-size: 2.75rem;
            font-weight: 800;
            color: var(--color-primary);
            margin-bottom: 12px;
            letter-spacing: -0.03em;
        }}

        .report-header .subtitle {{
            font-size: 1.125rem;
            color: var(--color-text-light);
            font-weight: 400;
        }}

        .report-meta {{
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid var(--color-border);
            display: flex;
            justify-content: center;
            gap: 32px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: var(--color-text-light);
        }}

        .meta-icon {{
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--color-bg);
            border-radius: 50%;
            font-size: 0.75rem;
        }}

        /* Print Button */
        .print-btn {{
            position: fixed;
            bottom: 32px;
            right: 32px;
            padding: 16px 28px;
            background: linear-gradient(135deg, var(--color-highlight), #ff6b6b);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg), 0 4px 20px rgba(233, 69, 96, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .print-btn:hover {{
            transform: translateY(-3px) scale(1.02);
            box-shadow: var(--shadow-xl), 0 8px 30px rgba(233, 69, 96, 0.5);
        }}

        .print-btn:active {{
            transform: translateY(-1px);
        }}

        .print-btn svg {{
            width: 20px;
            height: 20px;
        }}

        /* Section Styles */
        .section {{
            background: var(--color-white);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            margin-bottom: 32px;
            overflow: hidden;
        }}

        .section-header {{
            padding: 24px 32px;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            color: white;
        }}

        .section-header h2 {{
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .section-header .icon {{
            width: 32px;
            height: 32px;
            background: rgba(255,255,255,0.2);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .section-body {{
            padding: 32px;
        }}

        /* Table of Contents */
        .toc-list {{
            list-style: none;
            display: grid;
            gap: 8px;
        }}

        .toc-list li {{
            position: relative;
        }}

        .toc-list a {{
            display: flex;
            align-items: center;
            padding: 14px 20px;
            background: var(--color-bg);
            border-radius: var(--radius-sm);
            text-decoration: none;
            color: var(--color-text);
            font-weight: 500;
            transition: all 0.2s ease;
            border-left: 4px solid transparent;
        }}

        .toc-list a:hover {{
            background: linear-gradient(135deg, #667eea20, #764ba220);
            border-left-color: var(--color-highlight);
            transform: translateX(4px);
        }}

        .toc-list a::before {{
            content: '→';
            margin-right: 12px;
            color: var(--color-highlight);
            font-weight: 700;
        }}

        /* Summary Section */
        .summary-item {{
            padding: 16px 0;
            border-bottom: 1px solid var(--color-border);
        }}

        .summary-item:last-child {{
            border-bottom: none;
        }}

        .summary-title {{
            font-weight: 700;
            color: var(--color-primary);
            display: block;
            margin-bottom: 6px;
            font-size: 0.95rem;
        }}

        .summary-text {{
            color: var(--color-text-light);
            font-size: 0.9rem;
            line-height: 1.6;
        }}

        /* Slide Cards */
        .slides-section {{
            margin-top: 48px;
        }}

        .slides-section > h2 {{
            font-size: 1.75rem;
            color: white;
            margin-bottom: 24px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        .slide-card {{
            background: var(--color-white);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            margin-bottom: 28px;
            overflow: hidden;
            transition: all 0.3s ease;
            page-break-inside: avoid;
        }}

        .slide-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
        }}

        .slide-header {{
            padding: 28px 32px;
            background: linear-gradient(135deg, var(--color-accent), var(--color-secondary));
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .slide-number {{
            width: 48px;
            height: 48px;
            background: rgba(255,255,255,0.15);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 800;
            color: white;
            font-family: var(--font-mono);
            backdrop-filter: blur(10px);
        }}

        .slide-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: white;
            flex: 1;
        }}

        .slide-content {{
            padding: 32px;
            font-size: 1.05rem;
        }}

        .slide-content p {{
            margin-bottom: 18px;
            color: var(--color-text);
        }}

        .slide-content p:last-child {{
            margin-bottom: 0;
        }}

        .slide-footer {{
            padding: 16px 32px;
            background: var(--color-bg);
            border-top: 1px solid var(--color-border);
        }}

        .slide-source {{
            font-size: 0.8rem;
            color: var(--color-text-light);
            font-family: var(--font-mono);
        }}

        /* Back to Top */
        .back-to-top {{
            display: block;
            text-align: center;
            padding: 20px;
            color: white;
            text-decoration: none;
            font-weight: 600;
            opacity: 0.8;
            transition: opacity 0.2s;
        }}

        .back-to-top:hover {{
            opacity: 1;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .container {{
                max-width: 100%;
                padding: 0;
            }}

            .print-btn {{
                display: none !important;
            }}

            .report-header {{
                box-shadow: none;
                border: 2px solid var(--color-border);
                page-break-after: avoid;
            }}

            .section {{
                box-shadow: none;
                border: 1px solid var(--color-border);
            }}

            .slide-card {{
                box-shadow: none;
                border: 1px solid var(--color-border);
                page-break-inside: avoid;
                break-inside: avoid;
            }}

            .slides-section > h2 {{
                color: var(--color-primary);
                text-shadow: none;
            }}

            .back-to-top {{
                display: none;
            }}

            .toc-list a {{
                color: var(--color-primary);
            }}

            @page {{
                margin: 1in;
                size: letter;
            }}
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 20px 16px;
            }}

            .report-header {{
                padding: 40px 24px;
            }}

            .report-header h1 {{
                font-size: 2rem;
            }}

            .section-body {{
                padding: 24px;
            }}

            .slide-header {{
                padding: 20px 24px;
            }}

            .slide-content {{
                padding: 24px;
            }}

            .print-btn {{
                bottom: 20px;
                right: 20px;
                padding: 14px 20px;
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
        <!-- Header -->
        <header class="report-header">
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of presentation slides</p>
            <div class="report-meta">
                <div class="meta-item">
                    <span class="meta-icon">📄</span>
                    <span>{len(slides)} Slides</span>
                </div>
                <div class="meta-item">
                    <span class="meta-icon">📅</span>
                    <span>Generated Today</span>
                </div>
            </div>
        </header>

        <!-- Table of Contents -->
        <section class="section">
            <div class="section-header">
                <h2>
                    <span class="icon">📑</span>
                    Table of Contents
                </h2>
            </div>
            <div class="section-body">
                <ol class="toc-list">
                    {toc_html}
                </ol>
            </div>
        </section>

        <!-- Summary -->
        <section class="section">
            <div class="section-header">
                <h2>
                    <span class="icon">✨</span>
                    Executive Summary
                </h2>
            </div>
            <div class="section-body">
                {summary_html}
            </div>
        </section>

        <!-- Slides -->
        <section class="slides-section">
            <h2>📌 Slide Details</h2>
            {slides_html}
        </section>

        <a href="#" class="back-to-top">↑ Back to Top</a>
    </div>

    <!-- Print Button -->
    <button class="print-btn" onclick="window.print()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
        </svg>
        Print to PDF
    </button>

    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function(e) {{
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
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ Report generated: {output_path}")
    print(f"   📄 {len(slides)} slides processed")


def main():
    # Default to current directory or accept command line argument
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = 'report.html'
    
    print(f"🔍 Scanning directory: {directory}")
    slides = read_slides(directory)
    print(f"📝 Found {len(slides)} slide(s)")
    
    generate_html(slides, output_path)


if __name__ == '__main__':
    main()