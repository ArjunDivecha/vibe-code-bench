#!/usr/bin/env python3
"""
Slide Summary Reporter - Convert text files into beautiful HTML reports
"""

import os
import re
import html
from pathlib import Path
from datetime import datetime

def read_slide_files(directory='.'):
    """Read all .txt files from the directory, sorted numerically"""
    slides = []
    txt_files = sorted([f for f in os.listdir(directory) if f.endswith('.txt')])
    
    # Sort numerically (slide1.txt, slide2.txt, etc.)
    txt_files.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    
    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # Only add non-empty files
                    slides.append({
                        'filename': filename,
                        'title': content.split('\n')[0].strip(),
                        'content': content,
                        'preview': ' '.join(content.split('\n')[:3]).strip()
                    })
        except Exception as e:
            print(f"Warning: Could not read {filename}: {e}")
    
    return slides

def escape_html(text):
    """Escape HTML special characters"""
    return html.escape(text)

def generate_html_report(slides, output_file='report.html'):
    """Generate a beautiful HTML report from slides"""
    
    # Generate summary from first few lines of each slide
    summary_items = [slide['preview'] for slide in slides[:5]]  # First 5 slides
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* Premium Typography & Design System */
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --accent-color: #f59e0b;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--background-color);
            font-size: 16px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        /* Header Section */
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem 0;
            background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%);
            color: white;
            border-radius: 16px;
            box-shadow: var(--shadow-xl);
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}

        .header .subtitle {{
            font-size: 1.25rem;
            opacity: 0.9;
            font-weight: 300;
        }}

        .header .date {{
            font-size: 0.875rem;
            opacity: 0.8;
            margin-top: 1rem;
        }}

        /* Print Button */
        .print-button {{
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            z-index: 1000;
        }}

        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}

        /* Table of Contents */
        .toc {{
            background: var(--card-background);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-md);
        }}

        .toc h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary-color);
        }}

        .toc-list {{
            list-style: none;
        }}

        .toc-item {{
            margin-bottom: 0.5rem;
        }}

        .toc-link {{
            color: var(--primary-color);
            text-decoration: none;
            padding: 0.5rem 0;
            display: block;
            transition: color 0.2s ease;
        }}

        .toc-link:hover {{
            color: var(--accent-color);
        }}

        /* Summary Section */
        .summary {{
            background: var(--card-background);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-md);
        }}

        .summary h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary-color);
        }}

        .summary-content {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            line-height: 1.7;
        }}

        /* Slide Cards */
        .slide-card {{
            background: var(--card-background);
            border-radius: 16px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
        }}

        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-4px);
        }}

        .slide-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}

        .slide-number {{
            background: var(--primary-color);
            color: white;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 1.1rem;
        }}

        .slide-title {{
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--text-primary);
            flex: 1;
            margin-left: 1rem;
        }}

        .slide-filename {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-family: 'Monaco', 'Menlo', monospace;
        }}

        .slide-content {{
            font-size: 1.1rem;
            line-height: 1.8;
            color: var(--text-secondary);
            white-space: pre-wrap;
        }}

        .slide-content p {{
            margin-bottom: 1rem;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background-color: white;
            }}

            .container {{
                padding: 0;
            }}

            .print-button {{
                display: none;
            }}

            .slide-card {{
                page-break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
                margin-bottom: 1rem;
            }}

            .header {{
                background: white;
                color: black;
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            .toc, .summary {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            h1, h2, h3 {{
                page-break-after: avoid;
            }}

            p {{
                orphans: 3;
                widows: 3;
            }}
        }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            .header h1 {{
                font-size: 2rem;
            }}

            .slide-card {{
                padding: 1.5rem;
            }}

            .print-button {{
                top: 1rem;
                right: 1rem;
                padding: 0.5rem 1rem;
            }}
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .slide-card {{
            animation: fadeIn 0.6s ease-out;
        }}

        .slide-card:nth-child(even) {{
            animation-delay: 0.1s;
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">
        📄 Print to PDF
    </button>

    <div class="container">
        <header class="header">
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of all presentation slides</p>
            <p class="date">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </header>

        <!-- Table of Contents -->
        <section class="toc">
            <h2>📋 Table of Contents</h2>
            <ul class="toc-list">
"""
    
    # Add TOC items
    for i, slide in enumerate(slides, 1):
        html_content += f'                <li class="toc-item"><a href="#slide-{i}" class="toc-link">Slide {i}: {escape_html(slide["title"])}</a></li>\n'
    
    html_content += """            </ul>
        </section>

        <!-- Summary Section -->
        <section class="summary">
            <h2>📊 Executive Summary</h2>
            <div class="summary-content">
                <p>This report contains {slide_count} slides with the following key topics:</p>
                <ul style="margin-top: 1rem; margin-left: 2rem;">
""".format(slide_count=len(slides))
    
    # Add summary items
    for item in summary_items:
        html_content += f'                    <li>{escape_html(item)}</li>\n'
    
    html_content += """                </ul>
            </div>
        </section>

        <!-- Slides -->
        <main>
"""
    
    # Add slide cards
    for i, slide in enumerate(slides, 1):
        html_content += f"""
            <article class="slide-card" id="slide-{i}">
                <div class="slide-header">
                    <div class="slide-number">{i}</div>
                    <h3 class="slide-title">{escape_html(slide['title'])}</h3>
                    <span class="slide-filename">{escape_html(slide['filename'])}</span>
                </div>
                <div class="slide-content">{escape_html(slide['content'])}</div>
            </article>
"""
    
    html_content += """
        </main>
    </div>

    <script>
        // Smooth scrolling for TOC links
        document.querySelectorAll('.toc-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Add scroll indicator
        window.addEventListener('scroll', function() {
            const scrolled = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
            document.documentElement.style.setProperty('--scroll-progress', scrolled + '%');
        });
    </script>
</body>
</html>
"""
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

def main():
    """Main function to run the slide reporter"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert text files representing slides into a beautiful HTML report'
    )
    parser.add_argument(
        '-d', '--directory',
        default='.',
        help='Directory containing slide text files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output',
        default='report.html',
        help='Output HTML file name (default: report.html)'
    )
    
    args = parser.parse_args()
    
    print(f"🔍 Scanning directory: {args.directory}")
    slides = read_slide_files(args.directory)
    
    if not slides:
        print("❌ No slide files found! Make sure you have .txt files in the directory.")
        return
    
    print(f"📊 Found {len(slides)} slides")
    print("🎨 Generating beautiful HTML report...")
    
    output_file = generate_html_report(slides, args.output)
    
    print(f"✅ Report generated: {output_file}")
    print("🌐 Open the file in your browser to view the report!")

if __name__ == '__main__':
    main()