#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files representing slides and generates a beautiful HTML report.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime


def natural_sort_key(filename):
    """Sort filenames naturally (slide1, slide2, slide10 instead of slide1, slide10, slide2)"""
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', filename)]


def read_slide_files(directory):
    """Read all .txt files from the directory and return sorted list of (filename, content) tuples"""
    slides = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    txt_files = sorted(dir_path.glob("*.txt"), key=lambda x: natural_sort_key(x.name))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            slides.append((txt_file.stem, content))
        except Exception as e:
            print(f"Warning: Could not read {txt_file}: {e}")
    
    return slides


def extract_summary_lines(content, max_lines=3):
    """Extract first few non-empty lines from content"""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    return lines[:max_lines]


def escape_html(text):
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def generate_html_report(slides, output_path):
    """Generate a beautiful HTML report from slides"""
    
    # Build Table of Contents and Summary
    toc_items = []
    summary_items = []
    slide_cards = []
    
    for idx, (name, content) in enumerate(slides, 1):
        slide_id = f"slide-{idx}"
        display_name = name.replace('_', ' ').replace('-', ' ').title()
        
        # TOC item
        toc_items.append(f'''
            <a href="#{slide_id}" class="toc-item">
                <span class="toc-number">{idx:02d}</span>
                <span class="toc-title">{escape_html(display_name)}</span>
            </a>
        ''')
        
        # Summary item
        summary_lines = extract_summary_lines(content, 2)
        summary_text = ' '.join(summary_lines)[:150]
        if len(' '.join(summary_lines)) > 150:
            summary_text += '...'
        summary_items.append(f'''
            <div class="summary-item">
                <span class="summary-number">{idx}</span>
                <div class="summary-content">
                    <strong>{escape_html(display_name)}</strong>
                    <p>{escape_html(summary_text)}</p>
                </div>
            </div>
        ''')
        
        # Slide card
        formatted_content = escape_html(content)
        # Convert lines starting with # to headers
        lines = formatted_content.split('\n')
        formatted_lines = []
        for line in lines:
            if line.startswith('# '):
                formatted_lines.append(f'<h3 class="slide-heading">{line[2:]}</h3>')
            elif line.startswith('## '):
                formatted_lines.append(f'<h4 class="slide-subheading">{line[3:]}</h4>')
            elif line.startswith('- ') or line.startswith('* '):
                formatted_lines.append(f'<li class="slide-bullet">{line[2:]}</li>')
            elif line.strip():
                formatted_lines.append(f'<p class="slide-paragraph">{line}</p>')
        
        formatted_content = '\n'.join(formatted_lines)
        
        slide_cards.append(f'''
            <article class="slide-card" id="{slide_id}">
                <header class="slide-header">
                    <span class="slide-number">Slide {idx}</span>
                    <h2 class="slide-title">{escape_html(display_name)}</h2>
                </header>
                <div class="slide-content">
                    {formatted_content}
                </div>
            </article>
        ''')
    
    # Generate full HTML
    html = f'''<!DOCTYPE html>
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
            --color-primary: #2563eb;
            --color-primary-dark: #1d4ed8;
            --color-secondary: #7c3aed;
            --color-text: #1e293b;
            --color-text-light: #64748b;
            --color-bg: #f8fafc;
            --color-white: #ffffff;
            --color-border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 1rem;
            --radius-xl: 1.5rem;
        }}
        
        html {{
            font-size: 16px;
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--color-text);
            line-height: 1.7;
        }}
        
        /* Container */
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Header */
        .report-header {{
            background: var(--color-white);
            border-radius: var(--radius-xl);
            padding: 3rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-xl);
            text-align: center;
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
            background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
        }}
        
        .report-title {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}
        
        .report-subtitle {{
            color: var(--color-text-light);
            font-size: 1.1rem;
            font-weight: 400;
        }}
        
        .report-meta {{
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--color-border);
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--color-text-light);
            font-size: 0.9rem;
        }}
        
        .meta-icon {{
            width: 18px;
            height: 18px;
            opacity: 0.7;
        }}
        
        /* Print Button */
        .print-btn {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            color: white;
            border: none;
            padding: 1rem 1.5rem;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 1000;
        }}
        
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}
        
        .print-btn:active {{
            transform: translateY(0);
        }}
        
        /* Section Cards */
        .section-card {{
            background: var(--color-white);
            border-radius: var(--radius-xl);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--color-text);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .section-icon {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1rem;
        }}
        
        /* Table of Contents */
        .toc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 0.75rem;
        }}
        
        .toc-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.875rem 1rem;
            background: var(--color-bg);
            border-radius: var(--radius-md);
            text-decoration: none;
            color: var(--color-text);
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}
        
        .toc-item:hover {{
            background: white;
            border-color: var(--color-primary);
            box-shadow: var(--shadow-md);
            transform: translateX(4px);
        }}
        
        .toc-number {{
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }}
        
        .toc-title {{
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        /* Summary Section */
        .summary-grid {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .summary-item {{
            display: flex;
            gap: 1rem;
            padding: 1rem;
            background: var(--color-bg);
            border-radius: var(--radius-md);
            border-left: 4px solid var(--color-primary);
        }}
        
        .summary-number {{
            background: var(--color-primary);
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }}
        
        .summary-content strong {{
            color: var(--color-text);
            font-size: 0.95rem;
        }}
        
        .summary-content p {{
            color: var(--color-text-light);
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        
        /* Slide Cards */
        .slides-section {{
            margin-top: 1rem;
        }}
        
        .slide-card {{
            background: var(--color-white);
            border-radius: var(--radius-xl);
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-2px);
        }}
        
        .slide-header {{
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            padding: 1.5rem 2rem;
            color: white;
        }}
        
        .slide-number {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            opacity: 0.9;
        }}
        
        .slide-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }}
        
        .slide-content {{
            padding: 2rem;
        }}
        
        .slide-heading {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--color-text);
            margin-bottom: 1rem;
            margin-top: 1.5rem;
        }}
        
        .slide-heading:first-child {{
            margin-top: 0;
        }}
        
        .slide-subheading {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--color-text);
            margin-bottom: 0.75rem;
            margin-top: 1.25rem;
        }}
        
        .slide-paragraph {{
            color: var(--color-text);
            margin-bottom: 0.75rem;
            font-size: 1rem;
        }}
        
        .slide-bullet {{
            color: var(--color-text);
            margin-left: 1.5rem;
            margin-bottom: 0.5rem;
            position: relative;
        }}
        
        .slide-bullet::marker {{
            color: var(--color-primary);
        }}
        
        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 2rem;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
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
            
            .report-header,
            .section-card {{
                box-shadow: none;
                border: 1px solid var(--color-border);
            }}
            
            .slide-card {{
                box-shadow: none;
                border: 1px solid var(--color-border);
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            
            .slide-header {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .section-card {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            
            .slides-section .slide-card {{
                page-break-before: auto;
            }}
            
            .slides-section .slide-card:first-child {{
                page-break-before: avoid;
            }}
        }}
        
        @page {{
            margin: 1.5cm;
            size: A4;
        }}
        
        /* Responsive */
        @media (max-width: 640px) {{
            .container {{
                padding: 1rem;
            }}
            
            .report-header {{
                padding: 2rem 1.5rem;
            }}
            
            .report-title {{
                font-size: 1.75rem;
            }}
            
            .section-card {{
                padding: 1.5rem;
            }}
            
            .toc-grid {{
                grid-template-columns: 1fr;
            }}
            
            .slide-content {{
                padding: 1.5rem;
            }}
            
            .print-btn {{
                bottom: 1rem;
                right: 1rem;
                padding: 0.875rem 1.25rem;
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="report-header">
            <h1 class="report-title">Slide Summary Report</h1>
            <p class="report-subtitle">Comprehensive overview of presentation content</p>
            <div class="report-meta">
                <div class="meta-item">
                    <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <span>{len(slides)} Slides</span>
                </div>
                <div class="meta-item">
                    <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <span>{datetime.now().strftime('%B %d, %Y')}</span>
                </div>
            </div>
        </header>
        
        <!-- Table of Contents -->
        <section class="section-card">
            <h2 class="section-title">
                <span class="section-icon">📑</span>
                Table of Contents
            </h2>
            <nav class="toc-grid">
                {''.join(toc_items)}
            </nav>
        </section>
        
        <!-- Summary -->
        <section class="section-card">
            <h2 class="section-title">
                <span class="section-icon">📋</span>
                Executive Summary
            </h2>
            <div class="summary-grid">
                {''.join(summary_items)}
            </div>
        </section>
        
        <!-- Slides -->
        <section class="slides-section">
            {''.join(slide_cards)}
        </section>
        
        <!-- Footer -->
        <footer class="report-footer">
            <p>Generated with Slide Summary Reporter • {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </footer>
    </div>
    
    <!-- Print Button -->
    <button class="print-btn" onclick="window.print()">
        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
        </svg>
        Print to PDF
    </button>
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path


def main():
    # Default to current directory, or use command line argument
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    # Optional output path
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = 'report.html'
    
    print(f"📂 Scanning directory: {directory}")
    slides = read_slide_files(directory)
    
    if not slides:
        print("❌ No .txt files found in the directory.")
        sys.exit(1)
    
    print(f"📝 Found {len(slides)} slide(s):")
    for name, _ in slides:
        print(f"   • {name}")
    
    output = generate_html_report(slides, output_path)
    print(f"\n✅ Report generated: {output}")
    print("🖨️  Open the file and click 'Print to PDF' to export as PDF")


if __name__ == '__main__':
    main()