#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime


def get_slide_files(directory):
    """Get all .txt files from the directory, sorted naturally."""
    files = []
    for file in os.listdir(directory):
        if file.endswith('.txt'):
            files.append(file)
    
    # Natural sort (slide1, slide2, slide10 instead of slide1, slide10, slide2)
    def natural_sort_key(filename):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', filename)]
    
    return sorted(files, key=natural_sort_key)


def read_slide_content(filepath):
    """Read the content of a slide file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        return f"[Error reading file: {e}]"


def get_first_lines(content, num_lines=2):
    """Get the first few lines of content for summary."""
    lines = content.split('\n')
    first_lines = [line.strip() for line in lines[:num_lines] if line.strip()]
    return ' '.join(first_lines)


def generate_html_report(directory, output_file='report.html'):
    """Generate the HTML report from slide files."""
    slide_files = get_slide_files(directory)
    
    if not slide_files:
        print(f"No .txt files found in {directory}")
        return False
    
    # Read all slides
    slides = []
    for filename in slide_files:
        filepath = os.path.join(directory, filename)
        content = read_slide_content(filepath)
        slide_title = filename.replace('.txt', '').replace('_', ' ').title()
        slides.append({
            'filename': filename,
            'title': slide_title,
            'content': content,
            'summary': get_first_lines(content, 2)
        })
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* ============================================
           PREMIUM CSS STYLES
           ============================================ */
        
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
        
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --accent: #f59e0b;
            --bg-primary: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.5;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .header h1 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }}
        
        .header .subtitle {{
            font-size: 1.125rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .header .meta {{
            margin-top: 1.5rem;
            font-size: 0.875rem;
            opacity: 0.75;
        }}
        
        /* Print Button */
        .print-btn {{
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: white;
            color: var(--primary);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            font-family: inherit;
            font-weight: 600;
            font-size: 0.875rem;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}
        
        .print-btn svg {{
            width: 18px;
            height: 18px;
        }}
        
        /* Container */
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}
        
        /* Section Styles */
        .section {{
            margin-bottom: 4rem;
        }}
        
        .section-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .section-title::before {{
            content: '';
            width: 4px;
            height: 2rem;
            background: var(--primary);
            border-radius: 2px;
        }}
        
        /* Summary Section */
        .summary-box {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }}
        
        .summary-intro {{
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            font-size: 1rem;
        }}
        
        .summary-grid {{
            display: grid;
            gap: 1rem;
        }}
        
        .summary-item {{
            display: flex;
            gap: 1rem;
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 12px;
            transition: all 0.2s ease;
        }}
        
        .summary-item:hover {{
            background: #f1f5f9;
        }}
        
        .summary-item-number {{
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            background: var(--primary);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.875rem;
        }}
        
        .summary-item-content {{
            flex: 1;
        }}
        
        .summary-item-title {{
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }}
        
        .summary-item-text {{
            color: var(--text-secondary);
            font-size: 0.9375rem;
            line-height: 1.5;
        }}
        
        /* Table of Contents */
        .toc {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }}
        
        .toc-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 0.75rem;
        }}
        
        .toc-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.875rem 1rem;
            background: var(--bg-primary);
            border-radius: 10px;
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}
        
        .toc-item:hover {{
            background: white;
            border-color: var(--primary);
            box-shadow: var(--shadow-md);
            transform: translateX(4px);
        }}
        
        .toc-item-number {{
            width: 28px;
            height: 28px;
            background: var(--primary);
            color: white;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.8125rem;
            flex-shrink: 0;
        }}
        
        .toc-item-title {{
            font-weight: 500;
        }}
        
        /* Slide Cards */
        .slides-grid {{
            display: grid;
            gap: 2rem;
        }}
        
        .slide-card {{
            background: var(--bg-card);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-4px);
        }}
        
        .slide-card-header {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .slide-card-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .slide-card-number {{
            width: 40px;
            height: 40px;
            background: var(--primary);
            color: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.125rem;
        }}
        
        .slide-card-badge {{
            background: var(--accent);
            color: white;
            padding: 0.375rem 0.875rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .slide-card-content {{
            padding: 2rem;
        }}
        
        .slide-card-text {{
            color: var(--text-secondary);
            font-size: 1.0625rem;
            line-height: 1.8;
            white-space: pre-wrap;
        }}
        
        .slide-card-text p {{
            margin-bottom: 1rem;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
            border-top: 1px solid var(--border-color);
            margin-top: 4rem;
        }}
        
        /* ============================================
           PRINT STYLES
           ============================================ */
        
        @media print {{
            .print-btn {{
                display: none;
            }}
            
            body {{
                background: white;
            }}
            
            .header {{
                background: var(--primary) !important;
                color: white !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .slide-card {{
                box-shadow: none;
                border: 1px solid var(--border-color);
                break-inside: avoid;
                page-break-inside: avoid;
                margin-bottom: 2rem;
            }}
            
            .slide-card:hover {{
                transform: none;
            }}
            
            .section {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}
            
            .summary-item, .toc-item {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}
            
            a {{
                text-decoration: none;
                color: var(--text-primary) !important;
            }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .container {{
                padding: 2rem 1rem;
            }}
            
            .toc-list {{
                grid-template-columns: 1fr;
            }}
            
            .slide-card-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }}
            
            .print-btn {{
                top: 1rem;
                right: 1rem;
                padding: 0.5rem 1rem;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print to PDF
    </button>
    
    <header class="header">
        <div class="header-content">
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of presentation slides</p>
            <p class="meta">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} • {len(slides)} slides</p>
        </div>
    </header>
    
    <div class="container">
        <!-- Summary Section -->
        <section class="section" id="summary">
            <h2 class="section-title">Executive Summary</h2>
            <div class="summary-box">
                <p class="summary-intro">Quick overview of key points from each slide:</p>
                <div class="summary-grid">
"""
    
    # Add summary items
    for idx, slide in enumerate(slides, 1):
        html += f"""
                    <div class="summary-item">
                        <div class="summary-item-number">{idx}</div>
                        <div class="summary-item-content">
                            <div class="summary-item-title">{slide['title']}</div>
                            <div class="summary-item-text">{slide['summary'] or 'No content available'}</div>
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </section>
        
        <!-- Table of Contents -->
        <section class="section" id="toc">
            <h2 class="section-title">Table of Contents</h2>
            <div class="toc">
                <div class="toc-list">
"""
    
    # Add TOC items
    for idx, slide in enumerate(slides, 1):
        html += f"""
                    <a href="#slide-{idx}" class="toc-item">
                        <div class="toc-item-number">{idx}</div>
                        <span class="toc-item-title">{slide['title']}</span>
                    </a>
"""
    
    html += """
                </div>
            </div>
        </section>
        
        <!-- Slides -->
        <section class="section" id="slides">
            <h2 class="section-title">Slide Details</h2>
            <div class="slides-grid">
"""
    
    # Add slide cards
    for idx, slide in enumerate(slides, 1):
        # Escape HTML special characters in content
        escaped_content = slide['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html += f"""
                <article class="slide-card" id="slide-{idx}">
                    <div class="slide-card-header">
                        <div class="slide-card-title">
                            <span class="slide-card-number">{idx}</span>
                            {slide['title']}
                        </div>
                        <span class="slide-card-badge">Slide</span>
                    </div>
                    <div class="slide-card-content">
                        <div class="slide-card-text">{escaped_content}</div>
                    </div>
                </article>
"""
    
    html += f"""
            </div>
        </section>
    </div>
    
    <footer class="footer">
        <p>Slide Summary Report • Generated by Slide Reporter • {datetime.now().strftime('%Y')}</p>
    </footer>
    
    <script>
        // Smooth scroll for TOC links
        document.querySelectorAll('.toc-item').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Report generated: {output_file}")
    print(f"  - {len(slides)} slides processed")
    print(f"  - Open {output_file} in your browser to view")
    
    return True


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("Enter directory path containing slide .txt files: ").strip()
    
    directory = os.path.abspath(directory)
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        sys.exit(1)
    
    output_file = os.path.join(directory, 'report.html')
    
    print(f"\n📊 Slide Summary Reporter")
    print(f"{'='*40}")
    print(f"Scanning directory: {directory}\n")
    
    if generate_html_report(directory, output_file):
        print(f"\n✓ Done!")


if __name__ == '__main__':
    main()