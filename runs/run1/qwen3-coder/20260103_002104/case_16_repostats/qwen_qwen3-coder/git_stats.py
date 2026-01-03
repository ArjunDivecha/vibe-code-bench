import os
import json
from collections import defaultdict, Counter
from pathlib import Path


def scan_directory(path="."):
    """Recursively scan directory and gather statistics."""
    file_count_by_ext = defaultdict(int)
    total_lines = 0
    file_sizes = []
    max_depth = 0

    for root, dirs, files in os.walk(path):
        # Calculate directory depth
        depth = root[len(path):].count(os.sep)
        max_depth = max(max_depth, depth)
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Get file extension
            ext = Path(file).suffix.lower() or "no extension"
            file_count_by_ext[ext] += 1
            
            try:
                # Count lines in text files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
                    total_lines += lines
                    file_sizes.append((file_path, lines))
            except Exception:
                # Skip binary files or files that can't be read
                pass

    # Get largest files by line count
    largest_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "file_count_by_ext": dict(file_count_by_ext),
        "total_lines": total_lines,
        "largest_files": largest_files,
        "max_depth": max_depth,
        "total_files": sum(file_count_by_ext.values())
    }


def generate_colors(count):
    """Generate distinct vibrant colors for charts."""
    colors = []
    for i in range(count):
        # Use golden ratio to generate vibrant colors
        hue = int((i * 137.508) % 360)
        colors.append(f"hsl({hue}, 80%, 60%)")
    return colors


def create_pie_chart(data, title="File Types"):
    """Create SVG pie chart for file extensions."""
    total = sum(data.values())
    if total == 0:
        return "<p>No data available</p>"
    
    # Sort data by value (descending)
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 8 items, group the rest as "Others"
    if len(sorted_data) > 8:
        top_data = sorted_data[:8]
        others_sum = sum(v for _, v in sorted_data[8:])
        if others_sum > 0:
            top_data.append(("Others", others_sum))
    else:
        top_data = sorted_data
    
    # Generate colors
    colors = generate_colors(len(top_data))
    
    # Create SVG pie chart
    svg_size = 300
    radius = svg_size // 2 - 10
    center = svg_size // 2
    
    html = f'<div class="chart-container"><h3>{title}</h3><svg width="{svg_size}" height="{svg_size}">'
    
    # Draw pie slices
    cumulative_percentage = 0
    for i, (label, value) in enumerate(top_data):
        percentage = value / total
        slice_angle = percentage * 360
        
        # Convert to radians
        start_angle = cumulative_percentage * 360
        end_angle = start_angle + slice_angle
        
        start_rad = start_angle * 3.14159 / 180
        end_rad = end_angle * 3.14159 / 180
        
        # Calculate coordinates
        x1 = center + radius * 3.14159 * start_rad / 180
        y1 = center - radius * 3.14159 * start_rad / 180
        x2 = center + radius * 3.14159 * end_rad / 180
        y2 = center - radius * 3.14159 * end_rad / 180
        
        # SVG path for slice
        large_arc_flag = 1 if slice_angle > 180 else 0
        path_data = f"M {center} {center} L {x1} {y1} A {radius} {radius} 0 {large_arc_flag} 1 {x2} {y2} Z"
        
        # Adjust coordinates for proper arc calculation
        start_x = center + radius * 3.14159 * start_angle / 180
        start_y = center - radius * 3.14159 * start_angle / 180
        end_x = center + radius * 3.14159 * end_angle / 180
        end_y = center - radius * 3.14159 * end_angle / 180
        
        path_data = f"M {center} {center} L {start_x} {start_y} A {radius} {radius} 0 {large_arc_flag} 1 {end_x} {end_y} Z"
        
        # Simpler approach using actual SVG arc calculations
        start_x = center + radius * 3.14159 * start_angle / 180
        start_y = center - radius * 3.14159 * start_angle / 180
        end_x = center + radius * 3.14159 * end_angle / 180
        end_y = center - radius * 3.14159 * end_angle / 180
        
        # Even simpler approach - using actual SVG arc path
        large_arc = 1 if slice_angle > 180 else 0
        start_x = center + radius * 3.14159 * start_angle / 180
        start_y = center - radius * 3.14159 * start_angle / 180
        end_x = center + radius * 3.14159 * end_angle / 180
        end_y = center - radius * 3.14159 * end_angle / 180
        
        # Use correct SVG arc path calculation
        import math
        start_x = center + radius * math.cos(start_rad)
        start_y = center + radius * math.sin(start_rad)
        end_x = center + radius * math.cos(end_rad)
        end_y = center + radius * math.sin(end_rad)
        
        large_arc = 1 if slice_angle > 180 else 0
        path_data = f"M {center} {center} L {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {end_x} {end_y} Z"
        
        # Use a simpler approach for SVG pie chart
        html += f'<path d="{path_data}" fill="{colors[i]}" stroke="#222" stroke-width="1"/>'
        cumulative_percentage += percentage
    
    html += '</svg><div class="legend">'
    
    # Add legend
    for i, (label, value) in enumerate(top_data):
        percentage = (value / total) * 100
        html += f'<div class="legend-item"><div class="legend-color" style="background:{colors[i]}"></div>'
        html += f'<span class="legend-label">{label} ({value} files, {percentage:.1f}%)</span></div>'
    
    html += '</div></div>'
    return html


