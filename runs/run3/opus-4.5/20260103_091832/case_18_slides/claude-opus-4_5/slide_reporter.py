#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files representing slides and generates a beautiful HTML report.
"""

import os
import sys
import re
from html import escape
from datetime import datetime


def get_slide_number(filename):
    """Extract slide number from filename for sorting."""
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else 0


def read_slides(directory):
    """Read all .txt files from the directory and return sorted slide content."""
    slides = []
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        sys.exit(1)
    
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"No .txt files found in '{directory}'")
        sys.exit(1)
    
    # Sort by slide number
    txt_files.sort(key=get_slide_number)
    
    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Extract title (first non-empty line)
        lines = content.split('\n')
        title = filename.replace('.txt', '').replace('_', ' ').replace('-', ' ').title()
        for line in lines:
            if line.strip():
                title = line.strip()
                break
        
        slides.append({
            'filename': filename,
            'title': title,
            'content': content,
            'lines': lines
        })
    
    return slides


def generate_summary(slides, max_lines=3):
    """Generate a summary from the first few lines of each slide."""
    summary_items = []
    
    for slide in slides:
        # Get first few non-empty lines (excluding title)
        non_empty_lines = [l.strip() for l in slide['lines'] if l.strip()]
        preview_lines = non_empty_lines[1:max_lines+1] if len(non_empty_lines) > 1 else non_empty_lines[:max_lines]
        preview = ' '.join(preview_lines)[:200]
        if len(' '.join(preview_lines)) > 200:
            preview += '...'
        
        summary_items.append({
            'title': slide['title'],
            'preview': preview
        })
    
    return summary_items


def generate_html(slides, summary):
    """Generate the complete HTML report."""
    
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    # Build Table of Contents
    toc_items = ''
    for i, slide in enumerate(slides, 1):
        toc_items += f'''
            <li>
                <a href="#slide-{i}">
                    <span class="toc-number">{i:02d}</span>
                    <span class="toc-title">{escape(slide['title'])}</span>
                </a>
            </li>'''
    
    # Build Summary Section
    summary_items = ''
    for i, item in enumerate(summary, 1):
        summary_items += f'''
            <div class="summary-item">
                <div class="summary-number">{i}</div>
                <div class="summary-content">
                    <h4>{escape(item['title'])}</h4>
                    <p>{escape(item['preview']) if item['preview'] else '<em>No content preview available</em>'}</p>
                </div>
            </div>'''
    
    # Build Slide Cards
    slide_cards = ''
    for i, slide in enumerate(slides, 1):
        # Format content with proper paragraph handling
        content_html = ''
        paragraphs = slide['content'].split('\n\n')
        for para in paragraphs:
            lines = para.strip().split('\n')
            formatted_lines = '<br>'.join(escape(line) for line in lines if line.strip())
            if formatted_lines:
                content_html += f'<p>{formatted_lines}</p>'
        
        slide_cards += f'''
            <article class="slide-card" id="slide-{i}">
                <div class="slide-header">
                    <span class="slide-badge">Slide {i}</span>
                    <span class="slide-filename">{escape(slide['filename'])}</span>
                </div>
                <h2 class="slide-title">{escape(slide['title'])}</h2>
                <div class="slide-content">
                    {content_html}
                </div>
            </article>'''
    
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
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #a5b4fc;
            --secondary: #0ea5e9;
            --accent: #f59e0b;
            --success: #10b981;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-light: #f8fafc;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-dark: #1e293b;
            --border: #334155;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            --shadow-glow: 0 0 40px rgba(99, 102, 241, 0.15);
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 100%);
            color: var(--text-primary);
            line-height: 1.7;
            min-height: 100vh;
        }}
        
        /* Typography */
        h1, h2, h3, h4 {{
            font-weight: 700;
            letter-spacing: -0.025em;
            line-height: 1.3;
        }}
        
        h1 {{
            font-size: 2.75rem;
            background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        h2 {{
            font-size: 1.75rem;
            color: var(--text-primary);
        }}
        
        h3 {{
            font-size: 1.25rem;
            color: var(--primary-light);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 600;
        }}
        
        h4 {{
            font-size: 1.1rem;
            color: var(--text-primary);
        }}
        
        p {{
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }}
        
        /* Layout */
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}
        
        /* Header */
        header {{
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(180deg, rgba(99, 102, 241, 0.1) 0%, transparent 100%);
            border-bottom: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }}
        
        header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        
        .subtitle {{
            font-size: 1.125rem;
            color: var(--text-secondary);
            margin-top: 0.75rem;
        }}
        
        .meta {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        .meta-icon {{
            width: 18px;
            height: 18px;
            opacity: 0.7;
        }}
        
        /* Print Button */
        .print-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 2rem;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-lg), 0 0 20px rgba(99, 102, 241, 0.3);
        }}
        
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl), 0 0 30px rgba(99, 102, 241, 0.4);
        }}
        
        .print-btn:active {{
            transform: translateY(0);
        }}
        
        /* Sections */
        section {{
            margin-bottom: 4rem;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .section-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }}
        
        /* Table of Contents */
        .toc {{
            background: var(--bg-card);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: var(--shadow-xl), var(--shadow-glow);
            border: 1px solid var(--border);
        }}
        
        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 0.75rem;
        }}
        
        .toc-list li a {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 1.25rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            text-decoration: none;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }}
        
        .toc-list li a:hover {{
            background: rgba(99, 102, 241, 0.1);
            border-color: var(--primary);
            transform: translateX(4px);
        }}
        
        .toc-number {{
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--primary);
            background: rgba(99, 102, 241, 0.15);
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            font-family: 'SF Mono', 'Consolas', monospace;
        }}
        
        .toc-title {{
            color: var(--text-primary);
            font-weight: 500;
            font-size: 0.95rem;
        }}
        
        /* Summary Section */
        .summary-grid {{
            display: grid;
            gap: 1rem;
        }}
        
        .summary-item {{
            display: flex;
            gap: 1.25rem;
            padding: 1.5rem;
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }}
        
        .summary-item:hover {{
            border-color: var(--primary);
            box-shadow: var(--shadow-lg);
        }}
        
        .summary-number {{
            flex-shrink: 0;
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
        }}
        
        .summary-content h4 {{
            margin-bottom: 0.5rem;
        }}
        
        .summary-content p {{
            font-size: 0.9rem;
            margin-bottom: 0;
            line-height: 1.6;
        }}
        
        /* Slide Cards */
        .slides-grid {{
            display: grid;
            gap: 2rem;
        }}
        
        .slide-card {{
            background: var(--bg-card);
            border-radius: 24px;
            padding: 2.5rem;
            box-shadow: var(--shadow-xl);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .slide-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 50%, var(--accent) 100%);
        }}
        
        .slide-card:hover {{
            border-color: var(--primary);
            box-shadow: var(--shadow-xl), var(--shadow-glow);
            transform: translateY(-4px);
        }}
        
        .slide-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }}
        
        .slide-badge {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .slide-filename {{
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            background: rgba(255, 255, 255, 0.05);
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
        }}
        
        .slide-title {{
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}
        
        .slide-content {{
            font-size: 1rem;
        }}
        
        .slide-content p {{
            margin-bottom: 1.25rem;
            line-height: 1.8;
        }}
        
        .slide-content p:last-child {{
            margin-bottom: 0;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            padding: 3rem 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        footer a {{
            color: var(--primary-light);
            text-decoration: none;
        }}
        
        /* Back to Top */
        .back-to-top {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-lg);
            z-index: 100;
        }}
        
        .back-to-top.visible {{
            opacity: 1;
            visibility: visible;
        }}
        
        .back-to-top:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl), 0 0 20px rgba(99, 102, 241, 0.4);
        }}
        
        /* Print Styles */
        @media print {{
            body {{
                background: white;
                color: var(--text-dark);
            }}
            
            .container {{
                max-width: 100%;
                padding: 0;
            }}
            
            header {{
                background: none;
                border-bottom: 2px solid #e5e7eb;
                padding: 2rem 0;
            }}
            
            header::before {{
                display: none;
            }}
            
            h1 {{
                background: none;
                -webkit-text-fill-color: var(--primary-dark);
                color: var(--primary-dark);
            }}
            
            .print-btn, .back-to-top {{
                display: none !important;
            }}
            
            .toc, .summary-item, .slide-card {{
                background: white;
                box-shadow: none;
                border: 1px solid #e5e7eb;
            }}
            
            .toc-list li a {{
                background: none;
            }}
            
            .slide-card {{
                page-break-inside: avoid;
                break-inside: avoid;
                margin-bottom: 2rem;
            }}
            
            .slide-card::before {{
                background: var(--primary);
            }}
            
            h2, h3, h4 {{
                color: var(--text-dark);
            }}
            
            p, .toc-title, .slide-filename {{
                color: #4b5563;
            }}
            
            section {{
                page-break-before: auto;
            }}
            
            .slides-section {{
                page-break-before: always;
            }}
            
            @page {{
                margin: 1.5cm;
            }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            
            .container {{
                padding: 2rem 1rem;
            }}
            
            .toc, .slide-card {{
                padding: 1.5rem;
            }}
            
            .toc-list {{
                grid-template-columns: 1fr;
            }}
            
            .meta {{
                flex-direction: column;
                gap: 0.75rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">A comprehensive overview of your presentation slides</p>
            <div class="meta">
                <span class="meta-item">
                    <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    {len(slides)} Slides
                </span>
                <span class="meta-item">
                    <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Generated: {timestamp}
                </span>
            </div>
            <button class="print-btn" onclick="window.print()">
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
                </svg>
                Print to PDF
            </button>
        </div>
    </header>
    
    <main class="container">
        <!-- Table of Contents -->
        <section>
            <div class="section-header">
                <div class="section-icon">📑</div>
                <h3>Table of Contents</h3>
            </div>
            <nav class="toc">
                <ol class="toc-list">{toc_items}
                </ol>
            </nav>
        </section>
        
        <!-- Summary Section -->
        <section>
            <div class="section-header">
                <div class="section-icon">📝</div>
                <h3>Executive Summary</h3>
            </div>
            <div class="summary-grid">{summary_items}
            </div>
        </section>
        
        <!-- Slide Cards -->
        <section class="slides-section">
            <div class="section-header">
                <div class="section-icon">🎯</div>
                <h3>Full Slide Content</h3>
            </div>
            <div class="slides-grid">{slide_cards}
            </div>
        </section>
    </main>
    
    <footer>
        <p>Generated by <strong>Slide Summary Reporter</strong> • Built with Python</p>
    </footer>
    
    <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})" title="Back to top">↑</button>
    
    <script>
        // Back to top button visibility
        const backToTop = document.querySelector('.back-to-top');
        window.addEventListener('scroll', () => {{
            if (window.scrollY > 500) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        
        // Smooth scroll for TOC links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    return html


def main():
    # Default to current directory if no argument provided
    if len(sys.argv) < 2:
        directory = '.'
    else:
        directory = sys.argv[1]
    
    print(f"📂 Reading slides from: {os.path.abspath(directory)}")
    
    # Read all slides
    slides = read_slides(directory)
    print(f"📄 Found {len(slides)} slide(s)")
    
    # Generate summary
    summary = generate_summary(slides)
    
    # Generate HTML
    html = generate_html(slides, summary)
    
    # Write output
    output_path = 'report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report generated: {os.path.abspath(output_path)}")
    print("🖨️  Open the report in a browser and click 'Print to PDF' to save as PDF")


if __name__ == '__main__':
    main()