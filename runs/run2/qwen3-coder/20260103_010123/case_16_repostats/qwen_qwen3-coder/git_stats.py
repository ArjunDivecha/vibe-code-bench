import os
import json
from collections import defaultdict, Counter
from pathlib import Path

def scan_directory(path="."):
    """Recursively scan directory and gather statistics"""
    file_extensions = defaultdict(int)
    file_lines = defaultdict(int)
    file_sizes = []
    max_depth = 0
    
    for root, dirs, files in os.walk(path):
        # Calculate directory depth
        depth = root.replace(path, '').count(os.sep)
        max_depth = max(max_depth, depth)
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip if not a file or if it's a hidden file/directory
            if not os.path.isfile(file_path) or '/.' in file_path or file.startswith('.'):
                continue
                
            # Get file extension
            ext = Path(file).suffix.lower() or "no extension"
            file_extensions[ext] += 1
            
            # Get file size
            try:
                size = os.path.getsize(file_path)
                file_sizes.append((file_path, size))
                
                # Count lines for text files
                if ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.md', '.txt', '.json', '.xml', '.yml', '.yaml']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)
                        file_lines[ext] += line_count
            except (OSError, IOError):
                pass
    
    # Get largest files
    largest_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'file_extensions': dict(file_extensions),
        'file_lines': dict(file_lines),
        'total_lines': sum(file_lines.values()),
        'largest_files': largest_files,
        'directory_depth': max_depth,
        'total_files': sum(file_extensions.values())
    }

