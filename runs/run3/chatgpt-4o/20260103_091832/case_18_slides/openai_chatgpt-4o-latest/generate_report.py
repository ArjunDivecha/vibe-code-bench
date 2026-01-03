import os
import html
from pathlib import Path

def read_slides(slide_dir):
    slides = []
    for filename in sorted(os.listdir(slide_dir)):
        if filename.endswith('.txt'):
            path = os.path.join(slide_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                slides.append({
                    'filename': filename,
                    'title': filename.replace('.txt', '').replace('_', ' ').title(),
                    'content': content
                })
    return slides

def generate_summary(slides, lines_per_slide=2):
    summary_lines = []
    for slide in slides:
        lines = slide['content'].splitlines()
        snippet = "\n".join(lines[:lines_per_slide])
        summary_lines.append(f"<strong>{slide['title']}</strong>: {html.escape(snippet)}")
    return "<br><br>\n".join(summary_lines)

def generate_toc(slides):
    toc_items = []
    for idx, slide in enumerate(slides):
        toc_items.append(f'<li><a href="#slide{idx+1}">{html.escape(slide["title"])}</a></li>')
    return "<ul>\n" + "\n".join(toc_items) + "\n</ul>"

def generate_slide_cards(slides):
    cards = []
    for idx, slide in enumerate(slides):
        content_html = "<br>".join(html.escape(slide['content']).splitlines())
        card = f"""
        <div class="card" id="slide{idx+1}">
            <h2>{html.escape(slide['title'])}</h2>
            <p>{content_html}</p>
        </div>
        """
        cards.append(card)
    return "\n".join(cards)

def generate_html(slides):
    summary_html = generate_summary(slides)
    toc_html = generate_toc(slides)
    cards_html = generate_slide_cards(slides)

    html_report = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Slide Summary Report</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #f9f9f9;
            color: #333;
            padding: 40px;
            max-width: 900px;
            margin: auto;
        }}
        h1, h2 {{
            color: #2c3e50;
        }}
        .summary, .toc {{
            background: #ffffff;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .card {{
            background: #ffffff;
            padding: 30px;
            margin-bottom: 40px;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            page-break-inside: avoid;
        }}
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        ul li {{
            margin-bottom: 10px;
        }}
        a {{
            color: #2980b9;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        #print-btn {{
            background: #27ae60;
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        #print-btn:hover {{
            background: #219150;
        }}
        @media print {{
            #print-btn {{
                display: none;
            }}
            body {{
                padding: 0;
                margin: 0;
            }}
            .card {{
                page-break-before: always;
            }}
        }}
    </style>
</head>
<body>
    <button id="print-btn" onclick="window.print()">Print to PDF</button>

    <div class="summary">
        <h1>Summary</h1>
        <p>{summary_html}</p>
    </div>

    <div class="toc">
        <h1>Table of Contents</h1>
        {toc_html}
    </div>

    {cards_html}
</body>
</html>
"""
    return html_report

def main():
    slide_dir = '.'
    slides = read_slides(slide_dir)
    if not slides:
        print("No slide .txt files found in the current directory.")
        return
    html_content = generate_html(slides)
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("report.html generated successfully.")

if __name__ == '__main__':
    main()