import os
import re
from pathlib import Path

def natural_sort_key(s):
    """Sort strings containing numbers naturally (slide1, slide2, ..., slide10)"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def read_slides(directory):
    """Read all .txt files from directory and return sorted list of slides"""
    slides = []
    path = Path(directory)
    
    # Get all .txt files
    txt_files = sorted(path.glob('*.txt'), key=lambda x: natural_sort_key(x.name))
    
    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            slides.append({
                'filename': txt_file.name,
                'title': txt_file.stem.replace('_', ' ').title(),
                'content': content
            })
    
    return slides

def get_first_lines(content, num_lines=2):
    """Get first n lines from content"""
    lines = [line for line in content.split('\n') if line.strip()]
    return '\n'.join(lines[:num_lines])

def escape_html(text):
    """Escape HTML special characters"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

def generate_html(slides):
    """Generate HTML report from slides"""
    
    # Generate Table of Contents
    toc_html = ""
    for i, slide in enumerate(slides, 1):
        toc_html += f'        <li><a href="#slide-{i}">{escape_html(slide["title"])}</a></li>\n'
    
    # Generate Summary
    summary_html = ""
    for i, slide in enumerate(slides, 1):
        first_lines = get_first_lines(slide['content'], 2)
        summary_html += f'''
        <div class="summary-item">
            <strong>{escape_html(slide['title'])}:</strong>
            <div class="summary-content">{escape_html(first_lines)}</div>
        </div>
'''
    
    # Generate Slide Cards
    cards_html = ""
    for i, slide in enumerate(slides, 1):
        cards_html += f'''
    <div class="slide-card" id="slide-{i}">
        <div class="slide-header">
            <div class="slide-number">Slide {i}</div>
            <h2 class="slide-title">{escape_html(slide['title'])}</h2>
        </div>
        <div class="slide-content">
            <pre>{escape_html(slide['content'])}</pre>
        </div>
    </div>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* Premium Typography and Base Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --accent: #8b5cf6;
            --accent-dark: #7c3aed;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --text-light: #9ca3af;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --border: #e5e7eb;
            --border-light: #f3f4f6;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem 1rem;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-primary);
            border-radius: 20px;
            box-shadow: var(--shadow-2xl);
            overflow: hidden;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 2rem 3rem 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            letter-spacing: -0.03em;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header p {{
            font-size: 1.25rem;
            opacity: 0.95;
            font-weight: 300;
            letter-spacing: 0.01em;
        }}
        
        /* Action Bar */
        .action-bar {{
            background: var(--bg-secondary);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        .slide-count {{
            font-size: 0.9375rem;
            color: var(--text-secondary);
            font-weight: 600;
            letter-spacing: 0.01em;
        }}
        
        .slide-count span {{
            color: var(--primary);
            font-size: 1.125rem;
            font-weight: 700;
        }}
        
        .print-button {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            color: white;
            border: none;
            padding: 0.875rem 2rem;
            border-radius: 10px;
            font-size: 0.9375rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-md);
            letter-spacing: 0.01em;
        }}
        
        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}
        
        .print-button:active {{
            transform: translateY(0);
        }}
        
        /* Main Content */
        .content {{
            padding: 3rem 2rem;
        }}
        
        /* Section Styles */
        .section {{
            margin-bottom: 4rem;
        }}
        
        .section-title {{
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 2rem;
            color: var(--text-primary);
            letter-spacing: -0.02em;
            position: relative;
            padding-bottom: 1rem;
        }}
        
        .section-title::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 80px;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 2px;
        }}
        
        /* Table of Contents */
        .toc-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        
        .toc-list li {{
            background: var(--bg-secondary);
            border-radius: 12px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border-light);
        }}
        
        .toc-list li:hover {{
            background: white;
            transform: translateX(6px);
            box-shadow: var(--shadow-md);
            border-color: var(--primary-light);
        }}
        
        .toc-list a {{
            display: block;
            padding: 1rem 1.5rem;
            color: var(--primary);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9375rem;
            transition: color 0.2s;
        }}
        
        .toc-list a:hover {{
            color: var(--accent);
        }}
        
        /* Summary Section */
        .summary-item {{
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.25rem;
            border-left: 5px solid var(--primary);
            transition: all 0.3s;
        }}
        
        .summary-item:hover {{
            background: white;
            box-shadow: var(--shadow-md);
            transform: translateX(4px);
        }}
        
        .summary-item strong {{
            color: var(--primary);
            font-weight: 700;
            font-size: 1rem;
            display: block;
            margin-bottom: 0.75rem;
        }}
        
        .summary-content {{
            color: var(--text-secondary);
            font-size: 0.9375rem;
            line-height: 1.7;
            white-space: pre-wrap;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        }}
        
        /* Slide Cards */
        .slide-card {{
            background: white;
            border: 1px solid var(--border);
            border-radius: 16px;
            margin-bottom: 2.5rem;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .slide-card:hover {{
            box-shadow: var(--shadow-xl);
            transform: translateY(-4px);
        }}
        
        .slide-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 2.5rem;
            position: relative;
        }}
        
        .slide-header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 100%);
        }}
        
        .slide-number {{
            font-size: 0.8125rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }}
        
        .slide-title {{
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        
        .slide-content {{
            padding: 2.5rem;
            background: var(--bg-primary);
        }}
        
        .slide-content pre {{
            font-family: 'SF Mono', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
            font-size: 0.9375rem;
            line-height: 1.8;
            color: var(--text-primary);
            white-space: pre-wrap;
            word-wrap: break-word;
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid var(--border);
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            body {{
                padding: 1rem 0.5rem;
            }}
            
            .header {{
                padding: 2rem 1.5rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .header p {{
                font-size: 1rem;
            }}
            
            .content {{
                padding: 2rem 1.5rem;
            }}
            
            .toc-list {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Print Styles */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                border-radius: 0;
                max-width: 100%;
            }}
            
            .action-bar {{
                display: none !important;
            }}
            
            .print-button {{
                display: none !important;
            }}
            
            .header {{
                background: white !important;
                color: black !important;
                border-bottom: 3px solid black;
                padding: 2rem !important;
                page-break-after: always;
            }}
            
            .header::before {{
                display: none;
            }}
            
            .header h1,
            .header p {{
                color: black !important;
                text-shadow: none !important;
            }}
            
            .section {{
                page-break-inside: avoid;
            }}
            
            .section-title {{
                color: black !important;
            }}
            
            .section-title::after {{
                background: black !important;
            }}
            
            .slide-card {{
                page-break-inside: avoid;
                box-shadow: none !important;
                border: 2px solid #333 !important;
                margin-bottom: 2rem;
                transform: none !important;
            }}
            
            .slide-header {{
                background: #f0f0f0 !important;
                color: black !important;
                border-bottom: 2px solid #333;
            }}
            
            .slide-header::after {{
                display: none;
            }}
            
            .slide-number,
            .slide-title {{
                color: black !important;
                text-shadow: none !important;
            }}
            
            .slide-content {{
                background: white !important;
            }}
            
            .slide-content pre {{
                background: #f9f9f9 !important;
                border: 1px solid #ccc !important;
            }}
            
            .toc-list {{
                display: block;
            }}
            
            .toc-list li {{
                background: white !important;
                margin-bottom: 0.5rem;
                border: 1px solid #ddd !important;
                transform: none !important;
            }}
            
            .toc-list a {{
                color: black !important;
            }}
            
            .summary-item {{
                background: white !important;
                border-left-color: black !important;
                box-shadow: none !important;
                transform: none !important;
            }}
            
            .summary-item strong {{
                color: black !important;
            }}
            
            .summary-content {{
                color: #333 !important;
            }}
            
            /* Page breaks for better PDF layout */
            .section:not(:first-child) {{
                page-break-before: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>📊 Slide Summary Report</h1>
                <p>Comprehensive presentation analysis and overview</p>
            </div>
        </div>
        
        <div class="action-bar">
            <div class="slide-count">Total Slides: <span>{len(slides)}</span></div>
            <button class="print-button" onclick="window.print()">🖨️ Print to PDF</button>
        </div>
        
        <div class="content">
            <!-- Table of Contents -->
            <div class="section">
                <h2 class="section-title">📑 Table of Contents</h2>
                <ul class="toc-list">
{toc_html}
                </ul>
            </div>
            
            <!-- Summary Section -->
            <div class="section">
                <h2 class="section-title">📝 Executive Summary</h2>
{summary_html}
            </div>
            
            <!-- Slide Cards -->
            <div class="section">
                <h2 class="section-title">📄 Detailed Slides</h2>
{cards_html}
            </div>
        </div>
    </div>
</body>
</html>
'''
    
    return html

def main():
    import sys
    
    # Get directory from command line or use current directory
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    print(f"📂 Reading slides from: {directory}")
    
    # Read slides
    slides = read_slides(directory)
    
    if not slides:
        print("❌ No .txt files found in the directory!")
        print("   Please add some .txt files (e.g., slide1.txt, slide2.txt) and try again.")
        return
    
    print(f"✅ Found {len(slides)} slides")
    for slide in slides:
        print(f"   - {slide['filename']}")
    
    # Generate HTML
    print("\n🔨 Generating HTML report...")
    html = generate_html(slides)
    
    # Write to file
    output_file = 'report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_file}")
    print(f"📖 Open {output_file} in a browser and use the 'Print to PDF' button")

if __name__ == '__main__':
    main()