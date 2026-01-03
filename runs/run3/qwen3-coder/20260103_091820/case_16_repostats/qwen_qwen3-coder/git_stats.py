import os
import json
from collections import defaultdict, Counter
from pathlib import Path

def get_file_stats(root_dir='.'):
    """Scan directory and collect file statistics"""
    file_count_by_ext = defaultdict(int)
    lines_by_ext = defaultdict(int)
    file_sizes = []
    max_depth = 0
    total_files = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Calculate directory depth
        depth = root[len(root_dir):].count(os.sep)
        max_depth = max(max_depth, depth)
        
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, root_dir)
            
            # Get file extension
            ext = Path(file).suffix.lower()
            if not ext:
                ext = '.no_ext'
            file_count_by_ext[ext] += 1
            
            try:
                # Get file size
                size = os.path.getsize(file_path)
                file_sizes.append((relative_path, size))
                
                # Count lines for text files
                if ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.md', '.txt', '.json', '.xml', '.yml', '.yaml']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        lines_by_ext[ext] += lines
            except (OSError, IOError):
                # Skip files that can't be read
                pass
    
    # Get largest files
    largest_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
    
    # Total lines of code
    total_lines = sum(lines_by_ext.values())
    
    return {
        'file_count_by_ext': dict(file_count_by_ext),
        'lines_by_ext': dict(lines_by_ext),
        'total_lines': total_lines,
        'largest_files': largest_files,
        'max_depth': max_depth,
        'total_files': total_files
    }

def generate_pie_chart(data, title="File Types"):
    """Generate SVG pie chart"""
    total = sum(data.values())
    if total == 0:
        return "<p>No data available</p>"
    
    # Sort by value and limit to top 8
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    if len(sorted_data) < len(data):
        others = sum(v for k, v in data.items() if k not in dict(sorted_data))
        sorted_data.append(('Others', others))
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B', '#FB5607', 
        '#8338EC', '#3A86FF', '#06D6A0', '#118AB2', '#073B4C'
    ]
    
    svg = f'<div class="chart-container"><h3>{title}</h3><svg viewBox="0 0 200 200" width="200" height="200">'
    
    cx, cy, r = 100, 100, 80
    start_angle = 0
    
    legend = '<div class="legend">'
    
    for i, (label, value) in enumerate(sorted_data):
        percentage = (value / total) * 100
        angle = (value / total) * 360
        end_angle = start_angle + angle
        
        # Convert angles to radians
        start_rad = (start_angle - 90) * 3.14159 / 180
        end_rad = (end_angle - 90) * 3.14159 / 180
        
        # Calculate coordinates
        x1 = cx + r * np.cos(start_rad)
        y1 = cy + r * np.sin(start_rad)
        x2 = cx + r * np.cos(end_rad)
        y2 = cy + r * np.sin(end_rad)
        
        # Large arc flag
        large_arc = 1 if angle > 180 else 0
        
        # Draw path
        path = f'M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc},1 {x2},{y2} Z'
        color = colors[i % len(colors)]
        svg += f'<path d="{path}" fill="{color}" stroke="#1e1e1e" stroke-width="1"/>'
        
        # Add legend entry
        legend += f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div><span>{label} ({value})</span></div>'
        
        start_angle = end_angle
    
    legend += '</div>'
    svg += '</svg></div>'
    
    return svg + legend

def generate_bar_chart(data, title="Lines by File Type"):
    """Generate SVG bar chart"""
    if not data:
        return "<p>No data available</p>"
    
    # Sort by value and limit to top 8
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    
    max_value = max(data.values()) if data else 1
    bar_height = 20
    bar_spacing = 10
    chart_width = 300
    chart_height = len(sorted_data) * (bar_height + bar_spacing) + 20
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B', '#FB5607', 
        '#8338EC', '#3A86FF', '#06D6A0'
    ]
    
    svg = f'<div class="chart-container"><h3>{title}</h3><svg viewBox="0 0 {chart_width} {chart_height}" width="{chart_width}" height="{chart_height}">'
    
    legend = '<div class="legend">'
    
    for i, (label, value) in enumerate(sorted_data):
        bar_width = (value / max_value) * (chart_width - 120)
        y_pos = i * (bar_height + bar_spacing) + bar_spacing
        
        color = colors[i % len(colors)]
        svg += f'<rect x="0" y="{y_pos}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="3"/>'
        svg += f'<text x="{bar_width + 10}" y="{y_pos + bar_height/2 + 5}" fill="#e0e0e0" font-size="12">{value:,}</text>'
        
        # Add legend entry
        legend += f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div><span>{label} ({value:,})</span></div>'
    
    legend += '</div>'
    svg += '</svg></div>'
    
    return svg + legend

