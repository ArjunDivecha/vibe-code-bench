#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt slide files and generates a beautiful HTML report
"""

import os
import sys
from pathlib import Path
import re


def read_slides(directory="."):
    """Read all .txt files in the directory and return sorted slide data"""
    slides = []
    
    # Find all .txt files
    txt_files = sorted(Path(directory).glob("*.txt"))
    
    for filepath in txt_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Extract title (first line) and body
        lines = content.split('\n')
        title = lines[0] if lines else filepath.stem
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        slides.append({
            'filename': filepath.name,
            'title': title,
            'body': body,
            'full_content': content
        })
    
    return slides


def generate_summary(slides, max_lines=3):
    """Generate a summary combining first few lines from each slide"""
    summary_parts = []
    
    for slide in slides:
        lines = slide['full_content'].split('\n')
        preview = '\n'.join(lines[:max_lines])
        summary_parts.append(f"**{slide['title']}**: {preview}")
    
    return summary_parts


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
    
    # Generate summary
    summary_parts = generate_summary(slides)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* === PREMIUM DESIGN SYSTEM === */
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --background: #f8fafc;
            --surface: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--background);
            padding: 0;
            margin: 0;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}
        
        /* === HEADER === */
        
        .header {{
            text-align: center;
            margin-bottom: 4rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}
        
        .header .subtitle {{
            font-size: 1.125rem;
            color: var(--text-secondary);
            font-weight: 400;
        }}
        
        .header .meta {{
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        /* === PRINT BUTTON === */
        
        .print-button {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 0.5rem;
            cursor: pointer;
            box-shadow: var(--shadow);
            transition: all 0.2s ease;
            margin-top: 1.5rem;
        }}
        
        .print-button:hover {{
            background: var(--primary-dark);
            box-shadow: var(--shadow-lg);
            transform: translateY(-1px);
        }}
        
        .print-button:active {{
            transform: translateY(0);
        }}
        
        /* === SECTION HEADERS === */
        
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section-title {{
            font-size: 1.875rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 3px solid var(--primary);
            letter-spacing: -0.025em;
        }}
        
        /* === TABLE OF CONTENTS === */
        
        .toc {{
            background: var(--surface);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            margin-bottom: 3rem;
        }}
        
        .toc-list {{
            list-style: none;
            counter-reset: slide-counter;
        }}
        
        .toc-item {{
            counter-increment: slide-counter;
            margin-bottom: 0.75rem;
        }}
        
        .toc-link {{
            display: flex;
            align-items: baseline;
            gap: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
        }}
        
        .toc-link:hover {{
            background: var(--background);
            border-left-color: var(--primary);
            transform: translateX(4px);
        }}
        
        .toc-number {{
            font-weight: 700;
            color: var(--primary);
            min-width: 2rem;
        }}
        
        .toc-number::before {{
            content: counter(slide-counter, decimal-leading-zero);
        }}
        
        /* === SUMMARY SECTION === */
        
        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow-xl);
            margin-bottom: 3rem;
        }}
        
        .summary .section-title {{
            color: white;
            border-bottom-color: rgba(255, 255, 255, 0.3);
        }}
        
        .summary-item {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-left: 4px solid rgba(255, 255, 255, 0.5);
        }}
        
        .summary-item:last-child {{
            margin-bottom: 0;
        }}
        
        .summary-item strong {{
            display: block;
            font-size: 1.125rem;
            margin-bottom: 0.5rem;
        }}
        
        /* === SLIDE CARDS === */
        
        .slides {{
            display: grid;
            gap: 2rem;
        }}
        
        .slide-card {{
            background: var(--surface);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            border: 1px solid var(--border);
            scroll-margin-top: 2rem;
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-2px);
        }}
        
        .slide-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .slide-number {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 3rem;
            height: 3rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            font-weight: 700;
            font-size: 1.25rem;
            border-radius: 0.75rem;
            box-shadow: var(--shadow);
        }}
        
        .slide-title {{
            flex: 1;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.025em;
        }}
        
        .slide-filename {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            background: var(--background);
            padding: 0.25rem 0.75rem;
            border-radius: 0.375rem;
            font-family: 'Monaco', 'Courier New', monospace;
        }}
        
        .slide-body {{
            color: var(--text-secondary);
            font-size: 1rem;
            line-height: 1.8;
            white-space: pre-wrap;
        }}
        
        /* === PRINT STYLES === */
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                max-width: 100%;
                padding: 0;
            }}
            
            .print-button {{
                display: none;
            }}
            
            .header {{
                page-break-after: avoid;
                margin-bottom: 2rem;
            }}
            
            .toc {{
                page-break-after: always;
                box-shadow: none;
                border: 1px solid var(--border);
            }}
            
            .summary {{
                page-break-after: always;
                box-shadow: none;
                background: #f0f0f0;
                color: black;
            }}
            
            .summary .section-title {{
                color: black;
            }}
            
            .slide-card {{
                page-break-inside: avoid;
                page-break-after: always;
                box-shadow: none;
                border: 1px solid var(--border);
                margin-bottom: 0;
            }}
            
            .slide-card:hover {{
                transform: none;
                box-shadow: none;
            }}
            
            .toc-link:hover {{
                transform: none;
            }}
            
            a {{
                text-decoration: none;
                color: inherit;
            }}
        }}
        
        /* === RESPONSIVE === */
        
        @media (max-width: 768px) {{
            .container {{
                padding: 2rem 1rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .section-title {{
                font-size: 1.5rem;
            }}
            
            .slide-header {{
                flex-wrap: wrap;
            }}
            
            .slide-title {{
                font-size: 1.25rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of all presentation slides</p>
            <p class="meta">Total Slides: {len(slides)}</p>
            <button class="print-button" onclick="window.print()">
                <span>🖨️</span>
                <span>Print to PDF</span>
            </button>
        </div>
        
        <!-- TABLE OF CONTENTS -->
        <div class="section">
            <div class="toc">
                <h2 class="section-title">📑 Table of Contents</h2>
                <ul class="toc-list">
"""
    
    # Add TOC items
    for i, slide in enumerate(slides, 1):
        html += f"""                    <li class="toc-item">
                        <a href="#slide-{i}" class="toc-link">
                            <span class="toc-number"></span>
                            <span>{escape_html(slide['title'])}</span>
                        </a>
                    </li>
"""
    
    html += """                </ul>
            </div>
        </div>
        
        <!-- SUMMARY SECTION -->
        <div class="section">
            <div class="summary">
                <h2 class="section-title">✨ Executive Summary</h2>
"""
    
    # Add summary items
    for part in summary_parts:
        html += f"""                <div class="summary-item">
                    {escape_html(part).replace('**', '<strong>').replace('</strong>:', ':</strong>')}
                </div>
"""
    
    html += """            </div>
        </div>
        
        <!-- SLIDES -->
        <div class="section">
            <h2 class="section-title">📄 All Slides</h2>
            <div class="slides">
"""
    
    # Add slide cards
    for i, slide in enumerate(slides, 1):
        html += f"""                <div class="slide-card" id="slide-{i}">
                    <div class="slide-header">
                        <div class="slide-number">{i}</div>
                        <h3 class="slide-title">{escape_html(slide['title'])}</h3>
                        <span class="slide-filename">{escape_html(slide['filename'])}</span>
                    </div>
                    <div class="slide-body">{escape_html(slide['body']) if slide['body'] else '<em>No content</em>'}</div>
                </div>
"""
    
    html += """            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def main():
    """Main function"""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"📂 Reading slides from: {directory}")
    
    # Read slides
    slides = read_slides(directory)
    
    if not slides:
        print("❌ No .txt files found in the directory!")
        return
    
    print(f"✅ Found {len(slides)} slides")
    
    # Generate HTML
    html = generate_html(slides)
    
    # Write report
    output_file = "report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✨ Report generated: {output_file}")
    print(f"📄 Open {output_file} in your browser to view the report")


if __name__ == "__main__":
    main()