def generate_html(stats):
    """Generate HTML infographic"""
    # Prepare data for charts
    extensions = stats['file_extensions']
    lines = stats['file_lines']
    
    # Top 5 extensions for pie chart
    top_extensions = dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5])
    if len(extensions) > 5:
        others = sum(list(extensions.values())[5:])
        top_extensions['Others'] = others
    
    # Top 5 extensions by lines
    top_lines = dict(sorted(lines.items(), key=lambda x: x[1], reverse=True)[:5])
    
    # Generate pie chart SVG
    def generate_pie_chart(data, size=200):
        total = sum(data.values())
        if total == 0:
            return "<text>No data available</text>"
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B', '#FB5607', '#8338EC']
        svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        
        cx, cy, r = size/2, size/2, size/2 - 10
        start_angle = 0
        
        for i, (label, value) in enumerate(data.items()):
            percentage = value / total
            angle = percentage * 360
            end_angle = start_angle + angle
            
            # Convert angles to radians
            start_rad = start_angle * 3.14159 / 180
            end_rad = end_angle * 3.14159 / 180
            
            # Calculate coordinates
            x1 = cx + r * 3.14159 * 0.01 * start_angle
            y1 = cy + r * 3.14159 * 0.01 * start_angle
            x2 = cx + r * 3.14159 * 0.01 * end_angle
            y2 = cy + r * 3.14159 * 0.01 * end_angle
            
            # SVG arc path
            large_arc = 1 if angle > 180 else 0
            path_data = f"M {cx},{cy} L {cx + r * 3.14159 * 0.01 * start_angle},{cy + r * 3.14159 * 0.01 * start_angle} A {r},{r} 0 {large_arc},1 {cx + r * 3.14159 * 0.01 * end_angle},{cy + r * 3.14159 * 0.01 * end_angle} Z"
            
            color = colors[i % len(colors)]
            svg += f'<path d="{path_data}" fill="{color}" />'
            
            # Add label
            mid_angle = (start_angle + end_angle) / 2
            label_x = cx + (r * 0.7) * 3.14159 * 0.01 * mid_angle
            label_y = cy + (r * 0.7) * 3.14159 * 0.01 * mid_angle
            svg += f'<text x="{label_x}" y="{label_y}" fill="white" font-size="10" text-anchor="middle">{label}</text>'
            
            start_angle = end_angle
        
        svg += '</svg>'
        return svg
    
    # Generate bar chart SVG
    def generate_bar_chart(data, width=400, height=200):
        if not data:
            return "<text>No data available</text>"
        
        max_value = max(data.values()) if data.values() else 1
        bar_width = width / len(data) - 10
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B', '#FB5607']
        
        svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        
        for i, (label, value) in enumerate(data.items()):
            bar_height = (value / max_value) * (height - 40)
            x = i * (bar_width + 10) + 10
            y = height - bar_height - 20
            
            color = colors[i % len(colors)]
            svg += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" />'
            
            # Label
            svg += f'<text x="{x + bar_width/2}" y="{height - 5}" fill="white" font-size="10" text-anchor="middle">{label}</text>'
            
            # Value
            svg += f'<text x="{x + bar_width/2}" y="{y - 5}" fill="white" font-size="10" text-anchor="middle">{value}</text>'
        
        svg += '</svg>'
        return svg
    
    # Create the HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg-dark: #121212;
            --card-bg: #1e1e1e;
            --text-light: #e0e0e0;
            --accent: #bb86fc;
            --border: #333333;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-light);
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--border);
        }}
        
        h1 {{
            font-size: 2.5rem;
            color: var(--accent);
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #999;
            font-size: 1.1rem;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background-color: var(--card-bg);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }}
        
        .card-icon {{
            margin-right: 10px;
            font-size: 1.5rem;
        }}
        
        .card-title {{
            font-size: 1.3rem;
            font-weight: 600;
        }}
        
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }}
        
        .stat:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            color: #aaa;
        }}
        
        .stat-value {{
            font-weight: 600;
            color: var(--accent);
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
        
        .file-list li {{
            padding: 8px 0;
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #333;
        }}
        
        .file-list li:last-child {{
            border-bottom: none;
        }}
        
        .file-name {{
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 70%;
        }}
        
        .file-size {{
            color: var(--accent);
            font-weight: 600;
        }}
        
        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid var(--border);
            margin-top: 20px;
        }}
        
        @media (max-width: 768px) {{
            .grid {{
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
            <p class="subtitle">A statistical overview of your codebase</p>
        </header>
        
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📊</span>
                    <h2 class="card-title">File Extensions</h2>
                </div>
                <div class="chart-container">
                    {generate_pie_chart(top_extensions)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📈</span>
                    <h2 class="card-title">Lines of Code by Extension</h2>
                </div>
                <div class="chart-container">
                    {generate_bar_chart(top_lines)}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📁</span>
                    <h2 class="card-title">Codebase Summary</h2>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Files:</span>
                    <span class="stat-value">{stats['total_files']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Lines:</span>
                    <span class="stat-value">{stats['total_lines']:,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Directory Depth:</span>
                    <span class="stat-value">{stats['directory_depth']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">File Types:</span>
                    <span class="stat-value">{len(extensions)}</span>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">⚖️</span>
                    <h2 class="card-title">Largest Files</h2>
                </div>
                <ul class="file-list">
    """
    
    for file_path, size in stats['largest_files'][:5]:
        # Format file size
        if size > 1024*1024:
            size_str = f"{size/(1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size} B"
            
        html += f"""
                    <li>
                        <span class="file-name">{file_path}</span>
                        <span class="file-size">{size_str}</span>
                    </li>
        """
    
    html += """
                </ul>
            </div>
        </div>
        
        <footer>
            <p>Generated with Git Stats Infographic Generator</p>
        </footer>
    </div>
</body>
</html>
    """
    
    return html

def main():
    """Main function to scan directory and generate infographic"""
    print("Scanning directory...")
    stats = scan_directory()
    
    print("Generating infographic...")
    html = generate_html(stats)
    
    with open("stats.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("Infographic saved to stats.html")
    print(f"Total files: {stats['total_files']}")
    print(f"Total lines: {stats['total_lines']:,}")
    print(f"Directory depth: {stats['directory_depth']}")

if __name__ == "__main__":
    main()