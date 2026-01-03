#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Creates a beautiful HTML dashboard with codebase statistics
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

class GitStatsGenerator:
    def __init__(self):
        self.file_counts = Counter()
        self.file_sizes = []
        self.line_counts = defaultdict(int)
        self.directory_depths = []
        self.largest_files = []
        self.total_files = 0
        self.total_lines = 0
        
    def scan_directory(self, path='.'):
        """Recursively scan directory and collect statistics"""
        for root, dirs, files in os.walk(path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            
            # Calculate directory depth
            depth = root.replace(os.getcwd(), '').count(os.sep)
            self.directory_depths.append(depth)
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    # Get file extension
                    ext = os.path.splitext(file)[1].lower() or 'no-extension'
                    self.file_counts[ext] += 1
                    self.total_files += 1
                    
                    # Get file size
                    size = os.path.getsize(file_path)
                    self.file_sizes.append(size)
                    
                    # Count lines in text files
                    if self.is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = sum(1 for line in f)
                                self.line_counts[ext] += lines
                                self.total_lines += lines
                                self.largest_files.append({
                                    'name': os.path.relpath(file_path),
                                    'lines': lines,
                                    'size': size
                                })
                        except:
                            pass
                            
                except (OSError, PermissionError):
                    continue
    
    def is_text_file(self, filepath):
        """Simple check if file is likely text-based"""
        text_extensions = {'.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.txt', '.yml', '.yaml', '.java', '.cpp', '.c', '.h', '.rs', '.go', '.ts', '.jsx', '.tsx', '.php', '.rb', '.swift', '.kt', '.scala', '.sh', '.sql', '.r', '.m', '.pl', '.lua', '.dart'}
        ext = os.path.splitext(filepath)[1].lower()
        return ext in text_extensions
    
    def generate_colors(self, count):
        """Generate vibrant colors for charts"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
            '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8B739', '#6C5CE7',
            '#A29BFE', '#FD79A8', '#FDCB6E', '#6C5CE7', '#00CEC9'
        ]
        return colors[:count]
    
    def create_pie_chart_svg(self, data, title):
        """Create SVG pie chart"""
        if not data:
            return ''
        
        total = sum(data.values())
        colors = self.generate_colors(len(data))
        
        svg = f'<svg viewBox="0 0 200 200" class="chart">'
        svg += '<circle cx="100" cy="100" r="80" fill="#1a1a1a"/>'
        
        current_angle = 0
        for i, (label, value) in enumerate(data.items()):
            percentage = (value / total) * 100
            angle = (value / total) * 360
            
            # Calculate path
            start_angle = current_angle
            end_angle = current_angle + angle
            
            x1 = 100 + 80 * cos(radians(start_angle))
            y1 = 100 + 80 * sin(radians(start_angle))
            x2 = 100 + 80 * cos(radians(end_angle))
            y2 = 100 + 80 * sin(radians(end_angle))
            
            large_arc = 1 if angle > 180 else 0
            
            path = f'M 100 100 L {x1} {y1} A 80 80 0 {large_arc} 1 {x2} {y2} Z'
            
            svg += f'<path d="{path}" fill="{colors[i % len(colors)]}" stroke="#2a2a2a" stroke-width="1"/>'
            
            # Add label
            label_angle = current_angle + angle / 2
            label_x = 100 + 100 * cos(radians(label_angle))
            label_y = 100 + 100 * sin(radians(label_angle))
            
            svg += f'<text x="{label_x}" y="{label_y}" text-anchor="middle" class="chart-label">{label}</text>'
            
            current_angle += angle
        
        svg += '</svg>'
        return svg
    
    def create_bar_chart_svg(self, data, title):
        """Create SVG bar chart for largest files"""
        if not data:
            return ''
        
        max_lines = max(file['lines'] for file in data)
        colors = self.generate_colors(len(data))
        
        svg = f'<svg viewBox="0 0 400 200" class="chart">'
        
        bar_width = 350 / len(data)
        for i, file_data in enumerate(data):
            height = (file_data['lines'] / max_lines) * 150
            x = 25 + i * bar_width
            y = 175 - height
            
            svg += f'<rect x="{x}" y="{y}" width="{bar_width - 5}" height="{height}" fill="{colors[i % len(colors)]}" class="bar"/>'
            
            # Add value label
            svg += f'<text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" class="bar-label">{file_data["lines"]}</text>'
        
        # Add axis
        svg += '<line x1="25" y1="175" x2="375" y2="175" stroke="#666" stroke-width="1"/>'
        svg += '<line x1="25" y1="25" x2="25" y2="175" stroke="#666" stroke-width="1"/>'
        
        svg += '</svg>'
        return svg
    
    def generate_html(self):
        """Generate the complete HTML infographic"""
        
        # Prepare data
        top_extensions = dict(self.file_counts.most_common(8))
        largest_files = sorted(self.largest_files, key=lambda x: x['lines'], reverse=True)[:8]
        
        # Calculate stats
        avg_file_size = sum(self.file_sizes) / len(self.file_sizes) if self.file_sizes else 0
        max_depth = max(self.directory_depths) if self.directory_depths else 0
        avg_depth = sum(self.directory_depths) / len(self.directory_depths) if self.directory_depths else 0
        
        # Generate charts
        pie_chart = self.create_pie_chart_svg(top_extensions, "File Types")
        bar_chart = self.create_bar_chart_svg(largest_files, "Largest Files")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
        }}
        
        .header h1 {{
            font-size: 3.5em;
            font-weight: 700;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(255, 107, 107, 0.3);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            color: #888;
            font-weight: 300;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s;
        }}
        
        .card:hover::before {{
            left: 100%;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        }}
        
        .card-title {{
            font-size: 1.4em;
            margin-bottom: 20px;
            color: #4ECDC4;
            font-weight: 600;
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #FF6B6B;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #aaa;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .chart-container {{
            text-align: center;
            margin-top: 20px;
        }}
        
        .chart {{
            width: 100%;
            max-width: 200px;
            height: 200px;
            filter: drop-shadow(0 0 10px rgba(255, 107, 107, 0.3));
        }}
        
        .chart-label {{
            font-size: 10px;
            fill: #fff;
            font-weight: 600;
        }}
        
        .bar-label {{
            font-size: 8px;
            fill: #4ECDC4;
            font-weight: 600;
        }}
        
        .file-list {{
            list-style: none;
            margin-top: 15px;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .file-item:last-child {{
            border-bottom: none;
        }}
        
        .file-name {{
            color: #ccc;
            font-size: 0.9em;
            flex: 1;
            margin-right: 10px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .file-lines {{
            color: #FFA07A;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .ext-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .ext-name {{
            color: #4ECDC4;
            font-weight: 600;
        }}
        
        .ext-count {{
            color: #FFA07A;
            font-weight: 600;
        }}
        
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .card {{
            animation: fadeInUp 0.6s ease forwards;
        }}
        
        .card:nth-child(1) {{ animation-delay: 0.1s; }}
        .card:nth-child(2) {{ animation-delay: 0.2s; }}
        .card:nth-child(3) {{ animation-delay: 0.3s; }}
        .card:nth-child(4) {{ animation-delay: 0.4s; }}
        .card:nth-child(5) {{ animation-delay: 0.5s; }}
        .card:nth-child(6) {{ animation-delay: 0.6s; }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Codebase Fingerprint</h1>
            <div class="subtitle">Comprehensive analysis of your repository</div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <div class="card-title">📊 Overview</div>
                <div class="stat-number">{self.total_files:,}</div>
                <div class="stat-label">Total Files</div>
                <div style="margin-top: 20px;">
                    <div class="stat-number" style="font-size: 1.8em;">{self.total_lines:,}</div>
                    <div class="stat-label">Total Lines of Code</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">📁 File Distribution</div>
                <div class="chart-container">
                    {pie_chart}
                </div>
                <div style="margin-top: 15px;">
                    {''.join(f'<div class="ext-item"><span class="ext-name">{ext}</span><span class="ext-count">{count}</span></div>' for ext, count in list(top_extensions.items())[:5])}
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">🏔️ Directory Structure</div>
                <div class="stat-number" style="font-size: 1.8em;">{max_depth}</div>
                <div class="stat-label">Max Directory Depth</div>
                <div style="margin-top: 15px;">
                    <div class="stat-number" style="font-size: 1.5em; color: #4ECDC4;">{avg_depth:.1f}</div>
                    <div class="stat-label">Average Depth</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="stat-number" style="font-size: 1.5em; color: #FFA07A;">{len([d for d in self.directory_depths if d == 0])}</div>
                    <div class="stat-label">Root Level Files</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">📈 Largest Files</div>
                <div class="chart-container">
                    {bar_chart}
                </div>
                <ul class="file-list">
                    {''.join(f'<li class="file-item"><span class="file-name">{file["name"]}</span><span class="file-lines">{file["lines"]} lines</span></li>' for file in largest_files[:5])}
                </ul>
            </div>
            
            <div class="card">
                <div class="card-title">🎯 Code Quality Snapshot</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <div class="stat-number" style="font-size: 1.8em;">{avg_file_size / 1024:.1f}KB</div>
                        <div class="stat-label">Avg File Size</div>
                    </div>
                    <div>
                        <div class="stat-number" style="font-size: 1.8em;">{self.total_lines / self.total_files:.0f}</div>
                        <div class="stat-label">Avg Lines/File</div>
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <div style="background: rgba(78, 205, 196, 0.2); padding: 15px; border-radius: 10px;">
                        <div style="color: #4ECDC4; font-weight: 600; margin-bottom: 5px;">Top Language</div>
                        <div style="color: #fff; font-size: 1.1em;">{self.file_counts.most_common(1)[0][0] if self.file_counts else 'N/A'} ({self.file_counts.most_common(1)[0][1] if self.file_counts else 0} files)</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">🚀 Quick Insights</div>
                <div style="space-y: 15px;">
                    <div style="padding: 10px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <div style="color: #4ECDC4; font-size: 0.9em;">Most Common Extension</div>
                        <div style="color: #fff; font-weight: 600;">{self.file_counts.most_common(1)[0][0] if self.file_counts else 'N/A'}</div>
                    </div>
                    <div style="padding: 10px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <div style="color: #FFA07A; font-size: 0.9em;">Largest File</div>
                        <div style="color: #fff; font-weight: 600; font-size: 0.9em;">{largest_files[0]["name"] if largest_files else "N/A"}</div>
                    </div>
                    <div style="padding: 10px 0;">
                        <div style="color: #98D8C8; font-size: 0.9em;">Generated</div>
                        <div style="color: #fff; font-weight: 600;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
    
    <script>
        // Add some interactive magic
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.card');
            
            cards.forEach((card, index) => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.transform = 'translateY(-8px) scale(1.02)';
                }});
                
                card.addEventListener('mouseleave', function() {{
                    this.style.transform = 'translateY(0) scale(1)';
                }});
            }});
            
            // Animate numbers on load
            const numbers = document.querySelectorAll('.stat-number');
            numbers.forEach(num => {{
                const finalValue = parseInt(num.textContent.replace(/,/g, ''));
                if (!isNaN(finalValue)) {{
                    let currentValue = 0;
                    const increment = finalValue / 50;
                    const timer = setInterval(() => {{
                        currentValue += increment;
                        if (currentValue >= finalValue) {{
                            currentValue = finalValue;
                            clearInterval(timer);
                        }}
                        num.textContent = Math.floor(currentValue).toLocaleString();
                    }}, 20);
                }}
            }});
        }});
    </script>
</body>
</html>'''
        
        return html
    
    def run(self):
        """Main execution method"""
        print("🔍 Scanning directory...")
        self.scan_directory()
        
        print("📊 Generating infographic...")
        html_content = self.generate_html()
        
        with open('stats.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ Infographic generated: stats.html")
        print("🌐 Open stats.html in your browser to view the dashboard!")

if __name__ == "__main__":
    # Import math functions for SVG calculations
    from math import cos, sin, radians
    
    generator = GitStatsGenerator()
    generator.run()