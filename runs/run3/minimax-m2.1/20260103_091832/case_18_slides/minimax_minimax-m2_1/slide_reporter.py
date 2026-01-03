#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Default directory containing slide files
DEFAULT_SLIDES_DIR = "slides"


def get_slide_files(directory: str) -> List[Path]:
    """Get all .txt files from the specified directory, sorted naturally."""
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    txt_files = sorted(
        [f for f in dir_path.glob("*.txt") if f.is_file()],
        key=lambda f: int(f.stem.replace("slide", "")) if f.stem.replace("slide", "").isdigit() else 0
    )
    return txt_files


def read_slide_content(file_path: Path) -> Tuple[str, List[str]]:
    """Read a slide file and return title and all lines."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
    
    # First line is typically the title
    title = lines[0].strip() if lines else "Untitled Slide"
    return title, lines


def extract_summary_lines(all_slides: List[Tuple[str, List[str]]], num_lines: int = 3) -> str:
    """Extract the first few lines from each slide for the summary."""
    summary_parts = []
    for i, (title, lines) in enumerate(all_slides, 1):
        # Skip the title line, take next few lines
        content_lines = lines[1:1+num_lines]
        content = ' '.join(line.strip() for line in content_lines if line.strip())
        if content:
            summary_parts.append(f"• <strong>{title}:</strong> {content}...")
        else:
            summary_parts.append(f"• <strong>{title}</strong>")
    
    return '\n'.join(summary_parts)


def generate_html_report(
    slides_dir: str,
    output_file: str = "report.html"
) -> None:
    """Generate a beautiful HTML report from slide files."""
    
    # Read all slide files
    slide_files = get_slide_files(slides_dir)
    if not slide_files:
        raise ValueError(f"No .txt files found in directory: {slides_dir}")
    
    slides_data = []
    for file_path in slide_files:
        title, lines = read_slide_content(file_path)
        slides_data.append({
            'number': len(slides_data) + 1,
            'title': title,
            'content': lines,
            'filename': file_path.name
        })
    
    # Generate summary
    summary_html = extract_summary_lines([(s['title'], s['content']) for s in slides_data])
    
    # Build Table of Contents
    toc_items = []
    for slide in slides_data:
        toc_items.append(f'''
            <li class="toc-item">
                <a href="#slide-{slide['number']}" class="toc-link">
                    <span class="toc-number">{slide['number']}</span>
                    <span class="toc-title">{slide['title']}</span>
                </a>
            </li>
        ''')
    
    toc_html = '\n'.join(toc_items)
    
    # Build slide cards
    slide_cards = []
    for slide in slides_data:
        # Process content - preserve line breaks and add styling
        content_html = ''
        for i, line in enumerate(slide['content']):
            line = line.strip()
            if not line:
                continue
            
            # First line is title (already used), so skip or style differently
            if i == 0:
                continue
            
            # Check if it looks like a bullet point
            if line.startswith(('•', '-', '*', '○', '▪')):
                content_html += f'<li class="bullet-item">{line[1:].strip()}</li>\n'
            # Check if it's a numbered list
            elif line[0:2].replace('.', '').isdigit() and line[2:3] == ' ':
                content_html += f'<li class="numbered-item">{line}</li>\n'
            # Check if it's a subheader (all caps or ends with colon)
            elif line.isupper() or line.endswith(':'):
                content_html += f'<h4 class="subheader">{line}</h4>\n'
            else:
                content_html += f'<p class="content-line">{line}</p>\n'
        
        slide_cards.append(f'''
            <div class="slide-card" id="slide-{slide['number']}">
                <div class="slide-header">
                    <span class="slide-number">{slide['number']}</span>
                    <h2 class="slide-title">{slide['title']}</h2>
                </div>
                <div class="slide-content">
                    {content_html}
                </div>
                <div class="slide-footer">
                    <span class="slide-source">{slide['filename']}</span>
                </div>
            </div>
        ''')
    
    slides_html = '\n'.join(slide_cards)
    
    # Complete HTML document with premium CSS
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #1a1a2e;
            --secondary-color: #16213e;
            --accent-color: #0f3460;
            --highlight-color: #e94560;
            --text-primary: #2d3436;
            --text-secondary: #636e72;
            --text-light: #b2bec3;
            --bg-primary: #f8f9fa;
            --bg-white: #ffffff;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
            --shadow-xl: 0 16px 48px rgba(0,0,0,0.15);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            color: var(--text-primary);
            line-height: 1.7;
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        /* Header */
        .report-header {{
            text-align: center;
            margin-bottom: 50px;
            padding: 60px 40px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-xl);
            color: white;
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            pointer-events: none;
        }}

        .report-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
            position: relative;
        }}

        .report-subtitle {{
            font-size: 1.1rem;
            opacity: 0.85;
            font-weight: 300;
        }}

        .report-meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 25px;
            font-size: 0.9rem;
            opacity: 0.75;
        }}

        /* Print Button */
        .print-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 16px 32px;
            background: linear-gradient(135deg, var(--highlight-color) 0%, #d63447 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: var(--transition);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .print-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(233, 69, 96, 0.4);
        }}

        .print-btn svg {{
            width: 20px;
            height: 20px;
        }}

        /* Summary Section */
        .summary-section {{
            background: var(--bg-white);
            border-radius: var(--radius-lg);
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow-md);
            border: 1px solid rgba(0,0,0,0.04);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--bg-primary);
        }}

        .section-icon {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}

        .section-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--primary-color);
        }}

        .summary-content {{
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.8;
        }}

        .summary-content li {{
            margin-bottom: 10px;
            padding-left: 5px;
        }}

        /* Table of Contents */
        .toc-section {{
            background: var(--bg-white);
            border-radius: var(--radius-lg);
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: var(--shadow-md);
            border: 1px solid rgba(0,0,0,0.04);
        }}

        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }}

        .toc-item {{
            transition: var(--transition);
        }}

        .toc-link {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 20px;
            background: var(--bg-primary);
            border-radius: var(--radius-md);
            text-decoration: none;
            color: var(--text-primary);
            font-weight: 500;
            transition: var(--transition);
            border: 1px solid transparent;
        }}

        .toc-link:hover {{
            background: white;
            border-color: var(--accent-color);
            box-shadow: var(--shadow-sm);
            transform: translateX(4px);
        }}

        .toc-number {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 600;
            flex-shrink: 0;
        }}

        .toc-title {{
            font-size: 0.95rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Slide Cards */
        .slides-section {{
            display: flex;
            flex-direction: column;
            gap: 30px;
        }}

        .slide-card {{
            background: var(--bg-white);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-md);
            transition: var(--transition);
            border: 1px solid rgba(0,0,0,0.04);
            page-break-inside: avoid;
        }}

        .slide-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }}

        .slide-header {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 24px 30px;
            background: linear-gradient(135deg, var(--bg-primary) 0%, #ffffff 100%);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }}

        .slide-number {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 700;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(26, 26, 46, 0.3);
        }}

        .slide-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--primary-color);
        }}

        .slide-content {{
            padding: 30px;
        }}

        .slide-content p {{
            margin-bottom: 14px;
            font-size: 1rem;
            color: var(--text-secondary);
        }}

        .slide-content .subheader {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent-color);
            margin: 24px 0 14px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(0,0,0,0.06);
        }}

        .slide-content li {{
            margin-bottom: 10px;
            padding-left: 8px;
            color: var(--text-secondary);
        }}

        .bullet-item {{
            list-style: none;
            position: relative;
            padding-left: 20px;
        }}

        .bullet-item::before {{
            content: '→';
            position: absolute;
            left: 0;
            color: var(--highlight-color);
            font-weight: bold;
        }}

        .numbered-item {{
            list-style-type: none;
            padding-left: 24px;
            position: relative;
        }}

        .numbered-item::before {{
            content: attr(data-index);
            position: absolute;
            left: 0;
            color: var(--accent-color);
            font-weight: 600;
        }}

        .slide-footer {{
            padding: 14px 30px;
            background: var(--bg-primary);
            border-top: 1px solid rgba(0,0,0,0.05);
        }}

        .slide-source {{
            font-size: 0.8rem;
            color: var(--text-light);
            font-family: 'SF Mono', 'Consolas', monospace;
        }}

        /* Footer */
        .report-footer {{
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                padding: 0;
                font-size: 11pt;
            }}

            .container {{
                max-width: 100%;
                padding: 0;
            }}

            .print-btn {{
                display: none !important;
            }}

            .report-header {{
                background: var(--primary-color) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                border-radius: 0;
                padding: 30px;
                margin-bottom: 20px;
            }}

            .report-title {{
                font-size: 1.8rem;
            }}

            .summary-section,
            .toc-section,
            .slide-card {{
                box-shadow: none;
                border: 1px solid #ddd;
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            .slide-card {{
                margin-bottom: 20px;
                border-radius: 0;
            }}

            .slide-header {{
                background: #f5f5f5 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .slide-number {{
                background: var(--primary-color) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .toc-link:hover {{
                transform: none;
                box-shadow: none;
            }}

            .report-footer {{
                margin-top: 20px;
                padding: 20px 0;
            }}
        }}

        /* Page break for long content */
        @page {{
            margin: 1.5cm;
            @top-center {{
                content: 'Slide Summary Report';
                font-size: 9pt;
                color: #999;
            }};
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .report-title {{
                font-size: 2rem;
            }}

            .report-header {{
                padding: 40px 24px;
            }}

            .summary-section,
            .toc-section,
            .slide-card {{
                border-radius: var(--radius-md);
            }}

            .toc-list {{
                grid-template-columns: 1fr;
            }}

            .print-btn {{
                bottom: 20px;
                right: 20px;
                padding: 14px 24px;
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
            <p class="report-subtitle">Executive Overview & Detailed Analysis</p>
            <div class="report-meta">
                <span>📊 {len(slides_data)} Slides</span>
                <span>📁 {slides_dir}</span>
            </div>
        </header>

        <!-- Summary Section -->
        <section class="summary-section">
            <div class="section-header">
                <div class="section-icon">
                    <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                </div>
                <h2 class="section-title">Executive Summary</h2>
            </div>
            <div class="summary-content">
                <p>This report contains {len(slides_data)} slides covering the following key points:</p>
                <ul style="margin-top: 16px; margin-left: 8px;">
                    {summary_html}
                </ul>
            </div>
        </section>

        <!-- Table of Contents -->
        <section class="toc-section">
            <div class="section-header">
                <div class="section-icon">
                    <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </div>
                <h2 class="section-title">Table of Contents</h2>
            </div>
            <ul class="toc-list">
                {toc_html}
            </ul>
        </section>

        <!-- Slides Section -->
        <section class="slides-section">
            {slides_html}
        </section>

        <!-- Footer -->
        <footer class="report-footer">
            <p>Generated by Slide Summary Reporter • {slides_dir}</p>
        </footer>
    </div>

    <!-- Print Button -->
    <button class="print-btn" onclick="window.print()">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2M6 14h12v8H6v-8z"/>
        </svg>
        Print to PDF
    </button>

    <script>
        // Add smooth scroll behavior for TOC links
        document.querySelectorAll('.toc-link').forEach(link => {{
            link.addEventListener('click', (e) => {{
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const target = document.getElementById(targetId);
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});

        // Add animation on scroll
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('.slide-card').forEach(card => {{
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            observer.observe(card);
        }});
    </script>
</body>
</html>
'''
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Report generated successfully: {output_file}")
    print(f"   • {len(slides_data)} slides processed")
    print(f"   • Source directory: {slides_dir}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate a beautiful HTML report from slide text files."
    )
    parser.add_argument(
        '--dir', '-d',
        default=DEFAULT_SLIDES_DIR,
        help=f"Directory containing slide .txt files (default: {DEFAULT_SLIDES_DIR})"
    )
    parser.add_argument(
        '--output', '-o',
        default="report.html",
        help="Output HTML file name (default: report.html)"
    )
    
    args = parser.parse_args()
    
    try:
        generate_html_report(args.dir, args.output)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print(f"\nTo use this tool:")
        print(f"  1. Create a directory named '{args.dir}'")
        print(f"  2. Add your slide files (slide1.txt, slide2.txt, etc.)")
        print(f"  3. Run: python {sys.argv[0]} --dir {args.dir}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()