def generate_html_report(stats):
    """Generate HTML report with stats"""
    # We need to handle the pie chart differently since we can't use numpy
    file_count_html = generate_simple_pie_chart(stats['file_count_by_ext'], "File Types")
    lines_chart_html = generate_bar_chart(stats['lines_by_ext'], "Lines by File Type")
    
    # Format largest files
    largest_files_html = '<div class="file-list"><h3>Largest Files</h3><ul>'
    for file_path, size in stats['largest_files'][:10]:
        size_kb = size / 1024
        if size_kb > 1024:
            size_str = f"{size_kb/1024:.1f} MB"
        else:
            size_str = f"{size_kb:.1f} KB"
        largest_files_html += f'<li><span class="file-name">{file_path}</span><span class="file-size">{size_str}</span></li>'
    largest_files_html += '</ul></div>'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg-primary: #121212;
            --bg-secondary: #1e1e1e;
            --bg-card: #252526;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --accent-primary: #bb86fc;
            --accent-secondary: #03dac6;
            --border-color: #333;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background-color: var(--bg-card);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
            color: var(--accent-primary);
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .chart-container {{
            background-color: var(--bg-card);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }}
        
        .chart-container h3 {{
            margin-bottom: 15px;
            color: var(--accent-secondary);
        }}
        
        .legend {{
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .legend-color {{
            width: 15px;
            height: 15px;
            border-radius: 3px;
            margin-right: 10px;
        }}
        
        .file-list {{
            background-color: var(--bg-card);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }}
        
        .file-list h3 {{
            margin-bottom: 15px;
            color: var(--accent-secondary);
        }}
        
        .file-list ul {{
            list-style: none;
        }}
        
        .file-list li {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .file-list li:last-child {{
            border-bottom: none;
        }}
        
        .file-name {{
            flex: 1;
            word-break: break-all;
        }}
        
        .file-size {{
            color: var(--accent-primary);
            font-weight: bold;
            margin-left: 15px;
            white-space: nowrap;
        }}
        
        footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your code repository</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_files']:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_lines']:,}</div>
                <div class="stat-label">Total Lines</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(stats['file_count_by_ext'])}</div>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                {file_count_html}
            </div>
            <div class="chart-container">
                {lines_chart_html}
            </div>
        </div>
        
        <div class="file-list">
            {largest_files_html}
        </div>
        
        <footer>
            <p>Generated with Python • Git Stats Infographic Generator</p>
        </footer>
    </div>
    
    <script>
        // Simple animation for stat cards
        document.addEventListener('DOMContentLoaded', function() {{
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach((card, index) => {{
                // Stagger the animations
                setTimeout(() => {{
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    
                    // Trigger the animation
                    requestAnimationFrame(() => {{
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }});
                }}, index * 100);
            }});
        }});
    </script>
</body>
</html>'''
    
    return html

def generate_simple_pie_chart(data, title):
    """Generate a simple pie chart without external libraries"""
    total = sum(data.values())
    if total == 0:
        return "<p>No data available</p>"
    
    # Sort by value and limit to top 8
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:8]
    if len(sorted_data) < len(data):
        others = sum(v for k, v in data.items() if k not in dict(sorted_data))
        sorted_data.append(('Others', others))
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B', '#FB5607', 
        '#8338EC', '#3A86FF', '#06D6A0', '#118AB2', '#073B4C'
    ]
    
    # Create SVG pie chart manually
    svg = f'<h3>{title}</h3><svg viewBox="0 0 200 200" width="200" height="200">'
    
    cx, cy, r = 100, 100, 80
    start_angle = 0
    
    legend = '<div class="legend">'
    
    for i, (label, value) in enumerate(sorted_data):
        percentage = (value / total) * 100
        angle = (value / total) * 360
        end_angle = start_angle + angle
        
        # Convert to radians for calculation
        import math
        start_rad = math.radians(start_angle - 90)
        end_rad = math.radians(end_angle - 90)
        
        # Calculate coordinates
        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)
        
        # Large arc flag (1 if angle > 180, 0 otherwise)
        large_arc = 1 if angle > 180 else 0
        
        # Draw path
        path = f'M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc},1 {x2},{y2} Z'
        color = colors[i % len(colors)]
        svg += f'<path d="{path}" fill="{color}" stroke="#1e1e1e" stroke-width="1"/>'
        
        # Add legend entry
        legend += f'<div class="legend-item"><div class="legend-color" style="background:{color}"></div><span>{label} ({value})</span></div>'
        
        start_angle = end_angle
    
    legend += '</div>'
    svg += '</svg>'
    
    return svg + legend

def main():
    # Get stats
    stats = get_file_stats()
    
    # Generate HTML report
    html = generate_html_report(stats)
    
    # Write to file
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Stats report generated: stats.html")

if __name__ == "__main__":
    main()