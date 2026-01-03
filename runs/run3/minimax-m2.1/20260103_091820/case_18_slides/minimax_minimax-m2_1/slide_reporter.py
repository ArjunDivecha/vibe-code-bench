#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and generates a beautiful HTML report.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple


def find_slide_files(directory: str) -> List[Path]:
    """Find all .txt files in the directory, sorted by filename."""
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    txt_files = sorted(dir_path.glob("*.txt"))
    return txt_files


def read_slide_content(file_path: Path) -> Tuple[str, str]:
    """Read a slide file and return its title and content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use filename (without extension) as title, or first line if it's short
    title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
    lines = content.strip().split('\n')
    
    # Clean up title if first line is very short (likely a title)
    if lines and len(lines[0].strip()) < 50:
        title = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()
    
    return title, content


def generate_summary(slides: List[Tuple[str, str]]) -> str:
    """Generate a summary combining the first few lines of each slide."""
    summary_parts = []
    for title, content in slides:
        lines = content.strip().split('\n')
        # Take first meaningful lines (up to 3 non-empty lines)
        excerpt_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Skip very short lines
                excerpt_lines.append(line)
            if len(excerpt_lines) >= 3:
                break
        
        if excerpt_lines:
            excerpt = ' '.join(excerpt_lines[:2])  # Use first 2 substantial lines
            if len(excerpt) > 200:
                excerpt = excerpt[:200] + '...'
            summary_parts.append(f"• <strong>{title}:</strong> {excerpt}")
    
    return '\n'.join(summary_parts)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def format_content(content: str) -> str:
    """Format slide content with proper paragraph breaks."""
    paragraphs = []
    for para in content.split('\n\n'):
        para = para.strip()
        if para:
            # Convert line breaks within paragraph to spaces
            para = ' '.join(para.split())
            paragraphs.append(f"<p>{escape_html(para)}</p>")
    return '\n'.join(paragraphs)


def generate_html_report(slides: List[Tuple[str, str]], output_path: str, title: str = "Slide Summary Report") -> None:
    """Generate the complete HTML report."""
    
    table_of_contents = []
    slide_cards = []
    
    for i, (slide_title, content) in enumerate(slides, 1):
        # Add to TOC
        toc_id = f"slide-{i}"
        table_of_contents.append(f'''
            <li class="toc-item">
                <a href="#{toc_id}" class="toc-link">
                    <span class="toc-number">{i:02d}</span>
                    <span class="toc-title">{escape_html(slide_title)}</span>
                </a>
            </li>
        ''')
        
        # Add slide card
        formatted_content = format_content(content)
        slide_cards.append(f'''
            <div class="slide-card" id="{toc_id}">
                <div class="slide-header">
                    <span class="slide-number">{i:02d}</span>
                    <h2 class="slide-title">{escape_html(slide_title)}</h2>
                </div>
                <div class="slide-content">
                    {formatted_content}
                </div>
            </div>
        ''')
    
    summary = generate_summary(slides)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(title)}</title>
    <style>
        /* ===== CSS Reset & Base ===== */
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        :root {{
            --primary-color: #1a365d;
            --secondary-color: #2c5282;
            --accent-color: #3182ce;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --text-muted: #718096;
            --bg-primary: #ffffff;
            --bg-secondary: #f7fafc;
            --bg-card: #ffffff;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 40px rgba(0,0,0,0.12);
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --font-sans: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-serif: 'Georgia', 'Times New Roman', serif;
            --transition: all 0.3s ease;
        }}

        @page {{
            margin: 1.5cm;
            size: A4 portrait;
        }}

        /* ===== Typography ===== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

        html {{
            font-size: 16px;
            scroll-behavior: smooth;
        }}

        body {{
            font-family: var(--font-sans);
            background: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* ===== Layout ===== */
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px 80px;
        }}

        /* ===== Header Section ===== */
        .report-header {{
            text-align: center;
            margin-bottom: 48px;
            padding: 48px 32px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: var(--radius-lg);
            color: white;
            box-shadow: var(--shadow-lg);
        }}

        .report-header h1 {{
            font-family: 'Playfair Display', var(--font-serif);
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }}

        .report-header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }}

        .report-meta {{
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 20px;
            font-size: 0.875rem;
            opacity: 0.85;
        }}

        /* ===== Print Button ===== */
        .print-button-container {{
            position: fixed;
            bottom: 32px;
            right: 32px;
            z-index: 1000;
        }}

        .print-button {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 14px 28px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: var(--transition);
        }}

        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 14px 50px rgba(0,0,0,0.2);
            background: var(--secondary-color);
        }}

        .print-button svg {{
            width: 20px;
            height: 20px;
        }}

        /* ===== Table of Contents ===== */
        .toc-section {{
            background: var(--bg-card);
            border-radius: var(--radius-md);
            padding: 32px;
            margin-bottom: 40px;
            box-shadow: var(--shadow-md);
        }}

        .toc-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--border-color);
        }}

        .toc-header svg {{
            width: 24px;
            height: 24px;
            color: var(--accent-color);
        }}

        .toc-header h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .toc-list {{
            list-style: none;
            display: grid;
            gap: 8px;
        }}

        .toc-item {{
            transition: var(--transition);
        }}

        .toc-link {{
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 14px 18px;
            text-decoration: none;
            color: var(--text-secondary);
            background: var(--bg-secondary);
            border-radius: var(--radius-sm);
            transition: var(--transition);
        }}

        .toc-link:hover {{
            background: #e6f0ff;
            color: var(--accent-color);
            transform: translateX(4px);
        }}

        .toc-number {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background: var(--primary-color);
            color: white;
            border-radius: 50%;
            font-size: 0.85rem;
            font-weight: 600;
            flex-shrink: 0;
        }}

        .toc-title {{
            font-weight: 500;
        }}

        /* ===== Summary Section ===== */
        .summary-section {{
            background: linear-gradient(135deg, #faf5ff 0%, #f0fff4 100%);
            border-radius: var(--radius-md);
            padding: 32px;
            margin-bottom: 40px;
            border: 1px solid #e9d8fd;
            position: relative;
            overflow: hidden;
        }}

        .summary-section::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #805ad5, #48bb78);
        }}

        .summary-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
        }}

        .summary-header svg {{
            width: 28px;
            height: 28px;
            color: #805ad5;
        }}

        .summary-header h2 {{
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .summary-content {{
            color: var(--text-secondary);
            line-height: 1.8;
        }}

        .summary-content li {{
            margin-bottom: 14px;
            padding-left: 4px;
        }}

        /* ===== Slide Cards ===== */
        .slides-container {{
            display: flex;
            flex-direction: column;
            gap: 32px;
        }}

        .slide-card {{
            background: var(--bg-card);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            overflow: hidden;
            transition: var(--transition);
            break-inside: avoid;
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
            padding: 24px 28px;
            background: linear-gradient(to right, var(--bg-secondary), var(--bg-primary));
            border-bottom: 1px solid var(--border-color);
        }}

        .slide-number {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: var(--radius-sm);
            font-size: 1.1rem;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .slide-title {{
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.3;
        }}

        .slide-content {{
            padding: 28px;
            color: var(--text-secondary);
        }}

        .slide-content p {{
            margin-bottom: 16px;
            text-align: justify;
        }}

        .slide-content p:last-child {{
            margin-bottom: 0;
        }}

        /* ===== Footer ===== */
        .report-footer {{
            margin-top: 60px;
            padding-top: 32px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* ===== Print Styles ===== */
        @media print {{
            body {{
                background: white;
                font-size: 12pt;
            }}

            .print-button-container {{
                display: none !important;
            }}

            .report-container {{
                max-width: 100%;
                padding: 0;
            }}

            .report-header {{
                background: var(--primary-color) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                box-shadow: none;
                border-radius: 0;
                margin-bottom: 24px;
                padding: 24px;
            }}

            .report-header h1 {{
                font-size: 1.75rem;
            }}

            .toc-section, .summary-section, .slide-card {{
                box-shadow: none;
                border: 1px solid #ddd;
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            .slide-card {{
                margin-bottom: 16px;
            }}

            .toc-link:hover, .slide-card:hover {{
                transform: none;
            }}

            .slide-number, .toc-number {{
                background: var(--primary-color) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .summary-section {{
                background: #faf5ff !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}

        /* ===== Responsive ===== */
        @media (max-width: 768px) {{
            .report-header h1 {{
                font-size: 1.75rem;
            }}

            .report-meta {{
                flex-direction: column;
                gap: 8px;
            }}

            .slide-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }}

            .print-button-container {{
                bottom: 16px;
                right: 16px;
            }}

            .print-button {{
                padding: 12px 20px;
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Header -->
        <header class="report-header">
            <h1>{escape_html(title)}</h1>
            <p class="subtitle">Generated Slide Summary Report</p>
            <div class="report-meta">
                <span>{len(slides)} Slides</span>
                <span>•</span>
                <span>Generated on {escape_html(__import__('datetime').datetime.now().strftime('%B %d, %Y'))}</span>
            </div>
        </header>

        <!-- Table of Contents -->
        <nav class="toc-section">
            <div class="toc-header">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                <h2>Table of Contents</h2>
            </div>
            <ol class="toc-list">
                {''.join(table_of_contents)}
            </ol>
        </nav>

        <!-- Summary Section -->
        <section class="summary-section">
            <div class="summary-header">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h2>Executive Summary</h2>
            </div>
            <div class="summary-content">
                <ul>
                    {summary}
                </ul>
            </div>
        </section>

        <!-- Slides Container -->
        <main class="slides-container">
            {''.join(slide_cards)}
        </main>

        <!-- Footer -->
        <footer class="report-footer">
            <p>Slide Summary Reporter • Generated automatically</p>
        </footer>
    </div>

    <!-- Print Button -->
    <div class="print-button-container">
        <button class="print-button" onclick="window.print()">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print to PDF
        </button>
    </div>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Report generated successfully: {output_path}")
    print(f"  - Total slides: {len(slides)}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate a beautiful HTML report from slide text files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python slide_reporter.py                    # Use default 'slides' directory
  python slide_reporter.py --dir my_slides    # Custom directory
  python slide_reporter.py --output report.html --title "My Presentation"
        """
    )
    
    parser.add_argument(
        '--dir', '-d',
        default='slides',
        help='Directory containing .txt slide files (default: slides)'
    )
    parser.add_argument(
        '--output', '-o',
        default='report.html',
        help='Output HTML file path (default: report.html)'
    )
    parser.add_argument(
        '--title', '-t',
        default='Slide Summary Report',
        help='Title for the report (default: Slide Summary Report)'
    )
    
    args = parser.parse_args()
    
    try:
        slide_files = find_slide_files(args.dir)
        
        if not slide_files:
            print(f"✗ No .txt files found in directory: {args.dir}")
            print("  Create some .txt files and run again.")
            sys.exit(1)
        
        print(f"Found {len(slide_files)} slide file(s) in '{args.dir}'")
        
        slides = []
        for file_path in slide_files:
            title, content = read_slide_content(file_path)
            slides.append((title, content))
            print(f"  • {title}")
        
        generate_html_report(slides, args.output, args.title)
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()