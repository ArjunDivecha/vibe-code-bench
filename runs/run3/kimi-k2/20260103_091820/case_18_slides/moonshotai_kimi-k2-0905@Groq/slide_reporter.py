#!/usr/bin/env python3
"""
Slide Summary Reporter
Converts text files representing PowerPoint slides into a beautiful HTML report
"""

import os
import re
from pathlib import Path
from datetime import datetime


def read_slide_files(directory="."):
    """Read all .txt files from the directory, sorted alphabetically"""
    slides = []
    txt_files = sorted([f for f in os.listdir(directory) if f.endswith('.txt')])
    
    for filename in txt_files:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Extract title (first line) and body (rest of content)
            lines = content.split('\n')
            title = lines[0].strip() if lines else filename.replace('.txt', '')
            body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
            
            slides.append({
                'filename': filename,
                'title': title,
                'body': body,
                'content': content
            })
    
    return slides


def generate_summary(slides, max_lines=2):
    """Generate a summary from the first few lines of each slide"""
    summary_lines = []
    
    for slide in slides:
        lines = slide['content'].split('\n')
        # Take first max_lines from each slide
        for line in lines[:max_lines]:
            if line.strip():
                summary_lines.append(line.strip())
    
    return summary_lines


def create_html_report(slides, output_file="report.html"):
    """Generate the beautiful HTML report"""
    
    # Generate summary
    summary_lines = generate_summary(slides)
    
    # HTML Template with premium CSS
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide Summary Report</title>
    <style>
        /* Reset and Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #2d3748;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        /* Container */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: drift 20s linear infinite;
        }
        
        @keyframes drift {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }
        
        /* Print Button */
        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4c51bf;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .print-button:hover {
            background: #434190;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        /* Navigation */
        .nav {
            background: #f7fafc;
            padding: 30px 40px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .nav h2 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #4a5568;
        }
        
        .toc {
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .toc li {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .toc li:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .toc a {
            display: block;
            padding: 15px 20px;
            text-decoration: none;
            color: #4a5568;
            font-weight: 500;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .toc a:hover {
            color: #667eea;
            background: #f7fafc;
        }
        
        /* Summary Section */
        .summary {
            padding: 40px;
            background: #f7fafc;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .summary h2 {
            font-size: 2rem;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .summary-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }
        
        .summary-item {
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
            font-size: 1.1rem;
            color: #4a5568;
        }
        
        .summary-item:last-child {
            border-bottom: none;
        }
        
        /* Slides Section */
        .slides {
            padding: 40px;
        }
        
        .slides h2 {
            font-size: 2rem;
            margin-bottom: 30px;
            color: #2d3748;
            text-align: center;
        }
        
        .slide-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .slide-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }
        
        .slide-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
            position: relative;
        }
        
        .slide-number {
            position: absolute;
            top: 20px;
            right: 30px;
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .slide-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0;
            padding-right: 60px;
        }
        
        .slide-body {
            padding: 30px;
            font-size: 1.1rem;
            line-height: 1.8;
            color: #4a5568;
        }
        
        .slide-body p {
            margin-bottom: 15px;
        }
        
        .slide-body p:last-child {
            margin-bottom: 0;
        }
        
        /* Footer */
        .footer {
            background: #2d3748;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 0.9rem;
        }
        
        /* Print Styles */
        @media print {
            body {
                background: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                border-radius: 0;
            }
            
            .print-button {
                display: none;
            }
            
            .slide-card {
                page-break-inside: avoid;
                margin-bottom: 20px;
            }
            
            .summary, .nav, .slides {
                page-break-inside: avoid;
            }
            
            .header {
                background: #2d3748 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            .slide-header {
                background: #4a5568 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .header {
                padding: 40px 20px;
            }
            
            .nav, .summary, .slides {
                padding: 20px;
            }
            
            .toc {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">📄 Print to PDF</button>
    
    <div class="container">
        <header class="header">
            <h1>Slide Summary Report</h1>
            <p class="subtitle">Generated on {date}</p>
        </header>
        
        <nav class="nav">
            <h2>Table of Contents</h2>
            <ul class="toc">
                {toc_items}
            </ul>
        </nav>
        
        <section class="summary">
            <h2>Executive Summary</h2>
            <div class="summary-content">
                {summary_items}
            </div>
        </section>
        
        <section class="slides">
            <h2>Slide Details</h2>
            {slide_cards}
        </section>
        
        <footer class="footer">
            <p>Generated by Slide Summary Reporter • {slides_count} slides processed</p>
        </footer>
    </div>
</body>
</html>"""
    
    # Generate TOC items
    toc_items = []
    for i, slide in enumerate(slides, 1):
        toc_items.append(f'<li><a href="#slide-{i}">{slide["title"]}</a></li>')
    
    # Generate summary items
    summary_items = []
    for line in summary_lines:
        summary_items.append(f'<div class="summary-item">• {line}</div>')
    
    # Generate slide cards
    slide_cards = []
    for i, slide in enumerate(slides, 1):
        # Format body content - preserve paragraphs
        body_content = slide['body'].replace('\n\n', '</p><p>').replace('\n', '<br>')
        if body_content:
            body_content = f'<p>{body_content}</p>'
        
        slide_card = f"""
        <div class="slide-card" id="slide-{i}">
            <div class="slide-header">
                <div class="slide-number">Slide {i}</div>
                <h3 class="slide-title">{slide['title']}</h3>
            </div>
            <div class="slide-body">
                {body_content}
            </div>
        </div>"""
        slide_cards.append(slide_card)
    
    # Fill in the template
    html_content = html_template.format(
        date=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        toc_items='\n'.join(toc_items),
        summary_items='\n'.join(summary_items),
        slide_cards='\n'.join(slide_cards),
        slides_count=len(slides)
    )
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Report generated: {output_file}")
    return output_file


def main():
    """Main function to run the slide reporter"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert text files representing PowerPoint slides into a beautiful HTML report'
    )
    parser.add_argument(
        '-d', '--directory',
        default='.',
        help='Directory containing slide text files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output',
        default='report.html',
        help='Output HTML file name (default: report.html)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Scanning for slide files...")
    slides = read_slide_files(args.directory)
    
    if not slides:
        print("❌ No .txt files found in the specified directory.")
        return 1
    
    print(f"📊 Found {len(slides)} slide files")
    print("🎨 Generating beautiful HTML report...")
    
    create_html_report(slides, args.output)
    
    print("🎉 Done! Open the generated HTML file in your browser.")
    return 0


if __name__ == "__main__":
    exit(main())