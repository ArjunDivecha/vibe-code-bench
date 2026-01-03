#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report.
"""

import os
import sys
import re
from pathlib import Path
from html import escape
from datetime import datetime


def natural_sort_key(s):
    """Sort strings containing numbers naturally (slide1, slide2, slide10)."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]


def read_slides(directory):
    """Read all .txt files from the directory and return sorted slide data."""
    slides = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    txt_files = sorted(dir_path.glob("*.txt"), key=natural_sort_key)
    
    if not txt_files:
        print(f"Error: No .txt files found in '{directory}'.")
        sys.exit(1)
    
    for idx, file_path in enumerate(txt_files, 1):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        lines = content.split('\n')
        title = lines[0] if lines else file_path.stem
        
        slides.append({
            'id': idx,
            'filename': file_path.name,
            'title': title,
            'content': content,
            'lines': lines
        })
    
    return slides


def generate_summary(slides, lines_per_slide=2):
    """Generate a summary combining first few lines of each slide."""
    summary_parts = []
    for slide in slides:
        preview_lines = slide['lines'][:lines_per_slide]
        preview = ' '.join(preview_lines)
        if len(slide['lines']) > lines_per_slide:
            preview += '...'
        summary_parts.append(f"<strong>Slide {slide['id']}:</strong> {escape(preview)}")
    return summary_parts


