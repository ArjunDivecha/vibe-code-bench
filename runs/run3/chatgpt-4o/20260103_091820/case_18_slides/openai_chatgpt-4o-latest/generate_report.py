import os
import sys
import html
from pathlib import Path

def read_slide_files(directory):
    slide_files = sorted(
        [f for f in os.listdir(directory) if f.startswith("slide") and f.endswith(".txt")],
        key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
    )
    slides = []
    for filename in slide_files:
        path = os.path.join(directory, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            slides.append((filename, content))
    return slides

def extract_summary(slides, lines_per_slide=2):
    summary_lines = []
    for _, content in slides:
        lines = content.strip().splitlines()[:lines_per_slide]
        summary_lines.extend(lines)
    return summary_lines

def generate_html(slides, summary_lines):
    html_slides = []
    toc_entries = []

    for i, (filename, content) in enumerate(slides, start=1):
        slide_id = f"slide{i}"
        title = f"Slide {i}"
        toc_entries.append(f'<li><a href="#{slide_id}">{title}</a></li>')
        slide_html = f"""
        <div class="card" id="{slide_id}">
            <h2>{title}</h2>
            <pre>{html.escape(content.strip())}</pre>
        </div>
        """
        html_slides.append(slide_html)

    html_summary = "<br>".join(html.escape(line) for line in summary_lines)

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Slide Summary Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f9f9f9;
            color: #333;
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 0.2em;
        }}
        h2 {{
            font-size: 1.5em;
            margin-top: 0;
        }}
        .summary {{
            background: #fff;
            padding: 20px;
            margin-bottom: 40px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            border-left: 5px solid #4CAF50;
        }}
        .toc {{
            background: #fff;
            padding: 20px;
            margin-bottom: 40px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            border-left: 5px solid #2196F3;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 5px 0;
        }}
        .toc a {{
            text-decoration: none;
            color: #2196F3;
        }}
        .card {{
            background: #fff;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            page-break-inside: avoid;
        }}
        pre {{
            white-space: pre-wrap;
            font-family: 'Courier New', Courier, monospace;
            background: #f4f4f4;
            padding: 15px;
            border-radius: 4px;
        }}
        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 1em;
            border-radius: 5px;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }}
        @media print {{
            .print-button {{
                display: none;
            }}
            body {{
                margin: 10mm;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">Print to PDF</button>
    <h1>Slide Summary Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>{html_summary}</p>
    </div>
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            {''.join(toc_entries)}
        </ul>
    </div>
    {''.join(html_slides)}
</body>
</html>
    """
    return html_content

def main():
    input_dir = "."
    slides = read_slide_files(input_dir)
    if not slides:
        print("No slide .txt files found in the current directory.")
        sys.exit(1)
    summary_lines = extract_summary(slides)
    html_report = generate_html(slides, summary_lines)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    print("report.html generated successfully.")

if __name__ == "__main__":
    main()