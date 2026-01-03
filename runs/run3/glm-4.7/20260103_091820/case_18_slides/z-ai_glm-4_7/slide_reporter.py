#!/usr/bin/env python3
"""
Slide Summary Reporter
Reads .txt files from a directory and creates a beautiful HTML report.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime


def get_slide_number(filename):
    """Extract slide number from filename for sorting."""
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0


def read_slide_files(directory):
    """Read all .txt files in the directory, sorted by slide number."""
    slides = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    txt_files = sorted(dir_path.glob("*.txt"), key=lambda f: get_slide_number(f.name))
    
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in: {directory}")
    
    for filepath in txt_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        slides.append({
            'filename': filepath.stem,
            'content': content,
            'lines': content.split('\n'),
            'number': get_slide_number(filepath.name)
        })
    
    return slides


def generate_summary(slides, lines_per_slide=3):
    """Generate a summary combining first few lines of each slide."""
    summary_parts = []
    for slide in slides:
        title = slide['lines'][0] if slide['lines'] else slide['filename']
        preview_lines = [line.strip() for line in slide['lines'][1:lines_per_slide+1] if line.strip()]
        if preview_lines:
            summary_parts.append(f"<strong>{title}</strong>: {' '.join(preview_lines)}")
        else:
            summary_parts.append(f"<strong>{title}</strong>: (no content)")
    return ' '.join(summary_parts)


def generate_html(slides, output_path="report.html"):
    """Generate the HTML report."""
    summary = generate_summary(slides)
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: var(--text-primary);
            line-height: 1.7;
            min-height: 100vh;
            padding: 2rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        /* Header */
        header {{
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.6s ease-out;
        }}

        h1 {{
            font-size: 2.75rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.125rem;
            font-weight: 400;
        }}

        /* Print Button */
        .print-container {{
            text-align: center;
            margin-bottom: 2rem;
        }}

        .btn-print {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            padding: 0.875rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: var(--radius-lg);
            cursor: pointer;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
            font-family: inherit;
        }}

        .btn-print:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}

        .btn-print:active {{
            transform: translateY(0);
        }}

        .btn-print svg {{
            width: 20px;
            height: 20px;
        }}

        /* Cards */
        .card {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border);
            animation: fadeInUp 0.6s ease-out backwards;
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%);
        }}

        .card-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .card-badge {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .card-content {{
            color: var(--text-secondary);
            font-size: 1rem;
            white-space: pre-wrap;
            line-height: 1.8;
        }}

        /* Summary Section */
        .summary-section {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-left: 4px solid var(--primary);
        }}

        .summary-label {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.75rem;
        }}

        .summary-text {{
            color: var(--text-secondary);
            font-size: 1.05rem;
            line-height: 1.8;
        }}

        /* TOC Section */
        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 0.75rem;
        }}

        .toc-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            background: var(--bg-body);
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid var(--border);
        }}

        .toc-item:hover {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            transform: translateX(4px);
        }}

        .toc-number {{
            background: var(--primary-dark);
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

        .toc-item:hover .toc-number {{
            background: white;
            color: var(--primary);
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        /* Animations */
        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                max-width: 100%;
            }}

            .print-container {{
                display: none;
            }}

            .card {{
                box-shadow: none;
                border: 1px solid var(--border);
                page-break-inside: avoid;
                margin-bottom: 1.5rem;
            }}

            .card::before {{
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}

            .summary-section {{
                background: #f0f9ff !important;
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}

            .card-badge {{
                background: var(--primary) !important;
                color: white !important;
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}

            a {{
                text-decoration: none;
                color: var(--text-primary);
            }}

            .toc-item {{
                border: 1px solid var(--border);
                page-break-inside: avoid;
            }}

            h1 {{
                background: none;
                -webkit-text-fill-color: var(--text-primary);
                color: var(--text-primary);
            }}
        }}

        @page {{
            margin: 1.5cm;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Slide Summary Report</h1>
            <p class="subtitle">Generated on {timestamp} • {len(slides)} slides</p>
        </header>

        <div class="print-container">
            <button class="btn-print" onclick="window.print()">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Print to PDF
            </button>
        </div>

        <!-- Summary Section -->
        <div class="card summary-section" style="animation-delay: 0.1s;">
            <div class="summary-label">📝 Executive Summary</div>
            <div class="summary-text">{summary}</div>
        </div>

        <!-- Table of Contents -->
        <div class="card" style="animation-delay: 0.2s;">
            <h2 class="card-title">
                <span>📑</span>
                Table of Contents
            </h2>
            <nav class="toc-list">
"""

    # Add TOC items
    for i, slide in enumerate(slides):
        title = slide['lines'][0] if slide['lines'] else slide['filename']
        html += f"""
                <a href="#slide-{i + 1}" class="toc-item">
                    <span class="toc-number">{i + 1}</span>
                    <span>{title}</span>
                </a>
"""

    html += """
            </nav>
        </div>
"""

    # Add slide cards
    for i, slide in enumerate(slides):
        title = slide['lines'][0] if slide['lines'] else slide['filename']
        content_lines = slide['lines'][1:] if len(slide['lines']) > 1 else ['(No additional content)']
        content = '\n'.join(content_lines)
        
        html += f"""
        <div class="card" id="slide-{i + 1}" style="animation-delay: {0.3 + (i * 0.1)}s;">
            <h2 class="card-title">
                <span class="card-badge">Slide {i + 1}</span>
                {title}
            </h2>
            <div class="card-content">{content}</div>
        </div>
"""

    # Footer
    html += f"""
        <footer>
            <p>Slide Summary Report • Generated by Slide Reporter</p>
        </footer>
    </div>

    <script>
        // Smooth scroll for TOC links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
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
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python slide_reporter.py <directory> [output_file]")
        print("\nExample:")
        print("  python slide_reporter.py ./slides")
        print("  python slide_reporter.py ./slides custom_report.html")
        sys.exit(1)
    
    directory = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "report.html"
    
    try:
        print(f"📂 Reading slides from: {directory}")
        slides = read_slide_files(directory)
        print(f"✅ Found {len(slides)} slide file(s)")
        
        print(f"📝 Generating HTML report: {output_path}")
        generate_html(slides, output_path)
        
        print(f"✨ Report generated successfully!")
        print(f"📄 Open {output_path} in your browser to view the report")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()