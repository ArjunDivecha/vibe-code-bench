import os
import json
from collections import defaultdict
from pathlib import Path

def scan_directory(path):
    """Recursively scan directory and collect file statistics"""
    file_stats = defaultdict(int)
    extension_lines = defaultdict(int)
    file_sizes = []
    max_depth = 0
    
    for root, dirs, files in os.walk(path):
        # Calculate directory depth
        depth = root[len(path):].count(os.sep)
        max_depth = max(max_depth, depth)
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Get file extension
                ext = os.path.splitext(file)[1] or "No Extension"
                file_stats[ext] += 1
                
                # Count lines
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
                    extension_lines[ext] += lines
                
                # Store file size info for largest files
                size = os.path.getsize(file_path)
                file_sizes.append((file_path, size, lines))
            except (PermissionError, OSError):
                continue
    
    return dict(file_stats), dict(extension_lines), file_sizes, max_depth

def get_largest_files(file_sizes, n=5):
    """Get the n largest files by line count"""
    return sorted(file_sizes, key=lambda x: x[2], reverse=True)[:n]

def generate_html(file_stats, extension_lines, largest_files, max_depth, total_files, total_lines):
    """Generate the HTML infographic"""
    # Prepare data for pie chart
    extensions = list(file_stats.keys())
    counts = list(file_stats.values())
    
    # Prepare data for bar chart
    ext_labels = list(extension_lines.keys())
    line_counts = list(extension_lines.values())
    
    # Generate pie chart segments
    total_count = sum(counts)
    if total_count == 0:
        total_count = 1  # Prevent division by zero
    
    pie_segments = []
    cumulative_percent = 0
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFBE0B", "#FB5607",
        "#8338EC", "#3A86FF", "#06D6A0", "#118AB2", "#073B4C"
    ]
    
    for i, (ext, count) in enumerate(zip(extensions, counts)):
        percent = (count / total_count) * 100
        start_angle = cumulative_percent * 3.6
        end_angle = (cumulative_percent + percent) * 3.6
        color = colors[i % len(colors)]
        
        # Calculate coordinates for arc
        start_x = 50 + 40 * __import__('math').cos(__import__('math').radians(start_angle - 90))
        start_y = 50 + 40 * __import__('math').sin(__import__('math').radians(start_angle - 90))
        end_x = 50 + 40 * __import__('math').cos(__import__('math').radians(end_angle - 90))
        end_y = 50 + 40 * __import__('math').sin(__import__('math').radians(end_angle - 90))
        
        # Determine if large arc flag is needed
        large_arc = 1 if percent > 50 else 0
        
        path_data = f"M 50 50 L {start_x} {start_y} A 40 40 0 {large_arc} 1 {end_x} {end_y} Z"
        
        pie_segments.append({
            'path': path_data,
            'color': color,
            'percent': percent,
            'ext': ext
        })
        
        cumulative_percent += percent
    
    # Generate bar chart
    max_lines = max(line_counts) if line_counts else 1
    bars = []
    for i, (ext, lines) in enumerate(zip(ext_labels, line_counts)):
        height = (lines / max_lines) * 80 if max_lines > 0 else 0
        bars.append({
            'ext': ext,
            'lines': lines,
            'height': height,
            'color': colors[i % len(colors)]
        })
    
    # HTML template
    html_content = f"""<!DOCTYPE html>
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
            --accent: #bb86fc;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: var(--bg-secondary);
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: var(--accent);
            text-shadow: 0 0 10px rgba(187, 134, 252, 0.3);
        }}
        
        .subtitle {{
            font-size: 1.2rem;
            color: var(--text-secondary);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }}
        
        .stat-card h2 {{
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: var(--accent);
            display: flex;
            align-items: center;
        }}
        
        .stat-card h2 i {{
            margin-right: 10px;
        }}
        
        .chart-container {{
            height: 300px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .pie-chart {{
            width: 250px;
            height: 250px;
            position: relative;
        }}
        
        .bar-chart {{
            width: 100%;
            height: 250px;
            display: flex;
            align-items: end;
            gap: 15px;
            padding: 10px;
        }}
        
        .bar {{
            flex: 1;
            background: var(--accent);
            border-radius: 5px 5px 0 0;
            position: relative;
            min-width: 30px;
            transition: opacity 0.3s;
        }}
        
        .bar:hover {{
            opacity: 0.8;
        }}
        
        .bar-label {{
            position: absolute;
            bottom: -25px;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        .bar-value {{
            position: absolute;
            top: -25px;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 0.9rem;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9rem;
        }}
        
        .legend-color {{
            width: 15px;
            height: 15px;
            border-radius: 3px;
        }}
        
        .largest-files {{
            list-style: none;
        }}
        
        .largest-files li {{
            padding: 12px;
            margin-bottom: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
        }}
        
        .file-name {{
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-right: 10px;
        }}
        
        .file-size {{
            color: var(--accent);
            font-weight: bold;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .summary-item {{
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
        }}
        
        .summary-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent);
            margin: 10px 0;
        }}
        
        .summary-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
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
            <p class="subtitle">A visual analysis of your codebase</p>
        </header>
        
        <div class="summary-stats">
            <div class="summary-item">
                <div class="summary-label">Total Files</div>
                <div class="summary-value">{total_files}</div>
                <div class="summary-label">files</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Total Lines</div>
                <div class="summary-value">{total_lines:,}</div>
                <div class="summary-label">lines of code</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Directory Depth</div>
                <div class="summary-value">{max_depth}</div>
                <div class="summary-label">levels deep</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h2>File Types Distribution</h2>
                <div class="chart-container">
                    <div class="pie-chart">
                        <svg viewBox="0 0 100 100">
                            {''.join([f'<path d="{seg["path"]}" fill="{seg["color"]}"></path>' for seg in pie_segments])}
                            <circle cx="50" cy="50" r="15" fill="var(--bg-secondary)" />
                        </svg>
                    </div>
                </div>
                <div class="legend">
                    {''.join([f'<div class="legend-item"><div class="legend-color" style="background-color: {seg["color"]};"></div><span>{seg["ext"]} ({seg["percent"]:.1f}%)</span></div>' for seg in pie_segments])}
                </div>
            </div>
            
            <div class="stat-card">
                <h2>Lines of Code by File Type</h2>
                <div class="chart-container">
                    <div class="bar-chart">
                        {''.join([f'<div class="bar" style="height: {bar["height"]}%; background-color: {bar["color"]};"><div class="bar-value">{bar["lines"]:,}</div><div class="bar-label">{bar["ext"]}</div></div>' for bar in bars])}
                    </div>
                </div>
            </div>
            
            <div class="stat-card">
                <h2>Largest Files by Line Count</h2>
                <ul class="largest-files">
                    {''.join([f'<li><div class="file-name">{os.path.basename(file[0])}</div><div class="file-size">{file[2]:,} lines</div></li>' for file in largest_files])}
                </ul>
            </div>
        </div>
        
        <footer>
            <p>Generated with Python | Codebase Fingerprint Analyzer</p>
        </footer>
    </div>
</body>
</html>"""
    
    return html_content

def main():
    # Scan current directory
    file_stats, extension_lines, file_sizes, max_depth = scan_directory('.')
    
    # Calculate totals
    total_files = sum(file_stats.values())
    total_lines = sum(extension_lines.values())
    
    # Get largest files
    largest_files = get_largest_files(file_sizes)
    
    # Generate HTML
    html_content = generate_html(
        file_stats, 
        extension_lines, 
        largest_files, 
        max_depth, 
        total_files, 
        total_lines
    )
    
    # Write to file
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Codebase Fingerprint generated successfully!")
    print(f"Total files: {total_files}")
    print(f"Total lines: {total_lines:,}")
    print(f"Directory depth: {max_depth}")
    print("Output saved to: stats.html")

if __name__ == "__main__":
    main()