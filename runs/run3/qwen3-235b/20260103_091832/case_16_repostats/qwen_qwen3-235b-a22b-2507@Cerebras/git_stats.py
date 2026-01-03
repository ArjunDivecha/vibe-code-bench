import os
import json
from datetime import datetime
from collections import defaultdict, Counter

def scan_directory(root_dir):
    """Recursively scan directory and collect statistics."""
    file_stats = []
    total_lines = 0
    extension_count = Counter()
    extension_lines = defaultdict(int)
    
    max_depth = 0
    largest_files = []  # (path, size) tuples
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Calculate depth
        depth = dirpath[len(root_dir):].count(os.sep)
        max_depth = max(max_depth, depth)
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            
            # Skip the output HTML file if it exists
            if filename == 'stats.html':
                continue
                
            try:
                # Get file size
                stat = os.stat(filepath)
                size = stat.st_size
                
                # Store file info
                rel_path = os.path.relpath(filepath, root_dir)
                _, ext = os.path.splitext(filename)
                ext = ext.lower() or f".{filename.split('.')[-1]}"  # fallback for files like "Makefile"
                
                file_stats.append({
                    'path': rel_path,
                    'size': size,
                    'extension': ext,
                    'lines': 0  # will count below
                })
                
                extension_count[ext] += 1
                
                # Count lines and add to extension total
                lines = 0
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line_count, line in enumerate(f, 1):
                            if line.strip():  # only count non-empty lines
                                lines += 1
                                total_lines += 1
                    file_stats[-1]['lines'] = lines
                    extension_lines[ext] += lines
                except (UnicodeDecodeError, IOError):
                    # Skip binary files or unreadable files
                    file_stats.pop()  # remove from stats
                    extension_count[ext] -= 1
                    if extension_count[ext] == 0:
                        del extension_count[ext]
                
                # Track largest files (by size)
                largest_files.append((rel_path, size, lines))
                
            except (OSError, IOError):
                continue  # skip inaccessible files
    
    # Sort largest files by size (descending)
    largest_files.sort(key=lambda x: x[1], reverse=True)
    largest_files = largest_files[:10]  # top 10
    
    return {
        'file_stats': file_stats,
        'total_lines': total_lines,
        'extension_count': dict(extension_count),
        'extension_lines': dict(extension_lines),
        'max_depth': max_depth,
        'largest_files': largest_files,
        'total_files': len(file_stats)
    }

def generate_pie_chart(data, width=400, height=400):
    """Generate SVG pie chart for file extensions."""
    if not data:
        return '<text x="200" y="200" font-family="sans-serif" font-size="20" fill="#fff" text-anchor="middle">No data</text>'
    
    total = sum(data.values())
    if total == 0:
        return '<text x="200" y="200" font-family="sans-serif" font-size="20" fill="#fff" text-anchor="middle">No data</text>'
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
    ]
    
    cx, cy, r = width//2, height//2, min(width, height)//2 - 20
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
    
    current_angle = 0
    items = list(data.items())
    
    # Sort by count descending
    items.sort(key=lambda x: x[1], reverse=True)
    
    for i, (label, value) in enumerate(items):
        percentage = value / total
        color = colors[i % len(colors)]
        
        # Skip very small slices (<1%) to avoid rendering issues
        if percentage < 0.01:
            continue
            
        # Calculate angles
        next_angle = current_angle + percentage * 2 * 3.14159
        
        # Convert to radians for calculations
        x1 = cx + r * math.cos(current_angle)
        y1 = cy + r * math.sin(current_angle)
        x2 = cx + r * math.cos(next_angle)
        y2 = cy + r * math.sin(next_angle)
        
        # Large arc flag
        large_arc = 1 if percentage > 0.5 else 0
        
        # Create the path
        path = f'M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z'
        svg += f'  <path d="{path}" fill="{color}" stroke="#1a1a1a" stroke-width="1"/>\n'
        
        # Add a legend marker (will be positioned by CSS)
        svg += f'  <g class="legend-item" data-color="{color}" data-label="{label}" data-value="{value}"></g>'
        
        current_angle = next_angle
    
    svg += f'  <circle cx="{cx}" cy="{cy}" r="{r*0.6}" fill="#121212"/>'  # inner circle for donut
    svg += f'  <text x="{cx}" y="{cy}" font-family="sans-serif" font-size="24" fill="#fff" text-anchor="middle" dominant-baseline="middle" class="center-text">File Types</text>'
    svg += '</svg>'
    
    return svg

