#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Creates a beautiful HTML dashboard showing code statistics
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

class GitStatsGenerator:
    def __init__(self):
        self.file_stats = defaultdict(int)
        self.line_counts = defaultdict(int)
        self.file_sizes = []
        self.directory_depths = []
        self.total_files = 0
        self.total_lines = 0
        self.total_size = 0
        
    def scan_directory(self, path='.'):
        """Recursively scan directory and collect statistics"""
        for root, dirs, files in os.walk(path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            
            # Calculate directory depth
            depth = root.replace(path, '').count(os.sep)
            self.directory_depths.append(depth)
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip hidden files and common ignore patterns
                if file.startswith('.') or file in ['package-lock.json', 'yarn.lock']:
                    continue
                    
                try:
                    # Get file extension
                    ext = os.path.splitext(file)[1].lower()
                    if not ext:
                        ext = 'no-extension'
                    
                    self.file_stats[ext] += 1
                    self.total_files += 1
                    
                    # Count lines in file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        self.line_counts[ext] += lines
                        self.total_lines += lines
                    
                    # Get file size
                    size = os.path.getsize(file_path)
                    self.file_sizes.append((file_path, size, ext))
                    self.total_size += size
                    
                except (OSError, UnicodeDecodeError):
                    continue
    
    def get_top_extensions(self, n=8):
        """Get top N file extensions by count"""
        return dict(sorted(self.file_stats.items(), key=lambda x: x[1], reverse=True)[:n])
    
    def get_top_files(self, n=10):
        """Get top N largest files"""
        return sorted(self.file_sizes, key=lambda x: x[1], reverse=True)[:n]
    
    def get_directory_stats(self):
        """Get directory depth statistics"""
        if not self.directory_depths:
            return {'max': 0, 'avg': 0}
        return {
            'max': max(self.directory_depths),
            'avg': sum(self.directory_depths) / len(self.directory_depths)
        }
    
    def format_size(self, size_bytes):
        """Format size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def generate_pie_chart_svg(self, data, width=300, height=300):
        """Generate SVG pie chart for file extensions"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]
        
        total = sum(data.values())
        angles = []
        current_angle = 0
        
        for value in data.values():
            angle = (value / total) * 360
            angles.append((current_angle, current_angle + angle))
            current_angle += angle
        
        svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        cx, cy = width // 2, height // 2
        radius = min(width, height) // 2 - 20
        
        # Draw pie slices
        for i, (start_angle, end_angle) in enumerate(angles):
            start_rad = (start_angle - 90) * 3.14159 / 180
            end_rad = (end_angle - 90) * 3.14159 / 180
            
            x1 = cx + radius * 0.7 * (start_rad + end_rad) / 2
            y1 = cy + radius * 0.7 * (start_rad + end_rad) / 2
            
            large_arc = 1 if end_angle - start_angle > 180 else 0
            
            x1_outer = cx + radius * (start_rad + end_rad) / 2
            y1_outer = cy + radius * (start_rad + end_rad) / 2
            
            path = f'M {cx} {cy} L {cx + radius * (start_rad + end_rad) / 2} {cy + radius * (start_rad + end_rad) / 2} A {radius} {radius} 0 {large_arc} 1 {cx + radius * (start_rad + end_rad) / 2} {cy + radius * (start_rad + end_rad) / 2} Z'
            
            # Simplified pie slice
            start_x = cx + radius * (start_rad + end_rad) / 2
            start_y = cy + radius * (start_rad + end_rad) / 2
            
            path = f'M {cx} {cy} L {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {start_x} {start_y} Z'
            
            # More accurate pie slice
            start_x = cx + radius * (start_rad + end_rad) / 2
            start_y = cy + radius * (start_rad + end_rad) / 2
            
            # Calculate points more accurately
            start_x = cx + radius * (start_angle - 90) * 3.14159 / 180
            start_y = cy + radius * (start_angle - 90) * 3.14159 / 180
            
            # Actually, let's use a simpler approach
            start_rad = (start_angle - 90) * 3.14159 / 180
            end_rad = (end_angle - 90) * 3.14159 / 180
            
            start_x = cx + radius * (start_rad + end_rad) / 2
            start_y = cy + radius * (start_rad + end_rad) / 2
            
            # Simpler pie chart using path
            start_x = cx + radius * (start_angle - 90) * 3.14159 / 180
            start_y = cy + radius * (start_angle - 90) * 3.14159 / 180
            
            # Generate pie slice path
            x1 = cx + radius * (start_angle - 90) * 3.14159 / 180
            y1 = cy + radius * (start_angle - 90) * 3.14159 / 180
            
            start_x = cx + radius * (start_rad + end_rad) / 2
            start_y = cy + radius * (start_rad + end_rad) / 2
            
            path_data = f'M {cx} {cy} L {cx + radius * (start_angle - 90) * 3.14159 / 180} {cy + radius * (start_angle - 90) * 3.14159 / 180} A {radius} {radius} 0 {large_arc} 1 {cx + radius * (end_angle - 90) * 3.14159 / 180} {cy + radius * (end_angle - 90) * 3.14159 / 180} Z'
            
            svg += f'<path d="{path_data}" fill="{colors[i % len(colors)]}" stroke="#2D3748" stroke-width="2"/>'
        
        svg += '</svg>'
        return svg
    
    def generate_bar_chart_svg(self, data, width=400, height=200):
        """Generate SVG bar chart for line counts"""
        colors = ['#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        if not data:
            return f'<svg width="{width}" height="{height}"><text x="50%" y="50%" text-anchor="middle" fill="#A0AEC0" font-size="14">No data available</text></svg>'
        
        max_value = max(data.values())
        bar_width = width / len(data) * 0.8
        gap = width / len(data) * 0.2
        
        svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        
        # Draw bars
        for i, (ext, count) in enumerate(data.items()):
            bar_height = (count / max_value) * (height - 40)
            x = i * (bar_width + gap) + gap / 2
            y = height - bar_height - 20
            
            svg += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{colors[i % len(colors)]}" rx="2"/>'
            svg += f'<text x="{x + bar_width/2}" y="{height - 5}" text-anchor="middle" fill="#A0AEC0" font-size="10">{ext}</text>'
            svg += f'<text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" fill="#E2E8F0" font-size="10">{count}</text>'
        
        svg += '</svg>'
        return svg
    
    def generate_html(self):
        """Generate the complete HTML infographic"""
        top_extensions = self.get_top_extensions()
        top_files = self.get_top_files()
        dir_stats = self.get_directory_stats()
        
        # Prepare data for charts
        chart_extensions = dict(list(top_extensions.items())[:5])
        chart_lines = {ext: self.line_counts[ext] for ext in chart_extensions.keys()}
        
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%);
            color: #E2E8F0;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50px;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(78, 205, 196, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            z-index: -1;
        }}
        
        .title {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            font-size: 1.2rem;
            color: #A0AEC0;
            font-weight: 300;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        
        .card {{
            background: rgba(45, 55, 72, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        }}
        
        .card-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #4ECDC4;
        }}
        
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 1rem;
            background: rgba(26, 32, 44, 0.6);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #4ECDC4;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #A0AEC0;
            margin-top: 0.25rem;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 200px;
        }}
        
        .file-list {{
            list-style: none;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: rgba(26, 32, 44, 0.4);
            border-radius: 8px;
            border-left: 3px solid #4ECDC4;
            transition: background 0.3s ease;
        }}
        
        .file-item:hover {{
            background: rgba(26, 32, 44, 0.6);
        }}
        
        .file-name {{
            font-weight: 500;
            color: #E2E8F0;
            font-size: 0.9rem;
            word-break: break-all;
        }}
        
        .file-size {{
            color: #4ECDC4;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        
        .extension-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 1rem;
        }}
        
        .extension-item {{
            text-align: center;
            padding: 1rem;
            background: rgba(26, 32, 44, 0.4);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
        }}
        
        .extension-item:hover {{
            background: rgba(26, 32, 44, 0.6);
            transform: scale(1.05);
        }}
        
        .extension-name {{
            font-size: 0.8rem;
            color: #A0AEC0;
            margin-bottom: 0.25rem;
        }}
        
        .extension-count {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #4ECDC4;
        }}
        
        .timestamp {{
            text-align: center;
            color: #718096;
            font-size: 0.9rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .title {{
                font-size: 2rem;
            }}
            
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.8s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header fade-in">
            <h1 class="title">Codebase Fingerprint</h1>
            <p class="subtitle">Comprehensive analysis of your code repository</p>
        </div>
        
        <div class="dashboard">
            <div class="card fade-in">
                <h2 class="card-title">📊 Overall Statistics</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value">{self.total_files:,}</span>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{self.total_lines:,}</span>
                        <div class="stat-label">Total Lines</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{self.format_size(self.total_size)}</span>
                        <div class="stat-label">Total Size</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{dir_stats['max']}</span>
                        <div class="stat-label">Max Depth</div>
                    </div>
                </div>
            </div>
            
            <div class="card fade-in">
                <h2 class="card-title">📈 File Types Distribution</h2>
                <div class="chart-container">
                    {self.generate_pie_chart_svg(chart_extensions)}
                </div>
            </div>
            
            <div class="card fade-in">
                <h2 class="card-title">📊 Lines of Code by Type</h2>
                <div class="chart-container">
                    {self.generate_bar_chart_svg(chart_lines)}
                </div>
            </div>
            
            <div class="card fade-in">
                <h2 class="card-title">🔝 Largest Files</h2>
                <ul class="file-list">
                    {''.join([f'<li class="file-item"><span class="file-name">{Path(path).name}</span><span class="file-size">{self.format_size(size)}</span></li>' for path, size, ext in top_files[:5]])}
                </ul>
            </div>
            
            <div class="card fade-in">
                <h2 class="card-title">🔤 File Extensions</h2>
                <div class="extension-grid">
                    {''.join([f'<div class="extension-item"><div class="extension-name">{ext}</div><div class="extension-count">{count}</div></div>' for ext, count in list(top_extensions.items())[:6]])}
                </div>
            </div>
            
            <div class="card fade-in">
                <h2 class="card-title">📁 Directory Stats</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-value">{dir_stats['max']}</span>
                        <div class="stat-label">Maximum Depth</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{dir_stats['avg']:.1f}</span>
                        <div class="stat-label">Average Depth</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
    
    <script>
        // Add some interactive effects
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.card');
            
            // Add staggered animation
            cards.forEach((card, index) => {{
                card.style.animationDelay = `${{index * 0.1}}s`;
            }});
            
            // Add click effect to stat items
            const statItems = document.querySelectorAll('.stat-item');
            statItems.forEach(item => {{
                item.addEventListener('click', function() {{
                    this.style.transform = 'scale(0.95)';
                    setTimeout(() => {{
                        this.style.transform = 'scale(1)';
                    }}, 150);
                }});
            }});
            
            // Add hover effect to extension items
            const extItems = document.querySelectorAll('.extension-item');
            extItems.forEach(item => {{
                item.addEventListener('mouseenter', function() {{
                    this.style.boxShadow = '0 4px 12px rgba(78, 205, 196, 0.3)';
                }});
                
                item.addEventListener('mouseleave', function() {{
                    this.style.boxShadow = 'none';
                }});
            }});
        }});
    </script>
</body>
</html>'''
        
        return html

def main():
    """Main function"""
    print("🔍 Scanning directory...")
    generator = GitStatsGenerator()
    generator.scan_directory()
    
    print("📊 Generating infographic...")
    html_content = generator.generate_html()
    
    # Write HTML file
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Stats infographic generated: stats.html")
    print("🌐 Open stats.html in your browser to view the infographic!")

if __name__ == "__main__":
    main()