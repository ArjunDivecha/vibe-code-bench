import os
import sys
import html
from pathlib import Path

def collect_slides(directory):
    slides = []
    for filename in sorted(os.listdir(directory)):
        if filename.lower().endswith(".txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                title = os.path.splitext(filename)[0]
                slides.append({
                    'filename': filename,
                    'title': title,
                    'content': content
                })
    return slides

def generate_summary(slides, lines_per_slide=2):
    summary_lines = []
    for slide in slides:
        lines = slide['content'].splitlines()
        summary = "\n".join(lines[:lines_per_slide])
        summary_lines.append(f"<strong>{html.escape(slide['title'])}:</strong> {html.escape(summary)}")
    return "<br>\n".join(summary_lines)

def generate_table_of_contents(slides):
    toc = '<ul class="toc">'
    for i, slide in enumerate(slides, start=1):
        toc += f'<li><a href="#slide{i}">{html.escape(slide["title"])}</a></li>'
    toc += '</ul>'
    return toc

def generate_slide_cards(slides):
    cards = ''
    for i, slide in enumerate(slides, start=1):
        content_html = "<br>\n".join(html.escape(line) for line in slide['content'].splitlines())
        cards += f'''
        <div class="card" id="slide{i}">
            <h2>{html.escape(slide["title"])}</h2>
            <div class="card-content">{content_html}</div>
        </div>
        '''
    return cards

def generate_html(slides):
    summary_html = generate_summary(slides)
    toc_html = generate_table_of_contents(slides)
    cards_html = generate_slide_cards(slides)

    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Slide Summary Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2rem;
            background: #f9f9f9;
            color: #333;
        }}
        h1 {{
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        .summary {{
            background: #fff;
            padding: 1rem 2rem;
            margin: 2rem auto;
            max-width: 800px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border-left: 6px solid #4CAF50;
        }}
        .toc {{
            max-width: 800px;
            margin: 0 auto 2rem auto;
            padding: 1rem 2rem;
            background: #fff;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }}
        .toc li {{
            margin: 0.5rem 0;
        }}
        .toc a {{
            color: #007BFF;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .card {{
            background: #fff;
            margin: 2rem auto;
            padding: 2rem;
            max-width: 800px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
            border-radius: 8px;
            page-break-inside: avoid;
        }}
        .card h2 {{
            margin-top: 0;
            border-bottom: 2px solid #eee;
            padding-bottom: 0.5rem;
        }}
        .card-content {{
            margin-top: 1rem;
            line-height: 1.6;
        }}
        .print-button {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: #4CAF50;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            cursor: pointer;
        }}
        .print-button:hover {{
            background: #45a049;
        }}
        @media print {{
            .print-button {{
                display: none;
            }}
            body {{
                background: white;
                padding: 0;
            }}
            .card {{
                box-shadow: none;
                border: none;
                margin: 0 0 2rem 0;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">Print to PDF</button>
    <h1>Slide Summary Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>{summary_html}</p>
    </div>
    <div class="toc">
        <h2>Table of Contents</h2>
        {toc_html}
    </div>
    {cards_html}
</body>
</html>
    '''
    return html_content

def main():
    if len(sys.argv) < 2:
        print("Usage: python slide_reporter.py <slides_directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        sys.exit(1)

    slides = collect_slides(directory)
    if not slides:
        print("No .txt slide files found in the directory.")
        sys.exit(1)

    html_output = generate_html(slides)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("report.html has been created successfully.")

if __name__ == "__main__":
    main()