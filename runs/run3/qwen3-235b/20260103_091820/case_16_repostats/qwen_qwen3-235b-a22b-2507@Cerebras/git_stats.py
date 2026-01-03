import os
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple

def scan_directory(root_dir: str) -> Dict:
    """Recursively scan directory and collect statistics."""
    file_stats = []
    total_lines = 0
    max_depth = 0
    
    root_path = Path(root_dir)
    
    for file_path in root_path.rglob('*'):
        # Calculate depth
        depth = len(file_path.relative_to(root_path).parts)
        max_depth = max(max_depth, depth)
        
        # Skip directories
        if file_path.is_dir():
            continue
            
        # Get file size
        try:
            file_size = file_path.stat().st_size
        except (OSError, PermissionError):
            file_size = 0
            
        # Count lines
        lines = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f)
            total_lines += lines
        except (UnicodeDecodeError, OSError, PermissionError):
            # Binary file or unreadable
            lines = 0
        
        # Get extension
        ext = file_path.suffix.lower()
        if not ext:  # Handle files like "Dockerfile", ".gitignore"
            ext = f"no_ext_{file_path.name.lower()}"
            
        file_stats.append({
            'path': str(file_path),
            'name': file_path.name,
            'ext': ext,
            'size': file_size,
            'lines': lines,
            'depth': depth
        })
    
    return {
        'files': file_stats,
        'total_lines': total_lines,
        'total_files': len(file_stats),
        'max_depth': max_depth
    }

def create_pie_chart(data: Counter, width: int = 400, height: int = 400) -> str:
    """Create SVG pie chart from extension data."""
    total = sum(data.values())
    if total == 0:
        return '<text x="50%" y="50%" text-anchor="middle" fill="white">No data</text>'
    
    # Vibrant colors
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
        "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2"
    ]
    
    radius = min(width, height) / 2 - 10
    cx, cy = width / 2, height / 2
    
    # Sort by count (descending)
    sorted_items = data.most_common()
    
    svg_parts = [
        f'<g transform="translate({cx},{cy})">'
    ]
    
    current_angle = 0
    for i, (label, count) in enumerate(sorted_items):
        angle = (count / total) * 2 * 3.14159
        color = colors[i % len(colors)]
        
        # Calculate end angle
        end_angle = current_angle + angle
        
        # Large arc flag
        large_arc = "1" if angle > 3.14159 else "0"
        
        # End point
        x1 = radius * 0.8 * -1 * (current_angle)
        y1 = radius * 0.8 * -1 * (current_angle)
        x2 = radius * -1 * (end_angle)
        y2 = radius * -1 * (end_angle)
        
        # SVG arc command
        x1 = radius * 0.8 * -1 * __import__('math').sin(current_angle)
        y1 = radius * 0.8 * -1 * __import__('math').cos(current_angle)
        x2 = radius * -1 * __import__('math').sin(end_angle)
        y2 = radius * -1 * __import__('math').cos(end_angle)
        
        path = f"M 0 0 L {x1} {y1} A {radius*0.8} {radius*0.8} 0 {large_arc} 1 {x2} {y2} Z"
        
        title = f"Title='{label}: {count} files ({count/total*100:.1f}%)'"
        
        svg_parts.append(f'<path d="{path}" fill="{color}" {title}/>')
        
        # Add label (positioned outside)
        label_angle = current_angle + angle / 2
        label_r = radius * 1.2
        lx = (label_r * -1 * __import__('math').sin(label_angle))
        ly = (label_r * -1 * __import__('math').cos(label_angle))
        
        if abs(label_angle - 3.14159/2) < 1.57:  # Right side
            text_anchor = "start"
            lx += 5
        else:  # Left side
            text_anchor = "end"
            lx -= 5
            
        svg_parts.append(f'<text x="{lx}" y="{ly}" fill="white" font-size="12" text-anchor="{text_anchor}">{label}</text>')
        
        current_angle = end_angle
    
    svg_parts.append('</g>')
    return '\n'.join(svg_parts)

