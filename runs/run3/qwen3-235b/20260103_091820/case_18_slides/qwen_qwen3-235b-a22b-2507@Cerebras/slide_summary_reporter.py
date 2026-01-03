import os
import re
from pathlib import Path

def read_slide_files(directory="."):
    """Read all .txt files in the directory and return sorted list of (filename, content)"""
    slides = []
    for file_path in Path(directory).glob("slide*.txt"):
        if file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            # Extract number from slide filename for sorting
            match = re.search(r'\d+', file_path.name)
            slide_num = int(match.group()) if match else 999
            slides.append((slide_num, file_path.name, content))
    
    # Sort by slide number
    slides.sort()
    return [(name, content) for _, name, content in slides]

def extract_summary_preview(content, max_lines=2):
    """Extract first few lines of content for summary"""
    lines = content.split('\n')
    preview_lines = [line.strip() for line in lines[:max_lines] if line.strip()]
    if len(lines) > max_lines:
        preview_lines.append("...")
    return " ".join(preview_lines)

def generate_html_report(slides, output_file="report.html"):
    """Generate a beautiful HTML report from slides"""
    
    # Generate table of contents
    toc_items = []
    summary_items = []
    
    for i, (filename, content) in enumerate(slides, 1):
        # Clean title for anchor
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', filename.replace('.txt', ''))
        toc_items.append(f'            <li><a href="#slide-{clean_title}">Slide {i}: {filename}</a></li>')
        
        # Add to summary
        preview = extract_summary_preview(content)
        summary_items.append(f"            <p><strong>Slide {i}:</strong> {preview}</p>")
    
    toc_html = "\n".join(toc_items)
    summary_html = "\n".join(summary_items)
    
    # Generate slide cards
    slide_cards = []
    for (filename, content) in slides:
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', filename.replace('.txt', ''))
        slide_content = content.replace('\n', '<br>')
        slide_cards.append(f"""
            <div class="slide-card" id="slide-{clean_title}">
                <h2>{filename}</h2>
                <div class="slide-content">
                    {slide_content}
                </div>
            </div>
        """)
    
    slide_cards_html = "\n".join(slide_cards)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        :root {{
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --light-bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #2c3e50;
            --text-muted: #6c757d;
            --border: #dee2e6;
            --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background-color: var(--light-bg);
            padding: 2rem;
        }}
        
        @media print {{
            body {{
                padding: 0.5cm;
                background: white;
            }}
            
            .no-print {{
                display: none !important;
            }}
            
            .slide-card {{
                page-break-inside: avoid;
                break-inside: avoid;
                margin-bottom: 1rem;
            }}
            
            h1, h2 {{
                break-after: avoid;
            }}
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
            position: relative;
        }}
        
        h1 {{
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-weight: 700;
            font-size: 2.5rem;
        }}
        
        .date {{
            color: var(--text-muted);
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }}
        
        .print-btn {{
            background-color: var(--secondary-color);
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            position: absolute;
            top: 2rem;
            right: 2rem;
        }}
        
        .print-btn:hover {{
            background-color: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .no-print {{
            position: sticky;
            top: 0;
            background: white;
            padding: 1rem 0;
            z-index: 100;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }}
        
        .sections {{
            display: flex;
            gap: 2rem;
        }}
        
        .section {{
            flex: 1;
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: var(--shadow);
        }}
        
        .section h2 {{
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--secondary-color);
            font-size: 1.8rem;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .toc li {{
            margin-bottom: 0.8rem;
            padding: 0.5rem;
            border-left: 3px solid var(--secondary-color);
            background-color: rgba(52, 152, 219, 0.05);
            transition: all 0.2s ease;
        }}
        
        .toc a {{
            text-decoration: none;
            color: var(--primary-color);
            font-weight: 500;
            font-size: 1.1rem;
            display: block;
            transition: all 0.2s ease;
        }}
        
        .toc a:hover {{
            color: var(--secondary-color);
            transform: translateX(5px);
        }}
        
        .summary p {{
            margin-bottom: 1rem;
            padding: 0.8rem;
            background-color: rgba(44, 62, 80, 0.03);
            border-radius: 6px;
            border-left: 3px solid var(--accent-color);
        }}
        
        .summary strong {{
            color: var(--accent-color);
        }}
        
        .slide-card {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
            padding: 2.5rem;
            margin-bottom: 2.5rem;
            transition: all 0.3s ease;
            border: 1px solid var(--border);
            page-break-after: always;
        }}
        
        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        }}
        
        .slide-card h2 {{
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            font-weight: 600;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--secondary-color);
        }}
        
        .slide-content {{
            color: var(--text);
            font-size: 1.1rem;
            line-height: 1.8;
        }}
        
        .slide-content p {{
            margin-bottom: 1rem;
        }}
        
        .slide-content ul, .slide-content ol {{
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        .slide-content li {{
            margin-bottom: 0.5rem;
        }}
        
        footer {{
            text-align: center;
            margin-top: 4rem;
            padding: 2rem 0;
            color: var(--text-muted);
            font-size: 1rem;
            border-top: 1px solid var(--border);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            .print-btn {{
                position: static;
                width: 100%;
                margin-bottom: 1rem;
            }}
            
            .sections {{
                flex-direction: column;
            }}
            
            header {{
                padding: 1.5rem 1rem;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .slide-card {{
                padding: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Slide Summary Report</h1>
            <p class="date">Generated on {os.times().elapsed_time if hasattr(os.times(), 'elapsed_time') else ''}</p>
            <button class="print-btn no-print" onclick="window.print()">🖨️ Print to PDF</button>
        </header>
        
        <div class="no-print">
            <div class="sections">
                <div class="section toc">
                    <h2>Table of Contents</h2>
                    <ul>
{toc_html}
                    </ul>
                </div>
                <div class="section summary">
                    <h2>Executive Summary</h2>
{summary_html}
                </div>
            </div>
        </div>
        
        <!-- Slide Cards -->
{slide_cards_html}
        
        <footer>
            <p>Slide Summary Report &copy; {os.times().elapsed_time if hasattr(os.times(), 'elapsed_time') else ''} | Generated from text files</p>
        </footer>
    </div>
    
    <script>
        // Add current date to the report
        document.querySelector('.date').textContent = "Generated on " + new Date().toLocaleDateString('en-US', {{
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }});
        
        // Update footer year
        document.querySelector('footer p').innerHTML = document.querySelector('footer p').innerHTML.replace(/\d{{4}}/, new Date().getFullYear());
    </script>
</body>
</html>'''
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generated: {output_file}")
    print(f"Total slides processed: {len(slides)}")

def main():
    """Main function to generate the report"""
    slides = read_slide_files(".")
    if not slides:
        print("No slide files found. Please ensure you have files named like 'slide1.txt', 'slide2.txt', etc.")
        return
    
    generate_html_report(slides)
    
if __name__ == "__main__":
    main()