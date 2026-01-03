import os
import re
import html

def natural_sort_key(s):
    """
    Sort strings containing numbers naturally (e.g. slide1, slide2, slide10).
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def get_slide_files(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    return sorted(files, key=natural_sort_key)

def read_slide(filepath):
    """
    Reads a slide file.
    Returns a dict with 'title', 'content', 'summary'.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Basic parsing: Title is filename or first line if it looks like a title
    filename = os.path.basename(filepath)
    title = filename.replace('.txt', '').replace('_', ' ').title()
    
    content_lines = [line.strip() for line in lines]
    full_text = '\n'.join(lines)
    
    # Extract summary: First non-empty paragraph (up to 300 chars)
    summary_text = ""
    for line in content_lines:
        if line and not line.startswith('-') and not line.startswith('='):
            summary_text += line + " "
            if len(summary_text) > 150:
                break
    
    return {
        'id': filename.replace('.', '_'),
        'title': title,
        'filename': filename,
        'content': full_text,
        'summary': summary_text.strip() + "..."
    }

def generate_html(slides):
    # CSS Styles
    css = """
    :root {
        --bg-color: #f8f9fa;
        --card-bg: #ffffff;
        --text-primary: #1a1a1a;
        --text-secondary: #555555;
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --border-color: #e5e7eb;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    body {
        font-family: var(--font-family);
        background-color: var(--bg-color);
        color: var(--text-primary);
        line-height: 1.6;
        margin: 0;
        padding: 40px;
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
    }

    header {
        margin-bottom: 40px;
        text-align: center;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 20px;
    }

    h1 {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin-bottom: 10px;
        color: #111;
    }

    .meta {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .btn {
        background-color: var(--accent);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.2s;
        font-size: 0.9rem;
        margin-top: 15px;
    }

    .btn:hover {
        background-color: var(--accent-hover);
    }

    /* Summary Section */
    .summary-section {
        background: var(--card-bg);
        padding: 30px;
        border-radius: 12px;
        box-shadow: var(--shadow-md);
        margin-bottom: 40px;
        border-left: 5px solid var(--accent);
    }

    .summary-section h2 {
        margin-top: 0;
        font-size: 1.5rem;
    }

    /* TOC */
    .toc {
        background: var(--card-bg);
        padding: 20px 30px;
        border-radius: 12px;
        box-shadow: var(--shadow-sm);
        margin-bottom: 40px;
    }

    .toc h3 {
        margin-top: 0;
        font-size: 1.2rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .toc ul {
        list-style: none;
        padding: 0;
    }

    .toc li {
        margin-bottom: 8px;
    }

    .toc a {
        text-decoration: none;
        color: var(--accent);
        font-weight: 500;
    }

    .toc a:hover {
        text-decoration: underline;
    }

    /* Slide Cards */
    .slide-card {
        background: var(--card-bg);
        border-radius: 12px;
        box-shadow: var(--shadow-md);
        padding: 40px;
        margin-bottom: 40px;
        page-break-inside: avoid;
        break-inside: avoid;
        transition: transform 0.2s;
    }

    .slide-card:hover {
        transform: translateY(-2px);
    }

    .slide-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--border-color);
    }

    .slide-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }

    .slide-id {
        font-family: monospace;
        background: #f1f5f9;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .slide-content {
        white-space: pre-wrap;
        font-family: "Menlo", "Monaco", "Courier New", monospace;
        font-size: 0.95rem;
        color: #333;
        background: #fafafa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #eee;
    }

    /* Print Styles */
    @media print {
        body {
            background: white;
            padding: 0;
        }

        .container {
            max-width: 100%;
            width: 100%;
            margin: 0;
            padding: 20px;
        }

        .btn, .no-print {
            display: none;
        }

        .slide-card {
            box-shadow: none;
            border: 1px solid #ddd;
            break-inside: avoid;
            page-break-inside: avoid;
            margin-bottom: 30px;
        }

        .summary-section, .toc {
            box-shadow: none;
            border: 1px solid #ddd;
        }
    }
    """

    # HTML Header
    html_content = [
        f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Slide Summary Report</h1>
            <div class="meta">Generated from {len(slides)} slides</div>
            <button class="btn" onclick="window.print()">Print to PDF</button>
        </header>
        """
    ]

    # Executive Summary
    html_content.append("""
        <div class="summary-section">
            <h2>Executive Summary</h2>
            <p>Below is a compilation of key points extracted from the slide deck.</p>
            <ul>
    """)
    
    for slide in slides:
        html_content.append(f"<li><strong>{slide['title']}:</strong> {html.escape(slide['summary'])}</li>")
    
    html_content.append("""
            </ul>
        </div>
    """)

    # Table of Contents
    html_content.append("""
        <div class="toc no-print">
            <h3>Table of Contents</h3>
            <ul>
    """)
    
    for slide in slides:
        html_content.append(f"<li><a href='#{slide['id']}'>{slide['title']}</a></li>")
    
    html_content.append("""
            </ul>
        </div>
    """)

    # Slides
    for slide in slides:
        html_content.append(f"""
        <div id="{slide['id']}" class="slide-card">
            <div class="slide-header">
                <h2 class="slide-title">{slide['title']}</h2>
                <span class="slide-id">{slide['filename']}</span>
            </div>
            <div class="slide-content">{html.escape(slide['content'])}</div>
        </div>
        """)

    # Footer
    html_content.append("""
    </div>
</body>
</html>
    """)

    return "\n".join(html_content)

def main():
    # Detect directory
    if os.path.exists('slides'):
        target_dir = 'slides'
    else:
        target_dir = '.'
    
    print(f"Reading slides from: {target_dir}")
    
    slide_files = get_slide_files(target_dir)
    
    if not slide_files:
        print("No .txt files found.")
        return

    slides_data = []
    for f in slide_files:
        path = os.path.join(target_dir, f)
        slides_data.append(read_slide(path))
    
    report_html = generate_html(slides_data)
    
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(report_html)
    
    print(f"Successfully generated report.html with {len(slides_data)} slides.")

if __name__ == "__main__":
    main()