def create_bar_chart(data: List[Tuple[str, int]], width: int = 600, height: int = 300) -> str:
    """Create SVG bar chart for largest files by lines."""
    if not data:
        return '<text x="50%" y="50%" text-anchor="middle" fill="white">No data</text>'
    
    # Sort by line count
    data.sort(key=lambda x: x[1], reverse=True)
    if len(data) > 10:
        data = data[:10]
    
    bar_padding = 10
    chart_height = height - 60  # Leave space for labels
    chart_width = width - 60
    max_value = max(count for _, count in data)
    
    if max_value == 0:
        return '<text x="50%" y="50%" text-anchor="middle" fill="white">No data</text>'
    
    bar_width = (chart_width - bar_padding * (len(data) + 1)) / len(data)
    
    svg_parts = ['<g transform="translate(50, 20)">']
    
    # Y-axis line
    svg_parts.append(f'<line x1="0" y1="0" x2="0" y2="{chart_height}" stroke="gray" stroke-opacity="0.5"/>')
    # X-axis line
    svg_parts.append(f'<line x1="0" y1="{chart_height}" x2="{chart_width}" y2="{chart_height}" stroke="gray" stroke-opacity="0.5"/>')
    
    # Add Y-axis ticks and labels
    for i in range(0, 6):
        y = chart_height - (i * chart_height / 5)
        value = int(max_value * i / 5)
        svg_parts.append(f'<line x1="-5" y1="{y}" x2="0" y2="{y}" stroke="gray" stroke-opacity="0.5"/>')
        svg_parts.append(f'<text x="-10" y="{y + 4}" fill="white" font-size="10" text-anchor="end">{value}</text>')
    
    # Bars
    x_pos = bar_padding
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", 
              "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]
    
    for i, (filename, count) in enumerate(data):
        bar_height = (count / max_value) * chart_height
        color = colors[i % len(colors)]
        
        # Create bar
        svg_parts.append(f'<rect x="{x_pos}" y="{chart_height - bar_height}" '
                        f'width="{bar_width}" height="{bar_height}" fill="{color}" '
                        f'title="{filename}: {count} lines"/>')
        
        # X-axis label (rotated)
        label_x = x_pos + bar_width / 2
        svg_parts.append(f'<text x="{label_x}" y="{chart_height + 15}" fill="white" '
                        f'font-size="10" text-anchor="middle" transform="rotate(45, {label_x}, {chart_height + 15})">'
                        f'{filename}</text>')
        
        x_pos += bar_width + bar_padding
    
    svg_parts.append('</g>')
    return '\n'.join(svg_parts)