def generate_bar_chart(data, width=600, height=400):
    """Generate SVG horizontal bar chart for lines of code by extension."""
    if not data:
        return '<text x="300" y="200" font-family="sans-serif" font-size="20" fill="#fff" text-anchor="middle">No data</text>'
    
    # Sort by line count descending and take top 10
    items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if not items:
        return '<text x="300" y="200" font-family="sans-serif" font-size="20" fill="#fff" text-anchor="middle">No data</text>'
    
    max_lines = max(data.values())
    
    bar_height = 30
    spacing = 10
    chart_height = len(items) * (bar_height + spacing)
    chart_width = width - 150  # space for labels
    
    cx, cy = 150, (height - chart_height) // 2 + bar_height // 2
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
    
    for i, (label, lines) in enumerate(items):
        y = cy + i * (bar_height + spacing)
        bar_width = (lines / max_lines) * chart_width * 0.9
        color = colors[i % len(colors)]
        
        # Bar
        svg += f'  <rect x="{cx}" y="{y - bar_height//2}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="8" />\n'
        
        # Label
        svg += f'  <text x="{cx - 10}" y="{y}" font-family="sans-serif" font-size="14" fill="#aaa" text-anchor="end" dominant-baseline="middle">{label}</text>\n'
        
        # Value
        svg += f'  <text x="{cx + bar_width + 10}" y="{y}" font-family="sans-serif" font-size="14" fill="#fff" dominant-baseline="middle">{lines:,}</text>\n'
    
    # Title
    svg += f'  <text x="{width//2}" y="{cy - 40}" font-family="sans-serif" font-size="20" fill="#fff" text-anchor="middle">Lines of Code by Extension</text>'
    svg += '</svg>'
    
    return svg

