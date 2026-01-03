import os
import re
from datetime import datetime

def read_slide_files(directory):
    """Read all .txt files in the directory and return list of slide content."""
    slides = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                slides.append({
                    'filename': filename,
                    'title': content.split('\n')[0].strip(),
                    'content': content,
                    'summary': '\n'.join(content.split('\n')[:3]).strip()
                })
    return slides

def generate_html_report(slides, output_file='report.html'):
    """Generate beautiful HTML report from slides."""
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #f8f9fa;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header .date {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .print-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .print-btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }
        
        .toc {
            background: #f8f9fa;
            padding: 30px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .toc h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 400;
        }
        
        .toc ul {
            list-style: none;
            columns: 2;
            column-gap: 40px;
        }
        
        .toc li {
            margin-bottom: 12px;
            break-inside: avoid;
        }
        
        .toc a {
            color: #3498db;
            text-decoration: none;
            font-size: 1.1em;
            transition: color 0.3s ease;
            display: block;
            padding: 8px 0;
        }
        
        .toc a:hover {
            color: #2980b9;
            text-decoration: underline;
        }
        
        .summary {
            padding: 40px;
            background: white;
            border-bottom: 1px solid #e9ecef;
        }
        
        .summary h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 400;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .summary-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .summary-item h4 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .summary-item p {
            color: #6c757d;
            font-size: 0.95em;
            line-height: 1.5;
        }
        
        .slides-container {
            padding: 40px;
        }
        
        .slide-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            margin-bottom: 30px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            page-break-inside: avoid;
        }
        
        .slide-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }
        
        .slide-header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px 30px;
        }
        
        .slide-header h3 {
            font-size: 1.4em;
            font-weight: 400;
            margin-bottom: 5px;
        }
        
        .slide-header .filename {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .slide-content {
            padding: 30px;
            font-size: 1.1em;
            line-height: 1.8;
            white-space: pre-wrap;
            color: #495057;
        }
        
        .slide-content h1, .slide-content h2, .slide-content h3 {
            margin-top: 20px;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .slide-content ul, .slide-content ol {
            margin-left: 20px;
            margin-bottom: 15px;
        }
        
        .slide-content li {
            margin-bottom: 8px;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9em;
        }
        
        @media print {
            body {
                background: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                border-radius: 0;
            }
            
            .print-btn {
                display: none;
            }
            
            .slide-card {
                page-break-inside: avoid;
                margin-bottom: 20px;
                box-shadow: none;
                border: 1px solid #dee2e6;
            }
            
            .slide-card:hover {
                transform: none;
            }
            
            .toc ul {
                columns: 1;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 30px 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .toc {
                padding: 20px;
            }
            
            .toc ul {
                columns: 1;
            }
            
            .summary, .slides-container {
                padding: 20px;
            }
            
            .slide-content {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Print to PDF</button>
    
    <div class="container">
        <div class="header">
            <h1>Slide Summary Report</h1>
            <div class="date">Generated on {date}</div>
        </div>
        
        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>
                {toc_items}
            </ul>
        </div>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <p>This report summarizes {slide_count} presentation slides, providing key insights and an overview of the content covered.</p>
            <div class="summary-grid">
                {summary_items}
            </div>
        </div>
        
        <div class="slides-container">
            {slide_cards}
        </div>
        
        <div class="footer">
            <p>Generated by Slide Summary Reporter • {date}</p>
        </div>
    </div>
</body>
</html>"""

    # Generate content
    date_str = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    # Table of contents
    toc_items = []
    for i, slide in enumerate(slides):
        anchor = f"slide-{i+1}"
        toc_items.append(f'<li><a href="#{anchor}">{slide["title"]}</a></li>')
    
    # Summary items
    summary_items = []
    for slide in slides[:6]:  # Show first 6 slides in summary
        summary_items.append(f"""
        <div class="summary-item">
            <h4>{slide['title']}</h4>
            <p>{slide['summary']}</p>
        </div>
        """)
    
    # Slide cards
    slide_cards = []
    for i, slide in enumerate(slides):
        anchor = f"slide-{i+1}"
        slide_cards.append(f"""
        <div class="slide-card" id="{anchor}">
            <div class="slide-header">
                <h3>{slide['title']}</h3>
                <div class="filename">{slide['filename']}</div>
            </div>
            <div class="slide-content">{slide['content']}</div>
        </div>
        """)
    
    # Fill template
    html_content = html_template.format(
        date=date_str,
        toc_items='\n                '.join(toc_items),
        slide_count=len(slides),
        summary_items='\n                '.join(summary_items),
        slide_cards='\n            '.join(slide_cards)
    )
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

def main():
    """Main function to generate slide summary report."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate beautiful HTML report from slide text files')
    parser.add_argument('--directory', '-d', default='.', help='Directory containing slide .txt files (default: current directory)')
    parser.add_argument('--output', '-o', default='report.html', help='Output HTML file name (default: report.html)')
    
    args = parser.parse_args()
    
    try:
        print(f"Reading slide files from: {args.directory}")
        slides = read_slide_files(args.directory)
        
        if not slides:
            print("No .txt slide files found in the directory!")
            return
        
        print(f"Found {len(slides)} slide files")
        
        print(f"Generating HTML report: {args.output}")
        output_file = generate_html_report(slides, args.output)
        
        print(f"✅ Report generated successfully: {output_file}")
        print("Open the file in your browser to view the report")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")

if __name__ == '__main__':
    main()