def generate_html(slides, output_path):
    """Generate the HTML report."""
    
    summary_parts = generate_summary(slides)
    generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Generate Table of Contents HTML
    toc_items = '\n'.join([
        f'<li><a href="#slide-{s["id"]}">{escape(s["title"][:50])}{"..." if len(s["title"]) > 50 else ""}</a></li>'
        for s in slides
    ])
    
    # Generate Summary HTML
    summary_html = '\n'.join([
        f'<p class="summary-item">{part}</p>'
        for part in summary_parts
    ])
    
    # Generate Slide Cards HTML
    cards_html = '\n'.join([
        f'''
        <article class="slide-card" id="slide-{s['id']}">
            <header class="card-header">
                <span class="slide-number">Slide {s['id']}</span>
                <span class="slide-filename">{escape(s['filename'])}</span>
            </header>
            <h2 class="card-title">{escape(s['title'])}</h2>
            <div class="card-content">
                {''.join(f'<p>{escape(line)}</p>' if line.strip() else '<br>' for line in s['lines'][1:])}
            </div>
        </article>
        '''
        for s in slides
    ])
    
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
            --color-primary: #2563eb;
            --color-primary-dark: #1d4ed8;
            --color-secondary: #7c3aed;
            --color-text: #1f2937;
            --color-text-light: #6b7280;
            --color-bg: #f8fafc;
            --color-white: #ffffff;
            --color-border: #e5e7eb;
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
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: var(--color-text);
            line-height: 1.7;
            min-height: 100vh;
        }}
        
        /* Container */
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        
        /* Header */
        .report-header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-xl);
            color: var(--color-white);
            position: relative;
            overflow: hidden;
        }}
        
        .report-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            animation: shimmer 15s infinite linear;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .report-header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
        }}
        
        .report-header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }}
        
        .report-header .meta {{
            margin-top: 1rem;
            font-size: 0.875rem;
            opacity: 0.8;
            position: relative;
            z-index: 1;
        }}
        
        /* Print Button */
        .print-btn {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: var(--color-white);
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
        
        .print-btn svg {{
            width: 20px;
            height: 20px;
        }}
        
        /* Section Styling */
        .section {{
            background: var(--color-white);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            margin-bottom: 2rem;
            overflow: hidden;
            transition: box-shadow 0.3s ease;
        }}
        
        .section:hover {{
            box-shadow: var(--shadow-lg);
        }}
        
        .section-header {{
            background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 100%);
            padding: 1.25rem 1.75rem;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .section-header h2 {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--color-text);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .section-header h2 .icon {{
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--color-primary);
            color: white;
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
        }}
        
        .section-content {{
            padding: 1.75rem;
        }}
        
        /* Table of Contents */
        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 0.75rem;
        }}
        
        .toc-list li {{
            position: relative;
        }}
        
        .toc-list a {{
            display: block;
            padding: 0.75rem 1rem;
            background: #f8fafc;
            border-radius: var(--radius-md);
            color: var(--color-text);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}
        
        .toc-list a:hover {{
            background: var(--color-primary);
            color: var(--color-white);
            transform: translateX(4px);
            border-color: var(--color-primary-dark);
        }}
        
        /* Summary */
        .summary-item {{
            padding: 0.875rem 1rem;
            margin-bottom: 0.75rem;
            background: linear-gradient(90deg, #fafafa 0%, #f5f5f5 100%);
            border-left: 4px solid var(--color-primary);
            border-radius: 0 var(--radius-md) var(--radius-md) 0;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }}
        
        .summary-item:hover {{
            border-left-color: var(--color-secondary);
            background: linear-gradient(90deg, #f0f0ff 0%, #f5f5f5 100%);
        }}
        
        .summary-item:last-child {{
            margin-bottom: 0;
        }}
        
        .summary-item strong {{
            color: var(--color-primary);
        }}
        
        /* Slide Cards */
        .slides-section {{
            margin-top: 3rem;
        }}
        
        .slides-title {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--color-text);
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 3px solid var(--color-primary);
            display: inline-block;
        }}
        
        .slide-card {{
            background: var(--color-white);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            margin-bottom: 2rem;
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid var(--color-border);
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-4px);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: var(--color-white);
        }}
        
        .slide-number {{
            font-weight: 700;
            font-size: 0.9rem;
            background: rgba(255,255,255,0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
        }}
        
        .slide-filename {{
            font-size: 0.8rem;
            opacity: 0.9;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        
        .card-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--color-text);
            padding: 1.5rem 1.5rem 0.75rem;
            border-bottom: 1px solid var(--color-border);
            margin: 0;
        }}
        
        .card-content {{
            padding: 1.5rem;
            color: var(--color-text-light);
            font-size: 1rem;
        }}
        
        .card-content p {{
            margin-bottom: 0.75rem;
        }}
        
        .card-content p:last-child {{
            margin-bottom: 0;
        }}
        
        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 2rem;
            color: var(--color-text-light);
            font-size: 0.875rem;
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
                background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                page-break-after: avoid;
            }}
            
            .section {{
                box-shadow: none;
                border: 1px solid var(--color-border);
                page-break-inside: avoid;
            }}
            
            .slide-card {{
                box-shadow: none;
                border: 1px solid var(--color-border);
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            
            .card-header {{
                background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .slides-section {{
                page-break-before: always;
            }}
            
            .toc-list a:hover {{
                background: #f8fafc;
                color: var(--color-text);
                transform: none;
            }}
        }}
        
        @page {{
            margin: 1.5cm;
            size: A4;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="report-header">
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">{len(slides)} slides compiled into a comprehensive overview</p>
            <p class="meta">Generated on {generated_date}</p>
        </header>
        
        <!-- Table of Contents -->
        <section class="section">
            <div class="section-header">
                <h2><span class="icon">📑</span> Table of Contents</h2>
            </div>
            <div class="section-content">
                <ol class="toc-list">
                    {toc_items}
                </ol>
            </div>
        </section>
        
        <!-- Summary -->
        <section class="section">
            <div class="section-header">
                <h2><span class="icon">✨</span> Executive Summary</h2>
            </div>
            <div class="section-content">
                {summary_html}
            </div>
        </section>
        
        <!-- Slide Cards -->
        <section class="slides-section">
            <h2 class="slides-title">📄 Slide Details</h2>
            {cards_html}
        </section>
        
        <!-- Footer -->
        <footer class="report-footer">
            <p>Generated by Slide Summary Reporter • Python 3</p>
        </footer>
    </div>
    
    <!-- Print Button -->
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print to PDF
    </button>
    
    <script>
        // Smooth scroll for TOC links
        document.querySelectorAll('.toc-list a').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href').slice(1);
                const target = document.getElementById(targetId);
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return output_path


def main():
    """Main entry point."""
    # Default to current directory if no argument provided
    if len(sys.argv) < 2:
        slides_dir = "."
    else:
        slides_dir = sys.argv[1]
    
    # Output path can be specified as second argument
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = "report.html"
    
    print(f"📂 Reading slides from: {slides_dir}")
    slides = read_slides(slides_dir)
    print(f"📄 Found {len(slides)} slides")
    
    print(f"🔨 Generating HTML report...")
    result_path = generate_html(slides, output_path)
    
    print(f"✅ Report generated successfully: {result_path}")
    print(f"   Open in a browser to view, or use the 'Print to PDF' button to save as PDF.")


if __name__ == "__main__":
    main()