def generate_html_report(stats: Dict) -> str:
    """Generate HTML infographic from stats."""
    
    # File count by extension
    ext_counter = Counter()
    for file in stats['files']:
        ext_counter[file['ext']] += 1
    
    # Filter out very rare extensions (< 1%)
    total_files = stats['total_files']
    common_exts = Counter()
    other_count = 0
    for ext, count in ext_counter.items():
        if count / total_files >= 0.01:  # 1% threshold
            common_exts[ext] = count
        else:
            other_count += count
    
    if other_count > 0:
        common_exts['other'] = other_count
    
    # Largest files by lines
    largest_files = [(f['name'], f['lines']) for f in sorted(stats['files'], key=lambda x: x['lines'], reverse=True)[:10]]
    
    # Directory distribution
    depth_counter = Counter(f['depth'] for f in stats['files'])
    
    html = f"""
<!DOCTYPE html>
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
            --accent1: #4ECDC4;
            --accent2: #FF6B6B;
            --accent3: #45B7D1;
            --border-radius: 12px;
            --box-shadow: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
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
            margin-bottom: 30px;
            padding: 20px;
        }}
        
        h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent1), var(--accent3), var(--accent2));
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
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 25px;
            box-shadow: var(--box-shadow);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h2 {{
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent3);
            color: var(--accent1);
            font-size: 1.5rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
            color: var(--accent2);
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        svg {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 400px;
        }}
        
        .file-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .file-list table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .file-list th,
        .file-list td {{
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .file-list th {{
            background-color: rgba(255, 255, 255, 0.05);
            color: var(--accent1);
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .file-list tr:hover {{
            background-color: rgba(255, 255, 255, 0.05);
        }}
        
        .extension-cell {{
            display: flex;
            align-items: center;
        }}
        
        .color-square {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
            margin-right: 8px;
            display: inline-block;
        }}
        
        footer {{
            text-align: center;
            margin-top: 30px;
            color: var(--text-secondary);
            padding: 20px;
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 2.2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A comprehensive analysis of your codebase structure and composition</p>
        </header>
        
        <div class="dashboard">
            <div class="card">
                <h2>Overview</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{stats['total_files']}</div>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats['total_lines']:,}</div>
                        <div class="stat-label">Lines of Code</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats['max_depth']}</div>
                        <div class="stat-label">Max Directory Depth</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(ext_counter)}</div>
                        <div class="stat-label">File Extensions</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>File Distribution by Type</h2>
                <div class="chart-container">
                    <svg viewBox="0 0 400 400">
                        {create_pie_chart(common_exts, 400, 400)}
                    </svg>
                </div>
            </div>
            
            <div class="card">
                <h2>Largest Files by Lines</h2>
                <div class="chart-container">
                    <svg viewBox="0 0 600 300">
                        {create_bar_chart(largest_files, 600, 300)}
                    </svg>
                </div>
            </div>
            
            <div class="card">
                <h2>File Extension Details</h2>
                <div class="file-list">
                    <table>
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Count</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Add extension details to table
    total = sum(ext_counter.values())
    sorted_exts = ext_counter.most_common()
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", 
              "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]
    
    for i, (ext, count) in enumerate(sorted_exts):
        if count / total < 0.005:  # Skip very small percentages
            continue
        percentage = count / total * 100
        color = colors[i % len(colors)]
        ext_display = ext if not ext.startswith('no_ext_') else ext[7:]
        html += f"""
                            <tr>
                                <td>
                                    <span class="extension-cell">
                                        <span class="color-square" style="background-color: {color};"></span>
                                        {ext_display}
                                    </span>
                                </td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
        """
    
    html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Generated by Git Stats Infographic Generator | Analyzed on <span id="date"></span></p>
        </footer>
    </div>
    
    <script>
        // Set current date
        document.getElementById('date').textContent = new Date().toLocaleDateString();
        
        // Add interactivity to charts (hover effects, tooltips)
        document.addEventListener('DOMContentLoaded', function() {
            // Tooltips for SVG elements
            const svgPaths = document.querySelectorAll('path');
            svgPaths.forEach(path => {
                const title = path.getAttribute('title');
                if (title) {
                    path.addEventListener('mouseenter', function(e) {
                        // Remove any existing tooltip
                        document.querySelectorAll('.svg-tooltip').forEach(t => t.remove());
                        
                        // Create tooltip
                        const tooltip = document.createElement('div');
                        tooltip.className = 'svg-tooltip';
                        tooltip.style.position = 'absolute';
                        tooltip.style.background = 'rgba(0,0,0,0.8)';
                        tooltip.style.color = 'white';
                        tooltip.style.padding = '8px 12px';
                        tooltip.style.borderRadius = '4px';
                        tooltip.style.fontSize = '12px';
                        tooltip.style.zIndex = '1000';
                        tooltip.style.pointerEvents = 'none';
                        tooltip.textContent = title;
                        
                        // Position tooltip
                        tooltip.style.left = (e.pageX + 10) + 'px';
                        tooltip.style.top = (e.pageY - 10) + 'px';
                        
                        document.body.appendChild(tooltip);
                    });
                    
                    path.addEventListener('mousemove', function(e) {
                        const tooltip = document.querySelector('.svg-tooltip');
                        if (tooltip) {
                            tooltip.style.left = (e.pageX + 10) + 'px';
                            tooltip.style.top = (e.pageY - 10) + 'px';
                        }
                    });
                    
                    path.addEventListener('mouseleave', function() {
                        document.querySelectorAll('.svg-tooltip').forEach(t => t.remove());
                    });
                }
            });
        });
    </script>
</body>
</html>
    """
    
    return html

def main():
    """Main function to run the analysis and generate report."""
    print("Scanning directory for code statistics...")
    
    # Scan current directory
    stats = scan_directory(".")
    
    # Generate HTML report
    html_content = generate_html_report(stats)
    
    # Write to file
    with open("stats.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Analysis complete!")
    print(f"Total files: {stats['total_files']:,}")
    print(f"Total lines of code: {stats['total_lines']:,}")
    print(f"Unique extensions: {len(Counter(f['ext'] for f in stats['files']))}")
    print(f"Maximum directory depth: {stats['max_depth']}")
    print(f"Report generated: stats.html")

if __name__ == "__main__":
    main()