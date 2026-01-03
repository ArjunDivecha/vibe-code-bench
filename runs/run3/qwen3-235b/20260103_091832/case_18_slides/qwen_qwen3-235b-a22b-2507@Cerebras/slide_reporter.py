import os
import re
from pathlib import Path

def read_slides(directory="."):
    """Read all .txt files in the directory and return sorted list of (title, content)"""
    slides = []
    for file_path in sorted(Path(directory).glob("slide*.txt")):
        if file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Use first line as title if available, else filename
                title = content.split('\n')[0].strip() if content else file_path.stem
                # Remove title from content if it's just the first line
                if '\n' in content:
                    body = '\n'.join(content.split('\n')[1:]).strip()
                else:
                    body = ""
                slides.append((title, body, file_path.name))
    return slides

def generate_summary(slides, max_lines_per_slide=2):
    """Generate summary by taking first few lines from each slide"""
    summary_items = []
    for title, content, _ in slides:
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        preview_lines = lines[:max_lines_per_slide]
        preview = ' '.join(preview_lines)
        # Truncate if too long
        if len(preview) > 200:
            preview = preview[:197] + "..."
        summary_items.append(f"<li><strong>{title}:</strong> {preview}</li>")
    return "\n".join(summary_items)

def create_html_report(slides, output_file="report.html"):
    """Generate a beautiful HTML report with table of contents and summary"""
    
    # Generate TOC
    toc_items = []
    for i, (title, _, filename) in enumerate(slides, 1):
        toc_items.append(f'<li><a href="#slide-{i}">Slide {i}: {title}</a></li>')
    
    # Generate summary
    summary_html = generate_summary(slides)
    
    # Generate slide cards
    slide_cards = []
    for i, (title, content, _) in enumerate(slides, 1):
        content_html = content.replace('\n', '<br>') if content else '<em class="no-content">No content</em>'
        slide_cards.append(f"""
<div class="slide-card" id="slide-{i}">
    <div class="slide-header">
        <span class="slide-number">Slide {i}</span>
        <h2 class="slide-title">{title}</h2>
    </div>
    <div class="slide-content">
        {content_html}
    </div>
</div>
        """.strip())

    # CSS styling
    css = """
<style>
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --gray-light: #f8f9fa;
        --gray: #e9ecef;
        --gray-dark: #343a40;
        --border: #dee2e6;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        color: var(--gray-dark);
        background-color: #fff;
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    .header {
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    
    .header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--gray-dark);
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .header p {
        color: #666;
        font-size: 1.1rem;
    }
    
    .print-button {
        display: block;
        width: 200px;
        margin: 0 auto 2.5rem;
        padding: 0.75rem 1.5rem;
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }
    
    .print-button:hover {
        background-color: var(--primary-dark);
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg);
    }
    
    .section {
        margin-bottom: 3rem;
        page-break-inside: avoid;
    }
    
    .section-title {
        font-size: 1.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary);
        color: var(--gray-dark);
        font-weight: 600;
        display: inline-block;
    }
    
    .toc ul {
        list-style: none;
        padding-left: 0;
    }
    
    .toc li {
        margin-bottom: 0.75rem;
    }
    
    .toc a {
        text-decoration: none;
        color: var(--primary);
        font-size: 1.1rem;
        font-weight: 500;
        transition: color 0.2s ease;
        display: block;
        padding: 0.5rem 1rem;
        border-left: 3px solid transparent;
    }
    
    .toc a:hover {
        color: var(--primary-dark);
        border-left-color: var(--primary);
        background-color: var(--gray-light);
    }
    
    .summary ul {
        list-style: disc;
        padding-left: 1.5rem;
    }
    
    .summary li {
        margin-bottom: 1rem;
        padding: 0.75rem;
        background-color: var(--gray-light);
        border-radius: 6px;
        border-left: 4px solid var(--primary);
    }
    
    .no-content {
        color: #999;
        font-style: italic;
    }
    
    .slide-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        transition: box-shadow 0.3s ease;
        page-break-after: always;
    }
    
    .slide-card:hover {
        box-shadow: var(--shadow-lg);
    }
    
    .slide-header {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    
    .slide-number {
        display: block;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .slide-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--gray-dark);
        margin: 0;
        line-height: 1.3;
    }
    
    .slide-content {
        padding: 1.75rem;
        font-size: 1.1rem;
        line-height: 1.8;
        color: #444;
    }
    
    .slide-content p {
        margin-bottom: 1rem;
    }
    
    .slide-content ul, .slide-content ol {
        padding-left: 1.5rem;
        margin: 1rem 0;
    }
    
    .slide-content li {
        margin-bottom: 0.5rem;
    }
    
    @media print {
        body {
            padding: 0.5cm;
        }
        
        .print-button {
            display: none;
        }
        
        .header {
            margin-bottom: 1.5cm;
        }
        
        .section {
            margin-bottom: 1.5cm;
        }
        
        .slide-card {
            page-break-after: always;
            border: 1px solid #000;
        }
        
        a[href]:after {
            content: none !important;
        }
    }
    
    @media (max-width: 768px) {
        body {
            padding: 1rem;
        }
        
        .header h1 {
            font-size: 2rem;
        }
        
        .section-title {
            font-size: 1.5rem;
        }
        
        .slide-title {
            font-size: 1.5rem;
        }
        
        .slide-content {
            font-size: 1rem;
            padding: 1.25rem;
        }
    }
</style>
    """.strip()

    # HTML template
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    {css}
</head>
<body>
    <div class="header">
        <h1>Slide Summary Report</h1>
        <p>A comprehensive overview of all presentation slides</p>
    </div>
    
    <button class="print-button" onclick="window.print()">🖨️ Print to PDF</button>
    
    <div class="section toc">
        <h2 class="section-title">Table of Contents</h2>
        <ul>
            {"".join(toc_items)}
        </ul>
    </div>
    
    <div class="section summary">
        <h2 class="section-title">Summary</h2>
        <ul>
            {summary_html}
        </ul>
    </div>
    
    {''.join(slide_cards)}
</body>
</html>"""

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report generated successfully: {output_file}")
    print(f"📁 Found {len(slides)} slides")
    print(f"🔗 Open {output_file} in your browser and click 'Print to PDF'")

if __name__ == "__main__":
    slides = read_slides()
    if not slides:
        print("❌ No slide files found! Please add files named like 'slide1.txt', 'slide2.txt', etc.")
    else:
        create_html_report(slides)