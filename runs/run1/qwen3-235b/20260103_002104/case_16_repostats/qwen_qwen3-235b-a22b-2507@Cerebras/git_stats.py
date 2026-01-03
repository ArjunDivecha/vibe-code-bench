import os
import json
from datetime import datetime
from collections import defaultdict, Counter

def scan_directory(directory="."):
    """Recursively scan directory and collect statistics."""
    file_stats = []
    extension_data = Counter()
    total_lines = 0
    largest_files = []  # (path, size, lines)
    max_depth = 0
    
    for root, dirs, files in os.walk(directory):
        # Calculate depth
        depth = root[len(directory):].count(os.sep)
        max_depth = max(max_depth, depth)
        
        for file in files:
            filepath = os.path.join(root, file)
            
            # Skip the output HTML file if it exists
            if file == "stats.html":
                continue
                
            try:
                # Get file size
                stat = os.stat(filepath)
                size = stat.st_size
                
                # Get file extension
                _, ext = os.path.splitext(file)
                ext = ext.lower() or f".{file.split('.')[-1]}"  # fallback for dotfiles
                
                # Count lines
                lines = 0
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            lines += 1
                except (UnicodeDecodeError, IOError):
                    # Binary file or unreadable
                    pass
                
                # Update counters
                extension_data[ext] += 1
                total_lines += lines
                
                # Store file info
                file_stats.append({
                    'path': filepath,
                    'size': size,
                    'lines': lines,
                    'ext': ext
                })
                
                # Track largest files (by size)
                if len(largest_files) < 5:
                    largest_files.append((filepath, size, lines))
                    largest_files.sort(key=lambda x: x[1], reverse=True)
                elif size > largest_files[-1][1]:
                    largest_files[-1] = (filepath, size, lines)
                    largest_files.sort(key=lambda x: x[1], reverse=True)
                    
            except (OSError, IOError):
                # Skip files we can't access
                continue
    
    # Get top extensions by count and by lines
    top_extensions_count = extension_data.most_common(5)
    
    # Calculate lines by extension
    lines_by_extension = defaultdict(int)
    for stat in file_stats:
        lines_by_extension[stat['ext']] += stat['lines']
    
    top_extensions_lines = sorted(lines_by_extension.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total_files': len(file_stats),
        'extension_count': dict(top_extensions_count),
        'total_lines': total_lines,
        'largest_files': largest_files,
        'max_depth': max_depth,
        'lines_by_extension': dict(top_extensions_lines),
        'total_directories': sum(1 for _, dirs, _ in os.walk(directory) for _ in dirs) + 1
    }

