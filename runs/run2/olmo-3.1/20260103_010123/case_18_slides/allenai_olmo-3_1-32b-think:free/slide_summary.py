import os
import glob

def get_sort_key(filename):
    if filename.lower().startswith('slide'):
        suffix = filename[len('slide'):].split('.')[0]
        try:
            return int(suffix)
        except ValueError:
            return float('inf')
    else:
        return float('inf')

css_code = """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
}

h1 {
    text-align: center;
    color: #2c3e50;
    padding-top: 30px;
}

.summary {
    margin-bottom: 30px;
}

.summary h2 {
    text-align: center;
    color: #2c3e50;
    padding-bottom: 15px;
}

.summary-content {
    font-size: 1.1em;
    line-height: 1.5;
    margin-bottom: 20px;
    max-width: 90%;
    margin-left: auto;
    margin-right: auto;
}

.toc {
    margin-bottom: 30px;
}

.toc h2 {
    text-align: center;
    color: #2c3e50;
    padding-bottom: 15px;
}

.toc-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.toc-list li {
    margin-bottom: 10px;
    padding: 10px;
    background: #e9e9e9;
    border-radius: 4px;
    cursor: pointer;
}

.toc-list li a {
    color: #2c3e50;
    text-decoration: none;
    display: block;
    padding: 8px;
}

.slides-container {
    margin-top: 20px;
}

.slide-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
    max-width: 90%;
    text-align: left;
    border: 1px solid #ddd;
    page-break-after: always;
}

.slide-card h2 {
    color: #333;
    margin-bottom: 10px;
    text-align: center;
}

.slide-card p {
    line-height: 1.5;
    font-size: 1em;
    margin: 0;
}

button {
    background: #4CAF50;
    color: white;
    border: none;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
}

button:hover {
    background: #45a049;
}

@media print {
    body {
        font-size: 12pt;
        background-color: white;
    }
    .slide-card {
        background: white;
        box-shadow: none;
        border: none;
    }
    button {
        display: none;
    }
}
"""

files = glob.glob('*.txt')
files_sorted = sorted(files, key=get_sort_key)

slides_data = []

for filepath in files_sorted:
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.splitlines()
        title = ""
        for line in lines:
            stripped = line.strip()
            if stripped:
                title = stripped
                break
        if not title:
            basename = os.path.splitext(os.path.basename(filepath))[0]
            title = basename.replace('_', ' ').title()
        
        snippet_lines = []
        for line in lines[:2]:
            stripped = line.strip()
            if stripped:
                snippet_lines.append(stripped)
        summary_snippet = ' | '.join(snippet_lines) if snippet_lines else "No content"
        
        slides_data.append({
            'filepath': filepath,
            'title': title,
            'content': content,
            'summary_snippet': summary_snippet,
        })

html_parts = []
html_parts.append('<!DOCTYPE html>')
html_parts.append('<html>')
html_parts.append('<head>')
html_parts.append('<title>Slide Summary Report</title>')
html_parts.append('<style>')
html_parts.append(css_code)
html_parts.append('</style>')
html_parts.append('</head>')
html_parts.append('<body>')

html_parts.append('<h1>Slide Summary Report</h1>')

if slides_data:
    all_summaries = [slide['summary_snippet'] for slide in slides_data]
    summary_text = ' | '.join(all_summaries)
else:
    summary_text = "No slides found"

html_parts.append('<section class="summary">')
html_parts.append('<h2>Summary</h2>')
html_parts.append(f'<div class="summary-content">{summary_text}</div>')
html_parts.append('</section>')

html_parts.append('<section class="toc">')
html_parts.append('<h2>Table of Contents</h2>')
html_parts.append('<ul class="toc-list">')
for idx, slide in enumerate(slides_data, 1):
    title = slide['title']
    safe_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    html_parts.append(f'<li><a href="#slide-{idx}">{safe_title}</a></li>')
html_parts.append('</ul>')
html_parts.append('</section>')

html_parts.append('<div class="slides-container">')
for idx, slide in enumerate(slides_data, 1):
    title = slide['title']
    content = slide['content']
    safe_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    paragraphs = safe_content.split('\n\n')
    html_parts.append(f'<div id="slide-{idx}" class="slide-card">')
    html_parts.append(f'<h2>{title}</h2>')
    for para in paragraphs:
        stripped_para = para.strip()
        if stripped_para:
            html_parts.append(f'<p>{stripped_para}</p>')
    html_parts.append('</div>')
html_parts.append('</div>')

html_parts.append('<button onclick="window.print();">Print to PDF</button>')

html_parts.append('</body>')
html_parts.append('</html>')

with open('report.html', 'w') as f:
    f.write('\n'.join(html_parts))