#!/usr/bin/env python3
"""
Slide Summary Reporter - Converts text files into a beautiful HTML report
"""

import os
import re
import html
from pathlib import Path


def read_slide_files(directory="."):
    """Read all .txt files in the directory, sorted numerically"""
    slides = []
    txt_files = sorted([f for f in os.listdir(directory) if f.endswith('.txt')])
    
    for filename in txt_files:
        path = os.path.join(directory, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append({
                'filename': filename,
                'title': content.split('\n')[0].strip('#').strip(),
                'content': content,
                'lines': content.split('\n')
            })
    
    return slides


def extract_summary(slides, max_lines=2):
    """Extract summary from first few lines of each slide"""
    summary = []
    for slide in slides[:5]:  # First 5 slides
        lines = [line.strip('#*-').strip() for line in slide['lines'][:max_lines] if line.strip()]
        summary.extend(lines)
    return summary[:10]  # Max 10 summary points


def create_html_report(slides, summary, output_file="report.html"):
    """Generate the HTML report with premium styling"""
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* Premium Typography & Design System */
        :root {
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
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--background-color);
            font-size: 16px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Header Section */
        .header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem 0;
            background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%);
            color: white;
            border-radius: 16px;
            box-shadow: var(--shadow-xl);
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }

        .header .subtitle {
            font-size: 1.25rem;
            opacity: 0.9;
            font-weight: 300;
        }

        /* Action Buttons */
        .actions {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 3rem;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background-color: var(--primary-color);
            color: white;
            box-shadow: var(--shadow-md);
        }

        .btn-primary:hover {
            background-color: #1d4ed8;
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }

        .btn-secondary {
            background-color: white;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background-color: var(--background-color);
        }

        /* TOC Section */
        .toc-section {
            background: var(--card-background);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-md);
        }

        .toc-section h2 {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            font-weight: 600;
        }

        .toc {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 0.5rem;
        }

        .toc-item {
            padding: 0.75rem 1rem;
            background: var(--background-color);
            border-radius: 8px;
            transition: all 0.2s ease;
            cursor: pointer;
            border: 1px solid transparent;
        }

        .toc-item:hover {
            background: var(--primary-color);
            color: white;
            transform: translateX(4px);
            border-color: var(--primary-color);
        }

        .toc-item a {
            text-decoration: none;
            color: inherit;
            font-weight: 500;
        }

        /* Summary Section */
        .summary-section {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-md);
            border: 1px solid #bae6fd;
        }

        .summary-section h2 {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: #0c4a6e;
            font-weight: 600;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }

        .summary-item {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid var(--accent-color);
            box-shadow: var(--shadow-sm);
        }

        /* Slide Cards */
        .slide-card {
            background: var(--card-background);
            border-radius: 16px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
        }

        .slide-card:hover {
            box-shadow: var(--shadow-xl);
            transform: translateY(-2px);
        }

        .slide-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }

        .slide-number {
            background: var(--primary-color);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 1.1rem;
        }

        .slide-title {
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--text-primary);
            flex: 1;
            margin-left: 1rem;
        }

        .slide-content {
            font-size: 1.1rem;
            line-height: 1.8;
            color: var(--text-secondary);
        }

        .slide-content h1, .slide-content h2, .slide-content h3 {
            color: var(--text-primary);
            margin: 1rem 0 0.5rem 0;
        }

        .slide-content ul, .slide-content ol {
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }

        .slide-content li {
            margin-bottom: 0.5rem;
        }

        /* Print Styles */
        @media print {
            body {
                background-color: white;
            }
            
            .container {
                padding: 0;
                max-width: 100%;
            }
            
            .header {
                background: white !important;
                color: black !important;
                box-shadow: none !important;
                border: 1px solid #ddd;
                break-inside: avoid;
            }
            
            .actions {
                display: none;
            }
            
            .slide-card {
                break-inside: avoid;
                box-shadow: none !important;
                border: 1px solid #ddd;
                margin-bottom: 1rem;
            }
            
            .toc-section, .summary-section {
                break-inside: avoid;
                box-shadow: none !important;
                border: 1px solid #ddd;
            }
            
            .toc-item:hover {
                transform: none;
                background: var(--background-color) !important;
                color: var(--text-primary) !important;
            }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .slide-card {
                padding: 1.5rem;
            }
            
            .slide-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .slide-title {
                margin-left: 0;
            }
        }

        /* Scroll to top button */
        .scroll-top {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--primary-color);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            border: none;
            font-size: 1.2rem;
        }

        .scroll-top:hover {
            background: #1d4ed8;
            transform: translateY(-2px);
        }

        .scroll-top.hidden {
            opacity: 0;
            visibility: hidden;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Comprehensive overview of all presentation slides</p>
        </header>

        <!-- Actions -->
        <div class="actions">
            <button class="btn btn-primary" onclick="window.print()">
                📄 Print to PDF
            </button>
            <button class="btn btn-secondary" onclick="toggleTOC()">
                📋 Toggle Table of Contents
            </button>
        </div>

        <!-- Table of Contents -->
        <section class="toc-section" id="toc-section">
            <h2>📚 Table of Contents</h2>
            <div class="toc">
                {toc_items}
            </div>
        </section>

        <!-- Summary -->
        <section class="summary-section">
            <h2>📝 Executive Summary</h2>
            <div class="summary-grid">
                {summary_items}
            </div>
        </section>

        <!-- Slides -->
        <main>
            {slide_cards}
        </main>
    </div>

    <!-- Scroll to top -->
    <button class="scroll-top hidden" id="scroll-top" onclick="scrollToTop()">↑</button>

    <script>
        // Show/hide scroll to top button
        window.addEventListener('scroll', function() {
            const scrollTop = document.getElementById('scroll-top');
            if (window.pageYOffset > 300) {
                scrollTop.classList.remove('hidden');
            } else {
                scrollTop.classList.add('hidden');
            }
        });

        function scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function toggleTOC() {
            const toc = document.getElementById('toc-section');
            toc.style.display = toc.style.display === 'none' ? 'block' : 'none';
        }

        // Smooth scrolling for TOC links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>"""

    # Generate TOC items
    toc_items = []
    for i, slide in enumerate(slides, 1):
        toc_items.append(f"""
            <div class="toc-item">
                <a href="#slide-{i}">Slide {i}: {html.escape(slide['title'])}</a>
            </div>
        """)
    
    # Generate summary items
    summary_items = []
    for point in summary:
        summary_items.append(f"""
            <div class="summary-item">
                {html.escape(point)}
            </div>
        """)
    
    # Generate slide cards
    slide_cards = []
    for i, slide in enumerate(slides, 1):
        # Format slide content
        content = format_slide_content(slide['content'])
        
        slide_cards.append(f"""
            <article class="slide-card" id="slide-{i}">
                <div class="slide-header">
                    <div class="slide-number">{i}</div>
                    <h2 class="slide-title">{html.escape(slide['title'])}</h2>
                    <small>Source: {html.escape(slide['filename'])}</small>
                </div>
                <div class="slide-content">
                    {content}
                </div>
            </article>
        """)
    
    # Fill in the template
    html_content = html_template.format(
        toc_items='\n'.join(toc_items),
        summary_items='\n'.join(summary_items),
        slide_cards='\n'.join(slide_cards)
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def format_slide_content(content):
    """Format slide content with proper HTML"""
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Headers
        if line.startswith('#'):
            level = len(line.split()[0])
            text = line.strip('#').strip()
            formatted_lines.append(f'<h{level}>{html.escape(text)}</h{level}>')
        
        # Bullet points
        elif line.startswith('-') or line.startswith('*'):
            text = line.strip('-*').strip()
            formatted_lines.append(f'<li>{html.escape(text)}</li>')
        
        # Numbers
        elif re.match(r'^\d+\.', line):
            text = re.sub(r'^\d+\.', '', line).strip()
            formatted_lines.append(f'<li>{html.escape(text)}</li>')
        
        # Regular paragraphs
        else:
            formatted_lines.append(f'<p>{html.escape(line)}</p>')
    
    # Group consecutive list items
    result = []
    in_list = False
    list_type = None
    
    for line in formatted_lines:
        if line.startswith('<li>'):
            if not in_list:
                # Determine list type based on first item
                if re.match(r'<li>\d+\.', line):
                    list_type = 'ol'
                else:
                    list_type = 'ul'
                result.append(f'<{list_type}>')
                in_list = True
            result.append(line)
        else:
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
            result.append(line)
    
    if in_list:
        result.append(f'</{list_type}>')
    
    return '\n'.join(result)


def main():
    """Main function to generate the report"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate a beautiful HTML report from slide text files')
    parser.add_argument('--directory', '-d', default='.', help='Directory containing .txt slide files')
    parser.add_argument('--output', '-o', default='report.html', help='Output HTML file name')
    
    args = parser.parse_args()
    
    print(f"🔍 Scanning directory: {args.directory}")
    slides = read_slide_files(args.directory)
    
    if not slides:
        print("❌ No .txt slide files found in the directory!")
        return
    
    print(f"📊 Found {len(slides)} slide files")
    
    summary = extract_summary(slides)
    
    print("🎨 Generating HTML report...")
    output_file = create_html_report(slides, summary, args.output)
    
    print(f"✅ Report generated: {output_file}")
    print(f"📄 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print("🌟 Open the file in your browser to view the beautiful report!")


if __name__ == "__main__":
    main()