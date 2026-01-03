#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads text files representing PowerPoint slides and generates a beautiful HTML report.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple
from datetime import datetime


def read_slides(directory: str) -> List[Tuple[str, str]]:
    """Read all .txt files from the directory and return list of (filename, content) tuples."""
    slides = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    txt_files = sorted(dir_path.glob("slide*.txt"))
    
    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        slides.append((txt_file.name, content))
    
    return slides


def generate_summary(slides: List[Tuple[str, str]], lines_per_slide: int = 3) -> str:
    """Generate a summary by combining the first few lines of each slide."""
    summary_parts = []
    
    for filename, content in slides:
        first_lines = content.strip().split('\n')[:lines_per_slide]
        summary_text = ' '.join(line.strip() for line in first_lines if line.strip())
        if summary_text:
            summary_parts.append(f"• {summary_text}")
    
    return '\n'.join(summary_parts)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def generate_html_report(slides: List[Tuple[str, str]], output_path: str, summary: str):
    """Generate the complete HTML report with premium styling."""
    
    # Generate date first (before f-string)
    generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Generate TOC items
    toc_items = []
    for i, (filename, _) in enumerate(slides, 1):
        slide_id = f"slide-{i}"
        toc_items.append(f'''                <a href="#{slide_id}" class="toc-item" data-target="{slide_id}">
                    <span class="toc-number">{i}</span>
                    <span class="toc-filename">{escape_html(filename)}</span>
                </a>''')
    
    # Generate slide cards
    slide_cards = []
    for i, (filename, content) in enumerate(slides, 1):
        slide_id = f"slide-{i}"
        word_count = len(content.split())
        line_count = len([l for l in content.split('\n') if l.strip()])
        
        # Format content with paragraphs
        paragraphs = []
        for para in content.strip().split('\n\n'):
            para = para.strip()
            if para:
                # Convert URLs to links
                para = re.sub(r'(https?://\S+)', r'<a href="\1" target="_blank" style="color: var(--highlight-color);">\1</a>', para)
                paragraphs.append(f'<p>{escape_html(para)}</p>')
        
        content_html = '\n'.join(paragraphs) if paragraphs else f'<p>{escape_html(content)}</p>'
        
        slide_cards.append(f'''            <div class="slide-card" id="{slide_id}">
                <div class="slide-header">
                    <div class="slide-number">{i}</div>
                    <div class="slide-info">
                        <div class="slide-filename">{escape_html(filename)}</div>
                        <div class="slide-meta">{word_count} words • {line_count} lines</div>
                    </div>
                </div>
                <div class="slide-content">
                    {content_html}
                </div>
            </div>''')
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary-color: #1a1a2e;
            --secondary-color: #16213e;
            --accent-color: #0f3460;
            --highlight-color: #e94560;
            --text-color: #2d3436;
            --text-light: #636e72;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
            --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.12);
            --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.15);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.7;
            font-size: 16px;
        }}

        /* Print Button */
        .print-button {{
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 1000;
            background: linear-gradient(135deg, var(--highlight-color), #ff6b6b);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-md);
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}

        .print-button svg {{
            width: 18px;
            height: 18px;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 80px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            animation: pulse 15s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}

        .header-content {{
            position: relative;
            z-index: 1;
            max-width: 900px;
            margin: 0 auto;
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        .header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }}

        .meta-info {{
            margin-top: 24px;
            font-size: 0.9rem;
            opacity: 0.7;
        }}

        /* Container */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        /* Table of Contents */
        .toc-section {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow-sm);
            border: 1px solid rgba(0,0,0,0.05);
        }}

        .toc-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .toc-title::before {{
            content: '';
            width: 4px;
            height: 28px;
            background: linear-gradient(180deg, var(--highlight-color), #ff6b6b);
            border-radius: 2px;
        }}

        .toc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }}

        .toc-item {{
            display: flex;
            align-items: center;
            padding: 16px 20px;
            background: var(--bg-color);
            border-radius: 10px;
            transition: var(--transition);
            cursor: pointer;
            text-decoration: none;
            color: inherit;
        }}

        .toc-item:hover {{
            background: var(--accent-color);
            color: white;
            transform: translateX(4px);
        }}

        .toc-number {{
            width: 32px;
            height: 32px;
            background: var(--primary-color);
            color: white;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            margin-right: 16px;
            flex-shrink: 0;
        }}

        .toc-item:hover .toc-number {{
            background: rgba(255,255,255,0.2);
        }}

        .toc-filename {{
            font-weight: 500;
            font-size: 0.95rem;
        }}

        /* Summary Section */
        .summary-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 40px;
            color: white;
            box-shadow: var(--shadow-md);
        }}

        .summary-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .summary-title svg {{
            width: 28px;
            height: 28px;
        }}

        .summary-content {{
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            padding: 28px;
            line-height: 1.8;
            font-size: 1.05rem;
            backdrop-filter: blur(10px);
        }}

        .summary-content p {{
            margin-bottom: 12px;
        }}

        .summary-content p:last-child {{
            margin-bottom: 0;
        }}

        /* Slides Section */
        .slides-section {{
            margin-top: 40px;
        }}

        .slides-title {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 32px;
            padding-bottom: 16px;
            border-bottom: 3px solid var(--highlight-color);
            display: inline-block;
        }}

        /* Slide Cards */
        .slide-card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 32px;
            box-shadow: var(--shadow-sm);
            border: 1px solid rgba(0,0,0,0.05);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }}

        .slide-card:hover {{
            box-shadow: var(--shadow-md);
            transform: translateY(-4px);
        }}

        .slide-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--highlight-color), #ff6b6b, #feca57);
        }}

        .slide-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #eee;
        }}

        .slide-number {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.2rem;
            margin-right: 20px;
            flex-shrink: 0;
        }}

        .slide-info {{
            flex: 1;
        }}

        .slide-filename {{
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--primary-color);
        }}

        .slide-meta {{
            font-size: 0.85rem;
            color: var(--text-light);
            margin-top: 4px;
        }}

        .slide-content {{
            font-size: 1rem;
            line-height: 1.8;
            white-space: pre-wrap;
            color: var(--text-color);
        }}

        .slide-content p {{
            margin-bottom: 16px;
        }}

        .slide-content p:last-child {{
            margin-bottom: 0;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px;
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        .footer hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #ddd, transparent);
            margin-bottom: 20px;
        }}

        /* Page Break Styles for Print */
        @media print {{
            .print-button {{
                display: none !important;
            }}

            body {{
                background: white;
                font-size: 12pt;
            }}

            .header {{
                background: var(--primary-color) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                padding: 40px 30px;
            }}

            .header h1 {{
                font-size: 2rem;
            }}

            .container {{
                padding: 20px;
                max-width: 100%;
            }}

            .toc-section {{
                break-after: page;
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            .summary-section {{
                break-after: page;
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            .slide-card {{
                break-inside: avoid;
                page-break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
                margin-bottom: 20px;
            }}

            .slide-card::before {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .slide-number {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .toc-item:hover {{
                background: #f0f0f0 !important;
                -webkit-print-color                print-color-adjust: exact;
            }}
        }}

        /* Responsive */
        @media (max-width: 768-adjust: exact;
px) {{
            .header {{
                padding: 60px 24px;
            }}

            .header h1 {{
                font-size: 2rem;
            }}

            .toc-grid {{
                grid-template-columns: 1fr;
            }}

            .slide-card {{
                padding: 24px;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print to PDF
    </button>

    <header class="header">
        <div class="header-content">
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Automated Presentation Overview</p>
            <p class="meta-info">{len(slides)} slides processed • Generated on {generated_date}</p>
        </div>
    </header>

    <div class="container">
        <!-- Table of Contents -->
        <section class="toc-section">
            <h2 class="toc-title">Table of Contents</h2>
            <div class="toc-grid">
{chr(10).join(toc_items)}
            </div>
        </section>

        <!-- Summary Section -->
        <section class="summary-section">
            <h2 class="summary-title">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Executive Summary
            </h2>
            <div class="summary-content">
                <p>{escape_html(summary)}</p>
            </div>
        </section>

        <!-- Slides Section -->
        <section class="slides-section">
            <h2 class="slides-title">Slide Details</h2>
{chr(10).join(slide_cards)}
        </section>
    </div>

    <footer class="footer">
        <hr>
        <p>Slide Summary Reporter • Generated automatically from text files</p>
    </footer>

    <script>
        // Smooth scroll for TOC items
        document.querySelectorAll('.toc-item').forEach(item => {{
            item.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('data-target');
                const targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return len(slides)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate a beautiful HTML report from slide text files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python slide_reporter.py                    # Use current directory
  python slide_reporter.py ./my_slides        # Specify directory
  python slide_reporter.py -o custom.html     # Custom output filename
        '''
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing slide*.txt files (default: current directory)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='report.html',
        help='Output HTML filename (default: report.html)'
    )
    
    parser.add_argument(
        '--summary-lines',
        type=int,
        default=3,
        help='Number of lines per slide to include in summary (default: 3)'
    )
    
    args = parser.parse_args()
    
    try:
        print(f"📂 Reading slides from: {args.directory}")
        slides = read_slides(args.directory)
        
        if not slides:
            print("⚠️  No slide*.txt files found in the directory!")
            print("   Expected files named: slide1.txt, slide2.txt, etc.")
            sys.exit(1)
        
        print(f"📄 Found {len(slides)} slide file(s)")
        
        print("📝 Generating summary...")
        summary = generate_summary(slides, args.summary_lines)
        
        print("🎨 Generating HTML report with premium styling...")
        slide_count = generate_html_report(slides, args.output, summary)
        
        print(f"✅ Success! Created: {args.output}")
        print(f"   • {slide_count} slide cards")
        print(f"   • Auto-generated Table of Contents")
        print(f"   • Executive Summary")
        print(f"   • Print-ready with PDF support")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()