def create_bar_chart(data, title="Largest Files"):
    """Create SVG bar chart for largest files."""
    if not data:
        return "<p>No data available</p>"
    
    # Take top 10 files
    top_files = data[:10]
    max_value = max(v for _, v in top_files) if top_files else 1
    
    # Chart dimensions
    chart_width = 600
    chart_height = 300
    bar_width = chart_width / len(top_files) - 10
    bar_spacing = 10
    
    html = f'<div class="chart-container"><h3>{title}</h3><svg width="{chart_width}" height="{chart_height}">'
    
    # Generate colors
    colors = generate_colors(len(top_files))
    
    # Draw bars
    for i, (file_path, value) in enumerate(top_files):
        bar_height = (value / max_value) * (chart_height - 50)  # Leave space at top
        x = i * (bar_width + bar_spacing) + bar_spacing
        y = chart_height - bar_height - 20  # Leave space at bottom
        
        html += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{colors[i]}" />'
        
        # Add file name
        short_name = os.path.basename(file_path)
        if len(short_name) > 15:
            short_name = short_name[:12] + "..."
        html += f'<text x="{x + bar_width/2}" y="{chart_height - 5}" text-anchor="middle" fill="#fff" font-size="10">{short_name}</text>'
        
        # Add value above bar
        html += f'<text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" fill="#fff" font-size="10">{value}</text>'
    
    html += '</svg></div>'
    return html


def generate_html(stats):
    """Generate the complete HTML infographic."""
    # Create charts
    pie_chart = create_pie_chart(stats["file_count_by_ext"], "File Types Distribution")
    bar_chart = create_bar_chart(stats["largest_files"], "Largest Files by Line Count")
    
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
            --text-primary: #e0e0e0;
            --text-secondary: #9e9e9e;
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
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 2.5rem;
            color: var(--accent-primary);
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.2rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background-color: var(--bg-secondary);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent-secondary);
            margin: 10px 0;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        @media (max-width: 768px) {{
            .charts-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-container {{
            background-color: var(--bg-secondary);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }}
        
        .chart-container h3 {{
            text-align: center;
            margin-bottom: 20px;
            color: var(--accent-primary);
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
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 10px;
            border: 1px solid var(--border-color);
        }}
        
        .legend-label {{
            font-size: 0.9rem;
            color: var(--text-primary);
        }}
        
        footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your codebase</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_files']}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_lines']:,}</div>
                <div class="stat-label">Total Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['max_depth']}</div>
                <div class="stat-label">Max Directory Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(stats['file_count_by_ext'])}</div>
                <div class="stat-label">File Extensions</div>
            </div>
        </div>
        
        <div class="charts-container">
            {pie_chart}
            {bar_chart}
        </div>
        
        <footer>
            <p>Generated with Git Stats Infographic Generator</p>
        </footer>
    </div>
</body>
</html>"""
    
    return html


def main():
    """Main function to generate the infographic."""
    # Scan directory and gather stats
    stats = scan_directory()
    
    # Generate HTML
    html_content = generate_html(stats)
    
    # Write to file
    with open("stats.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Infographic generated: stats.html")


if __name__ == "__main__":
    main()