def generate_html_report(stats, output_path):
    """Generate HTML report with embedded CSS and JS."""
    
    # Import math for use in the template
    import math
    
    # Prepare data for charts
    pie_data = stats['extension_count']
    bar_data = stats['extension_lines']
    
    # Generate charts
    pie_chart = generate_pie_chart(pie_data)
    bar_chart = generate_bar_chart(bar_data)
    
    # Format largest files
    largest_files_html = ""
    for path, size, lines in stats['largest_files']:
        largest_files_html += f"""
        <div class="file-item">
            <span class="file-path" title="{path}">{path}</span>
            <span class="file-meta">{size:,} bytes • {lines:,} lines</span>
        </div>
        """
    
    # Format summary stats
    summary_stats = f"""
    <div class="stat-card">
        <div class="stat-value">{stats['total_files']:,}</div>
        <div class="stat-label">Total Files</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats['total_lines']:,}</div>
        <div class="stat-label">Lines of Code</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats['max_depth']}</div>
        <div class="stat-label">Max Directory Depth</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{len(stats['extension_count'])}</div>
        <div class="stat-label">File Extensions</div>
    </div>
    """
    
    html_template = f"""<!DOCTYPE html>
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
            --shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
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
            min-height: 100vh;
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
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent1), var(--accent3), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 25px;
            text-align: center;
            box-shadow: var(--shadow);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-value {{
            font-size: 2.2rem;
            font-weight: bold;
            margin-bottom: 8px;
            color: var(--accent1);
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        @media (max-width: 1000px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-container {{
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 25px;
            box-shadow: var(--shadow);
        }}
        
        .chart-title {{
            text-align: center;
            margin-bottom: 20px;
            color: var(--text-primary);
            font-size: 1.5rem;
        }}
        
        .pie-container {{
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 20px;
            width: 100%;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            margin-right: 8px;
        }}
        
        .legend-label {{
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .legend-count {{
            color: var(--text-primary);
            font-family: monospace;
            margin-left: 8px;
        }}
        
        .files-container {{
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 25px;
            box-shadow: var(--shadow);
        }}
        
        .files-title {{
            margin-bottom: 20px;
            color: var(--text-primary);
            font-size: 1.5rem;
        }}
        
        .files-list {{
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #2a2a2a;
            font-size: 0.95rem;
        }}
        
        .file-item:last-child {{
            border-bottom: none;
        }}
        
        .file-path {{
            color: var(--accent3);
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 15px;
        }}
        
        .file-meta {{
            color: var(--text-secondary);
            white-space: nowrap;
            font-family: monospace;
            font-size: 0.9rem;
        }}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #1a1a1a;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #3a3a3a;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
        
        footer {{
            text-align: center;
            color: var(--text-secondary);
            padding: 20px;
            margin-top: 30px;
            font-size: 0.9rem;
        }}
        
        .generated-at {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A comprehensive analysis of your codebase structure and composition</p>
        </header>
        
        <div class="summary-stats">
            {summary_stats}
        </div>
        
        <div class="dashboard">
            <div class="chart-container">
                <h2 class="chart-title">File Type Distribution</h2>
                <div class="pie-container">
                    {pie_chart}
                    <div class="legend" id="pie-legend"></div>
                </div>
            </div>
            
            <div class="chart-container">
                <h2 class="chart-title">Lines of Code by Extension</h2>
                {bar_chart}
            </div>
        </div>
        
        <div class="files-container">
            <h2 class="files-title">Largest Files</h2>
            <div class="files-list">
                {largest_files_html}
            </div>
        </div>
        
        <footer>
            <p>Generated by Git Stats Infographic Generator</p>
            <p class="generated-at">Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </footer>
    </div>
    
    <script>
        // Generate legend for pie chart
        document.addEventListener('DOMContentLoaded', function() {{
            const legendContainer = document.getElementById('pie-legend');
            const legendItems = document.querySelectorAll('.legend-item');
            
            // Clear the SVG legend elements
            legendItems.forEach(item => item.remove());
            
            // Create proper legend elements
            const data = {json.dumps(stats['extension_count'])};
            const colors = [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
            ];
            
            // Sort by count descending
            const sortedEntries = Object.entries(data).sort((a, b) => b[1] - a[1]);
            
            sortedEntries.forEach(([label, count], index) => {{
                if (count / {sum(stats['extension_count'].values()) or 1} < 0.01) return; // Skip tiny slices
                
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                
                const colorBox = document.createElement('div');
                colorBox.className = 'legend-color';
                colorBox.style.backgroundColor = colors[index % colors.length];
                
                const labelSpan = document.createElement('span');
                labelSpan.className = 'legend-label';
                labelSpan.textContent = label;
                
                const countSpan = document.createElement('span');
                countSpan.className = 'legend-count';
                countSpan.textContent = count;
                
                legendItem.appendChild(colorBox);
                legendItem.appendChild(labelSpan);
                legendItem.appendChild(countSpan);
                
                legendContainer.appendChild(legendItem);
            }});
            
            // Add interactivity to charts
            const centerText = document.querySelector('.center-text');
            const totalFiles = {stats['total_files']};
            
            centerText.textContent = `${{Object.keys(data).length}} Types`;
            
            // Update center text on hover
            const chartContainer = document.querySelector('.pie-container');
            chartContainer.addEventListener('mouseenter', () => {{
                centerText.textContent = 'File Types';
            }});
            
            chartContainer.addEventListener('mouseleave', () => {{
                centerText.textContent = `${{Object.keys(data).length}} Types`;
            }});
        }});
    </script>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Statistics report generated: {output_path}")
    print(f"Files analyzed: {stats['total_files']}")
    print(f"Total lines of code: {stats['total_lines']:,}")
    print(f"File extensions detected: {len(stats['extension_count'])}")
    print(f"Max directory depth: {stats['max_depth']}")

def main():
    """Main function."""
    print("Scanning directory for code statistics...")
    root_dir = os.getcwd()
    
    stats = scan_directory(root_dir)
    
    output_path = os.path.join(root_dir, 'stats.html')
    generate_html_report(stats, output_path)

if __name__ == "__main__":
    main()