#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report.
"""

import os
import re
import sys
from datetime import datetime
from html import escape


def natural_sort_key(s):
    """Sort strings containing numbers in natural order."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def read_slides(directory):
    """Read all .txt files from the directory."""
    slides = []
    
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' not found.")
        sys.exit(1)
    
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    txt_files.sort(key=natural_sort_key)
    
    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first non-empty line) and body
            lines = content.strip().split('\n')
            title = lines[0].strip() if lines else filename
            body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
            
            # Get first few lines for summary (up to 3 lines or 150 chars)
            summary_lines = []
            char_count = 0
            for line in lines[:4]:
                if char_count < 150:
                    summary_lines.append(line.strip())
                    char_count += len(line)
            summary = ' '.join(summary_lines)[:200]
            if len(' '.join(summary_lines)) > 200:
                summary += '...'
            
            slides.append({
                'filename': filename,
                'title': title,
                'body': body,
                'full_content': content,
                'summary': summary,
                'slide_number': len(slides) + 1
            })
        except Exception as e:
            print(f"Warning: Could not read {filename}: {e}")
    
    return slides


def generate_html(slides, output_path):
    """Generate the HTML report."""
    
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
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
            --color-primary: #6366f1;
            --color-primary-dark: #4f46e5;
            --color-secondary: #8b5cf6;
            --color-bg: #f8fafc;
            --color-surface: #ffffff;
            --color-text: #1e293b;
            --color-text-muted: #64748b;
            --color-border: #e2e8f0;
            --color-accent: #f1f5f9;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 1rem;
            --radius-xl: 1.5rem;
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--color-text);
            line-height: 1.7;
            font-size: 16px;
        }}
        
        /* Container */
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 3rem 2rem;
            margin-bottom: 2rem;
            background: var(--color-surface);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
        }}
        
        .header h1 {{
            font-size: 2.75rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }}
        
        .header .subtitle {{
            color: var(--color-text-muted);
            font-size: 1.1rem;
            font-weight: 400;
        }}
        
        .header .meta {{
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--color-border);
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        
        .header .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--color-text-muted);
            font-size: 0.9rem;
        }}
        
        .header .meta-item strong {{
            color: var(--color-text);
        }}
        
        /* Print Button */
        .print-btn {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            color: white;
            border: none;
            padding: 1rem 1.75rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: var(--shadow-lg), 0 0 0 4px rgba(99, 102, 241, 0.2);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 1000;
        }}
        
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl), 0 0 0 6px rgba(99, 102, 241, 0.3);
        }}
        
        .print-btn:active {{
            transform: translateY(0);
        }}
        
        .print-btn svg {{
            width: 20px;
            height: 20px;
        }}
        
        /* Section Card */
        .section {{
            background: var(--color-surface);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
            overflow: hidden;
        }}
        
        .section-header {{
            padding: 1.5rem 2rem;
            background: var(--color-accent);
            border-bottom: 1px solid var(--color-border);
        }}
        
        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--color-text);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .section-title .icon {{
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.875rem;
        }}
        
        .section-body {{
            padding: 2rem;
        }}
        
        /* Table of Contents */
        .toc-list {{
            list-style: none;
            display: grid;
            gap: 0.5rem;
        }}
        
        .toc-item {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .toc-number {{
            width: 32px;
            height: 32px;
            background: var(--color-accent);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--color-primary);
            flex-shrink: 0;
        }}
        
        .toc-link {{
            color: var(--color-text);
            text-decoration: none;
            font-weight: 500;
            padding: 0.75rem 1rem;
            flex: 1;
            border-radius: var(--radius-md);
            transition: all 0.2s ease;
        }}
        
        .toc-link:hover {{
            background: var(--color-accent);
            color: var(--color-primary);
        }}
        
        /* Summary */
        .summary-content {{
            display: grid;
            gap: 1rem;
        }}
        
        .summary-item {{
            padding: 1.25rem;
            background: var(--color-accent);
            border-radius: var(--radius-md);
            border-left: 4px solid var(--color-primary);
        }}
        
        .summary-item-title {{
            font-weight: 600;
            color: var(--color-primary);
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }}
        
        .summary-item-text {{
            color: var(--color-text-muted);
            font-size: 0.95rem;
            line-height: 1.6;
        }}
        
        /* Slide Cards */
        .slide-card {{
            background: var(--color-surface);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
            overflow: hidden;
            transition: all 0.3s ease;
            page-break-inside: avoid;
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-2px);
        }}
        
        .slide-header {{
            padding: 1.5rem 2rem;
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            color: white;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .slide-number {{
            width: 48px;
            height: 48px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 700;
            flex-shrink: 0;
        }}
        
        .slide-title {{
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}
        
        .slide-filename {{
            font-size: 0.8rem;
            opacity: 0.8;
            margin-top: 0.25rem;
            font-weight: 400;
        }}
        
        .slide-body {{
            padding: 2rem;
        }}
        
        .slide-content {{
            color: var(--color-text);
            white-space: pre-wrap;
            font-size: 1rem;
            line-height: 1.8;
        }}
        
        .slide-content:empty::after {{
            content: 'No additional content';
            color: var(--color-text-muted);
            font-style: italic;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            background: var(--color-surface);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
        }}
        
        .empty-state h2 {{
            color: var(--color-text-muted);
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .empty-state p {{
            color: var(--color-text-muted);
        }}
        
        /* Print Styles */
        @media print {{
            body {{
                background: white;
                font-size: 12pt;
            }}
            
            .container {{
                max-width: 100%;
                padding: 0;
            }}
            
            .print-btn {{
                display: none !important;
            }}
            
            .header {{
                box-shadow: none;
                border: 1px solid var(--color-border);
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
                margin-bottom: 1rem;
            }}
            
            .slide-card:hover {{
                transform: none;
                box-shadow: none;
            }}
            
            .slide-header {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .toc-link:hover {{
                background: none;
            }}
            
            @page {{
                margin: 1.5cm;
            }}
        }}
        
        /* Responsive */
        @media (max-width: 640px) {{
            .container {{
                padding: 1rem;
            }}
            
            .header {{
                padding: 2rem 1.5rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .header .meta {{
                flex-direction: column;
                gap: 0.75rem;
            }}
            
            .section-body,
            .slide-body {{
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
        <header class="header">
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of presentation content</p>
            <div class="meta">
                <div class="meta-item">
                    <span>📊</span>
                    <span><strong>{len(slides)}</strong> Slides</span>
                </div>
                <div class="meta-item">
                    <span>📅</span>
                    <span>Generated: <strong>{timestamp}</strong></span>
                </div>
            </div>
        </header>
'''
    
    if not slides:
        html += '''
        <div class="empty-state">
            <h2>No Slides Found</h2>
            <p>No .txt files were found in the specified directory.</p>
        </div>
'''
    else:
        # Table of Contents
        html += '''
        <!-- Table of Contents -->
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">📑</span>
                    Table of Contents
                </h2>
            </div>
            <div class="section-body">
                <ol class="toc-list">
'''
        for slide in slides:
            html += f'''                    <li class="toc-item">
                        <span class="toc-number">{slide['slide_number']}</span>
                        <a href="#slide-{slide['slide_number']}" class="toc-link">{escape(slide['title'])}</a>
                    </li>
'''
        html += '''                </ol>
            </div>
        </section>
'''
        
        # Summary Section
        html += '''
        <!-- Summary -->
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">✨</span>
                    Executive Summary
                </h2>
            </div>
            <div class="section-body">
                <div class="summary-content">
'''
        for slide in slides:
            html += f'''                    <div class="summary-item">
                        <div class="summary-item-title">Slide {slide['slide_number']}: {escape(slide['title'])}</div>
                        <div class="summary-item-text">{escape(slide['summary'])}</div>
                    </div>
'''
        html += '''                </div>
            </div>
        </section>
'''
        
        # Slide Cards
        html += '''
        <!-- Slides -->
'''
        for slide in slides:
            html += f'''        <article class="slide-card" id="slide-{slide['slide_number']}">
            <div class="slide-header">
                <div class="slide-number">{slide['slide_number']}</div>
                <div>
                    <h3 class="slide-title">{escape(slide['title'])}</h3>
                    <div class="slide-filename">{escape(slide['filename'])}</div>
                </div>
            </div>
            <div class="slide-body">
                <div class="slide-content">{escape(slide['body'])}</div>
            </div>
        </article>
'''
    
    html += '''
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
    
    print(f"✅ Report generated: {output_path}")
    print(f"   • {len(slides)} slides processed")


def main():
    # Default directory is current directory, or use command line argument
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    # Output path
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = 'report.html'
    
    print(f"📂 Reading slides from: {os.path.abspath(directory)}")
    slides = read_slides(directory)
    
    if slides:
        print(f"📄 Found {len(slides)} slide(s)")
    else:
        print("⚠️  No .txt files found")
    
    generate_html(slides, output_path)


if __name__ == '__main__':
    main()