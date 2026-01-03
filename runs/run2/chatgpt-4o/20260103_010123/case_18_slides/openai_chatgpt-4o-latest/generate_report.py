import os
import html
import sys

def get_slide_files(directory):
    return sorted(
        [f for f in os.listdir(directory) if f.endswith(".txt")],
        key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
    )

def extract_summary_from_slide(content, lines=2):
    return '\n'.join(content.strip().splitlines()[:lines])

def generate_html(slide_contents, summaries):
    toc_items = []
    slide_cards = []
    
    for idx, content in enumerate(slide_contents, 1):
        slide_id = f"slide{idx}"
        toc_items.append(f'<li><a href="#{slide_id}">Slide {idx}</a></li>')
        slide_html = f'''
        <div class="card" id="{slide_id}">
            <h2>Slide {idx}</h2>
            <pre>{html.escape(content.strip())}</pre>
        </div>
        '''
        slide_cards.append(slide_html)
    
    summary_section = '<br>'.join(f'<strong>Slide {i+1}:</strong> {html.escape(s)}' for i, s in enumerate(summaries))
    
    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Slide Summary Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f9f9f9;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .summary {{
            background: #ffffff;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            border-radius: 8px;
        }}
        .toc {{
            background: #ffffff;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            border-radius: 8px;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 8px 0;
        }}
        .toc a {{
            text-decoration: none;
            color: #2980b9;
        }}
        .card {{
            background: #ffffff;
            padding: 20px;
            margin-bottom: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border-radius: 8px;
            page-break-inside: avoid;
        }}
        pre {{
            white-space: pre-wrap;
            font-family: inherit;
            font-size: 1rem;
        }}
        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
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
        <p>{summary_section}</p>
    </div>

    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            {''.join(toc_items)}
        </ul>
    </div>

    {''.join(slide_cards)}

</body>
</html>
    '''
    return html_content

def main():
    directory = os.getcwd()
    slide_files = get_slide_files(directory)
    
    slide_contents = []
    summaries = []
    
    for fname in slide_files:
        with open(os.path.join(directory, fname), 'r', encoding='utf-8') as f:
            content = f.read()
            slide_contents.append(content)
            summaries.append(extract_summary_from_slide(content, lines=2))
    
    html_report = generate_html(slide_contents, summaries)
    
    with open(os.path.join(directory, 'report.html'), 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print("report.html generated successfully.")

if __name__ == "__main__":
    main()