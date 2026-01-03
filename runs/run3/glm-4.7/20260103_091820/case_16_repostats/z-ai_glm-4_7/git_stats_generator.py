#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans directory and generates a beautiful HTML infographic
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from html import escape


class CodebaseAnalyzer:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir).resolve()
        self.file_stats = defaultdict(lambda: {"count": 0, "lines": 0})
        self.total_files = 0
        self.total_lines = 0
        self.largest_files = []
        self.max_depth = 0
        self.directory_count = 0
        
        # Color palette for charts (vibrant colors for dark mode)
        self.colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
            "#F8B500", "#FF6F61", "#6B5B95", "#88B04B", "#F7CAC9",
            "#92A8D1", "#955251", "#B565A7", "#009B77", "#DD4124"
        ]
    
    def is_binary_file(self, filepath):
        """Check if a file is binary by reading a small portion"""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return True
                # Check for common binary signatures
                textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                return not bool(chunk.translate(None, textchars))
        except:
            return True
    
    def count_lines(self, filepath):
        """Count lines in a file, handling different encodings"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def analyze(self):
        """Recursively analyze the codebase"""
        print(f"Scanning: {self.root_dir}")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'venv', 'env', '.git',
                'dist', 'build', 'target', 'bin', 'obj'
            }]
            
            # Calculate depth
            rel_path = Path(root).relative_to(self.root_dir)
            depth = len(rel_path.parts) if str(rel_path) != '.' else 0
            self.max_depth = max(self.max_depth, depth)
            self.directory_count += 1
            
            for filename in files:
                if filename.startswith('.'):
                    continue
                
                filepath = Path(root) / filename
                try:
                    file_size = filepath.stat().st_size
                    
                    # Skip very large files (likely binaries)
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        continue
                    
                    if self.is_binary_file(filepath):
                        continue
                    
                    # Get file extension
                    ext = filepath.suffix.lower()
                    if not ext:
                        ext = '(no extension)'
                    
                    # Count lines
                    lines = self.count_lines(filepath)
                    
                    # Update stats
                    self.file_stats[ext]["count"] += 1
                    self.file_stats[ext]["lines"] += lines
                    self.total_files += 1
                    self.total_lines += lines
                    
                    # Track largest files
                    self.largest_files.append({
                        "name": str(filepath.relative_to(self.root_dir)),
                        "lines": lines,
                        "size": file_size
                    })
                    
                except (PermissionError, OSError):
                    continue
        
        # Sort largest files by line count
        self.largest_files.sort(key=lambda x: x["lines"], reverse=True)
        self.largest_files = self.largest_files[:10]
    
    def generate_svg_pie_chart(self, data, width=300, height=300):
        """Generate SVG pie chart"""
        total = sum(d["count"] for d in data)
        if total == 0:
            return ""
        
        cx, cy = width // 2, height // 2
        radius = min(width, height) // 2 - 20
        
        svg_parts = []
        start_angle = 0
        
        for i, item in enumerate(data):
            count = item["count"]
            if count == 0:
                continue
            
            slice_angle = (count / total) * 360
            end_angle = start_angle + slice_angle
            
            # Convert to radians
            start_rad = (start_angle - 90) * 3.14159 / 180
            end_rad = (end_angle - 90) * 3.14159 / 180
            
            # Calculate coordinates
            x1 = cx + radius * (3.14159 / 180) * (start_angle - 90)
            y1 = cy + radius * (3.14159 / 180) * (start_angle - 90)
            x2 = cx + radius * (3.14159 / 180) * (end_angle - 90)
            y2 = cy + radius * (3.14159 / 180) * (end_angle - 90)
            
            # Better coordinate calculation
            def get_coord(angle):
                rad = (angle - 90) * 3.14159 / 180
                return cx + radius * (rad / 3.14159) * 180, cy + radius * (rad / 3.14159) * 180
            
            # Use proper trigonometry
            x1 = cx + radius * ((3.14159 / 180) * (start_angle - 90) / 3.14159 * 180)
            y1 = cy + radius * ((3.14159 / 180) * (start_angle - 90) / 3.14159 * 180)
            
            # Simpler approach: use sin/cos
            import math
            x1 = cx + radius * math.cos(math.radians(start_angle - 90))
            y1 = cy + radius * math.sin(math.radians(start_angle - 90))
            x2 = cx + radius * math.cos(math.radians(end_angle - 90))
            y2 = cy + radius * math.sin(math.radians(end_angle - 90))
            
            large_arc = 1 if slice_angle > 180 else 0
            
            if slice_angle >= 360:
                path = f"M {cx} {cy - radius} A {radius} {radius} 0 1 1 {cx} {cy + radius} A {radius} {radius} 0 1 1 {cx} {cy - radius}"
            else:
                path = f"M {cx} {cy} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z"
            
            color = self.colors[i % len(self.colors)]
            percentage = (count / total) * 100
            
            svg_parts.append(f'''
                <path d="{path}" fill="{color}" stroke="#1a1a2e" stroke-width="2" 
                      class="slice" data-label="{escape(item['ext'])}" data-value="{count}" data-percent="{percentage:.1f}">
                    <title>{escape(item['ext'])}: {count} files ({percentage:.1f}%)</title>
                </path>
            ''')
            
            start_angle = end_angle
        
        return f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            {"".join(svg_parts)}
            <circle cx="{cx}" cy="{cy}" r="40" fill="#1a1a2e"/>
            <text x="{cx}" y="{cy - 5}" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="bold">{total}</text>
            <text x="{cx}" y="{cy + 15}" text-anchor="middle" fill="#888888" font-size="10">FILES</text>
        </svg>
        '''
    
    def generate_svg_bar_chart(self, data, width=500, height=300):
        """Generate SVG bar chart"""
        if not data:
            return ""
        
        max_value = max(d["lines"] for d in data)
        if max_value == 0:
            max_value = 1
        
        bar_width = (width - 100) / len(data)
        max_bar_height = height - 60
        
        svg_parts = []
        
        for i, item in enumerate(data):
            bar_height = (item["lines"] / max_value) * max_bar_height
            x = 60 + i * bar_width
            y = height - 30 - bar_height
            
            color = self.colors[i % len(self.colors)]
            
            # Bar
            svg_parts.append(f'''
                <rect x="{x + 2}" y="{y}" width="{bar_width - 4}" height="{bar_height}" 
                      fill="{color}" rx="3" class="bar">
                    <title>{escape(item['ext'])}: {item['lines']:,} lines</title>
                </rect>
            ''')
            
            # Value on top
            if bar_height > 20:
                svg_parts.append(f'''
                    <text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" 
                          fill="#ffffff" font-size="10">{item['lines']:,}</text>
                ''')
            
            # Label on bottom
            ext = item['ext'][:10] + '...' if len(item['ext']) > 10 else item['ext']
            svg_parts.append(f'''
                <text x="{x + bar_width/2}" y="{height - 10}" text-anchor="middle" 
                      fill="#888888" font-size="9" transform="rotate(-45, {x + bar_width/2}, {height - 10})">{escape(ext)}</text>
            ''')
        
        # Y-axis labels
        for i in range(5):
            value = int((max_value / 4) * i)
            y = height - 30 - (value / max_value) * max_bar_height
            svg_parts.append(f'''
                <text x="50" y="{y + 3}" text-anchor="end" fill="#666666" font-size="9">{value:,}</text>
                <line x1="55" y1="{y}" x2="{width - 20}" y2="{y}" stroke="#333333" stroke-dasharray="2"/>
            ''')
        
        return f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            {"".join(svg_parts)}
            <text x="{width/2}" y="20" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="bold">Lines by File Type</text>
        </svg>
        '''
    
    def format_size(self, bytes_size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"
    
    def generate_html(self):
        """Generate the HTML infographic"""
        # Prepare data for charts
        ext_data = sorted([
            {"ext": ext, "count": stats["count"], "lines": stats["lines"]}
            for ext, stats in self.file_stats.items()
        ], key=lambda x: x["count"], reverse=True)[:10]
        
        lines_data = sorted([
            {"ext": ext, "count": stats["count"], "lines": stats["lines"]}
            for ext, stats in self.file_stats.items()
        ], key=lambda x: x["lines"], reverse=True)[:8]
        
        pie_chart = self.generate_svg_pie_chart(ext_data)
        bar_chart = self.generate_svg_bar_chart(lines_data)
        
        # Generate legend for pie chart
        legend_items = []
        for i, item in enumerate(ext_data):
            color = self.colors[i % len(self.colors)]
            percentage = (item["count"] / self.total_files * 100) if self.total_files > 0 else 0
            legend_items.append(f'''
                <div class="legend-item">
                    <span class="legend-color" style="background: {color}"></span>
                    <span class="legend-label">{escape(item['ext'])}</span>
                    <span class="legend-value">{item['count']} ({percentage:.1f}%)</span>
                </div>
            ''')
        
        # Generate largest files list
        largest_files_html = ""
        for i, f in enumerate(self.largest_files):
            largest_files_html += f'''
                <div class="file-item">
                    <span class="file-rank">{i + 1}</span>
                    <span class="file-name" title="{escape(f['name'])}">{escape(f['name'][:50]) + '...' if len(f['name']) > 50 else escape(f['name'])}</span>
                    <span class="file-lines">{f['lines']:,} lines</span>
                    <span class="file-size">{self.format_size(f['size'])}</span>
                </div>
            '''
        
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
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 3rem;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: 2px;
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1.1rem;
        }}
        
        .path {{
            color: #4ECDC4;
            font-family: monospace;
            margin-top: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card:nth-child(1) .stat-value {{ color: #FF6B6B; }}
        .stat-card:nth-child(2) .stat-value {{ color: #4ECDC4; }}
        .stat-card:nth-child(3) .stat-value {{ color: #45B7D1; }}
        .stat-card:nth-child(4) .stat-value {{ color: #FFEAA7; }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #fff;
            text-align: center;
        }}
        
        .chart-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px 12px;
            border-radius: 20px;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .legend-label {{
            color: #ccc;
            font-size: 0.85rem;
        }}
        
        .legend-value {{
            color: #fff;
            font-weight: bold;
            font-size: 0.85rem;
        }}
        
        .largest-files {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .file-list {{
            margin-top: 20px;
        }}
        
        .file-item {{
            display: grid;
            grid-template-columns: 40px 1fr auto auto;
            gap: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            margin-bottom: 10px;
            align-items: center;
            transition: background 0.3s;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.08);
        }}
        
        .file-rank {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9rem;
        }}
        
        .file-name {{
            color: #ccc;
            font-family: monospace;
            font-size: 0.9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .file-lines {{
            color: #4ECDC4;
            font-weight: bold;
        }}
        
        .file-size {{
            color: #888;
            font-size: 0.85rem;
        }}
        
        .slice {{
            cursor: pointer;
            transition: opacity 0.3s, transform 0.3s;
            transform-origin: center;
        }}
        
        .slice:hover {{
            opacity: 0.8;
            transform: scale(1.05);
        }}
        
        .bar {{
            cursor: pointer;
            transition: opacity 0.3s;
        }}
        
        .bar:hover {{
            opacity: 0.8;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid #333;
            margin-top: 30px;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .file-item {{
                grid-template-columns: 30px 1fr;
                gap: 10px;
            }}
            
            .file-size {{
                grid-column: 2;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Visual Analytics of Your Project</p>
            <p class="path">{escape(str(self.root_dir))}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{self.total_files:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.total_lines:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.max_depth}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.directory_count:,}</div>
                <div class="stat-label">Directories</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h2 class="chart-title">Files by Extension</h2>
                <div class="chart-wrapper">
                    {pie_chart}
                </div>
                <div class="legend">
                    {"".join(legend_items)}
                </div>
            </div>
            
            <div class="chart-container">
                <h2 class="chart-title">Lines by File Type</h2>
                <div class="chart-wrapper">
                    {bar_chart}
                </div>
            </div>
        </div>
        
        <div class="largest-files">
            <h2 class="chart-title">Top 10 Largest Files (by lines)</h2>
            <div class="file-list">
                {largest_files_html if self.largest_files else '<p style="text-align: center; color: #888;">No files found</p>'}
            </div>
        </div>
        
        <footer>
            Generated by Git Stats Infographic Generator | Python Standard Library Only
        </footer>
    </div>
    
    <script>
        // Add simple interactivity
        document.querySelectorAll('.stat-card').forEach(card => {{
            card.addEventListener('mouseenter', function() {{
                this.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            }});
            card.addEventListener('mouseleave', function() {{
                this.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }});
        }});
        
        // Animate stats on load
        document.addEventListener('DOMContentLoaded', function() {{
            const stats = document.querySelectorAll('.stat-value');
            stats.forEach(stat => {{
                const finalValue = stat.textContent;
                const isNumeric = /^\\d[,\\d]+$/.test(finalValue);
                
                if (isNumeric) {{
                    const target = parseInt(finalValue.replace(/,/g, ''));
                    let current = 0;
                    const increment = target / 50;
                    const duration = 1000;
                    const stepTime = duration / 50;
                    
                    const counter = setInterval(() => {{
                        current += increment;
                        if (current >= target) {{
                            stat.textContent = finalValue;
                            clearInterval(counter);
                        }} else {{
                            stat.textContent = Math.floor(current).toLocaleString();
                        }}
                    }}, stepTime);
                }}
            }});
        }});
    </script>
</body>
</html>'''
        
        return html


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a codebase statistics infographic")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan (default: current)")
    parser.add_argument("-o", "--output", default="stats.html", help="Output HTML file (default: stats.html)")
    
    args = parser.parse_args()
    
    # Analyze the codebase
    analyzer = CodebaseAnalyzer(args.directory)
    analyzer.analyze()
    
    # Generate and save HTML
    html = analyzer.generate_html()
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Infographic generated: {args.output}")
    print(f"  - {analyzer.total_files:,} files analyzed")
    print(f"  - {analyzer.total_lines:,} lines of code")
    print(f"  - {analyzer.directory_count:,} directories")
    print(f"  - Max depth: {analyzer.max_depth}")


if __name__ == "__main__":
    main()