def generate_pie_chart(data, width=300, height=300):
    """Generate SVG pie chart from data dictionary."""
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
    ]
    
    total = sum(data.values())
    if total == 0:
        return '<svg width="300" height="300"><text x="150" y="150" text-anchor="middle" fill="white">No data</text></svg>'
    
    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 2 - 10
    
    # Create legend
    legend_x = width - 120
    legend_y = 20
    
    current_angle = 0
    items = list(data.items())
    
    for i, (label, value) in enumerate(items):
        color = colors[i % len(colors)]
        
        # Calculate angles
        ratio = value / total
        angle = ratio * 360
        
        # Convert to radians
        start_angle = current_angle * 3.14159 / 180
        end_angle = (current_angle + angle) * 3.14159 / 180
        
        # Calculate points
        x1 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9 * 0.9
        y1 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9 * 0.9
        
        x2 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9 * 0.9
        y2 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9 * 0.9
        
        x1 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9
        y1 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9
        
        x2 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9
        y2 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9 * 0.9
        
        x1 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9
        y1 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9
        
        x2 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9
        y2 = center_x + radius * 0.7 * 0.9 * 0.9 * 0.9
        
        x1 = center_x + radius * 0.7 * 0.9 * 0.9
        y1 = center_x + radius * 0.7 * 0.9 * 0.9
        
        x2 = center_x + radius * 0.7 * 0.9 * 0.9
        y2 = center_x + radius * 0.7 * 0.9 * 0.9
        
        x1 = center_x + radius * 0.7 * 0.9
        y1 = center_x + radius * 0.7 * 0.9
        
        x2 = center_x + radius * 0.7 * 0.9
        y2 = center_x + radius * 0.7 * 0.9
        
        x1 = center_x + radius * 0.7
        y1 = center_y + radius * 0.7
        x2 = center_x + radius * 0.7 * 0.9
        y2 = center_y + radius * 0.7 * 0.9
        
        x1 = center_x + radius * 0.7 * 0.9
        y1 = center_y + radius * 0.7 * 0.9
        x2 = center_x + radius * 0.7
        y2 = center_y + radius * 0.7
        
        # Large arc flag
        large_arc = 1 if angle > 180 else 0
        
        # Starting point
        if i == 0:
            start_x = center_x + radius * 0.7
            start_y = center_y
        else:
            start_x = center_x + radius * 0.7 * __import__('math').cos(start_angle)
            start_y = center_y + radius * 0.7 * __import__('math').sin(start_angle)
        
        # End point
        end_x = center_x + radius * 0.7 * __import__('math').cos(end_angle)
        end_y = center_y + radius * 0.7 * __import__('math').sin(end_angle)
        
        # Create path
        path = (
            f"M {center_x} {center_y} "
            f"L {start_x} {start_y} "
            f"A {radius * 0.7} {radius * 0.7} 0 {large_arc} 1 {end_x} {end_y} "
            f"Z"
        )
        
        svg_parts.append(f'<path d="{path}" fill="{color}" stroke="#222" stroke-width="1"/>')
        
        # Add legend
        legend_item = (
            f'<rect x="{legend_x}" y="{legend_y + i * 25}" width="12" height="12" fill="{color}" />'
            f'<text x="{legend_x + 20}" y="{legend_y + i * 25 + 10}" fill="white" font-size="12px">{label}</text>'
            f'<tspan fill="#888" font-size="10px" x="{legend_x + 100}" y="{legend_y + i * 25 + 10}">({ratio*100:.1f}%)</tspan>'
        )
        svg_parts.append(legend_item)
        
        current_angle += angle
    
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def generate_bar_chart(data, width=400, height=200, title=""):
    """Generate SVG bar chart from data dictionary."""
    if not data:
        return '<svg width="400" height="200"><text x="200" y="100" text-anchor="middle" fill="white">No data</text></svg>'
    
    # Sort data by value
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    max_value = max(data.values())
    
    bar_width = (width - 100) // len(data)  # leave space for labels
    max_bar_width = 40
    bar_width = min(bar_width, max_bar_width)
    bar_spacing = 10
    
    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    
    # Add title
    if title:
        svg_parts.append(f'<text x="{width//2}" y="20" text-anchor="middle" fill="white" font-size="16px" font-weight="bold">{title}</text>')
    
    # Draw bars
    x_offset = 80  # leave space for y-axis labels
    y_offset = 40  # leave space for title
    chart_height = height - y_offset - 30
    chart_width = len(data) * (bar_width + bar_spacing)
    
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
    
    for i, (label, value) in enumerate(sorted_data):
        color = colors[i % len(colors)]
        bar_height = (value / max_value) * chart_height if max_value > 0 else 0
        x = x_offset + i * (bar_width + bar_spacing)
        y = height - 30 - bar_height
        
        # Bar
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4" />')
        
        # Value label on top of bar
        svg_parts.append(f'<text x="{x + bar_width//2}" y="{y - 5}" text-anchor="middle" fill="#BBB" font-size="10px">{value:,}</text>')
        
        # X-axis label
        svg_parts.append(f'<text x="{x + bar_width//2}" y="{height - 10}" text-anchor="middle" fill="white" font-size="10px">{label}</text>')
    
    # Y-axis
    svg_parts.append(f'<line x1="{x_offset}" y1="{y_offset}" x2="{x_offset}" y2="{height-30}" stroke="#444" />')
    
    # Y-axis labels
    for i in range(5):
        y_pos = height - 30 - (i * chart_height / 4)
        value = int(max_value * i / 4)
        svg_parts.append(f'<text x="{x_offset - 10}" y="{y_pos + 5}" text-anchor="end" fill="#888" font-size="10px">{value:,}</text>')
        svg_parts.append(f'<line x1="{x_offset}" y1="{y_pos}" x2="{width}" y2="{y_pos}" stroke="#444" stroke-dasharray="2,2" />')
    
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def generate_html_report(stats):
    """Generate complete HTML report with embedded SVG charts."""
    
    # Generate charts
    pie_chart_svg = generate_pie_chart(stats['extension_count'])
    lines_bar_chart_svg = generate_bar_chart(stats['lines_by_extension'], title="Lines of Code by Extension")
    
    # Format largest files
    largest_files_html = ""
    for path, size, lines in stats['largest_files']:
        rel_path = os.path.relpath(path)
        largest_files_html += f"""
        <div class="file-item">
            <span class="file-path" title="{rel_path}">{rel_path}</span>
            <span class="file-size">{size:,} bytes</span>
            <span class="file-lines">{lines:,} lines</span>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg-primary: #121212;
            --bg-secondary: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --accent: #8a2be2;
            --accent-hover: #a450f2;
            --card-bg: #252525;
            --border: #333333;
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
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 30px 0;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #8a2be2, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.2rem;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            border: 1px solid var(--border);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 20px rgba(0,0,0,0.4);
        }}
        
        .card h2 {{
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
        }}
        
        .card h2::before {{
            content: "";
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            margin-right: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        
        .stat-item {{
            background-color: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--accent);
            display: block;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        .chart-container {{
            text-align: center;
            padding: 10px;
        }}
        
        .file-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .file-list::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .file-list::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
            border-radius: 3px;
        }}
        
        .file-list::-webkit-scrollbar-thumb {{
            background: var(--accent);
            border-radius: 3px;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }}
        
        .file-item:last-child {{
            border-bottom: none;
        }}
        
        .file-path {{
            flex: 3;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text-primary);
        }}
        
        .file-size, .file-lines {{
            flex: 1;
            color: var(--text-secondary);
            font-family: monospace;
        }}
        
        footer {{
            text-align: center;
            padding: 30px 0;
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 30px;
            border-top: 1px solid var(--border);
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 2.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Generated on {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
        </header>
        
        <div class="dashboard">
            <div class="card">
                <h2>Overview</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value">{stats['total_files']:,}</span>
                        <span class="stat-label">Files</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{stats['total_directories']:,}</span>
                        <span class="stat-label">Directories</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{stats['total_lines']:,}</span>
                        <span class="stat-label">Lines of Code</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{stats['max_depth']}</span>
                        <span class="stat-label">Max Depth</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>File Distribution</h2>
                <div class="chart-container">
                    {pie_chart_svg}
                </div>
            </div>
            
            <div class="card">
                <h2>Lines of Code by Extension</h2>
                <div class="chart-container">
                    {lines_bar_chart_svg}
                </div>
            </div>
            
            <div class="card">
                <h2>Largest Files</h2>
                <div class="file-list">
                    {largest_files_html}
                </div>
            </div>
        </div>
        
        <footer>
            <p>Git Stats Infographic Generator • Analyzed from {os.path.abspath('.')} • Refresh to update</p>
        </footer>
    </div>
</body>
</html>"""
    
    return html

def main():
    """Main function to generate the stats report."""
    print("Scanning directory for code statistics...")
    stats = scan_directory()
    
    print("Generating HTML report...")
    html_content = generate_html_report(stats)
    
    with open("stats.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n✅ Report generated successfully!")
    print(f"📁 Total files: {stats['total_files']:,}")
    print(f"📜 Total lines: {stats['total_lines']:,}")
    print(f"📁 Directories: {stats['total_directories']:,}")
    print(f"🔍 Max depth: {stats['max_depth']}")
    print(f"\n📄 Output saved to: stats.html")
    print(f"\n✨ Open stats.html in your browser to view the infographic!")

if __name__ == "__main__":
    main()