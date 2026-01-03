#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans the current directory and generates a beautiful HTML infographic.
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def scan_directory(root_path: str) -> Tuple[Dict[str, int], Dict[str, int], List[Tuple[str, int]], int]:
    """
    Recursively scan directory and collect statistics.
    
    Returns:
        - ext_counts: File count by extension
        - line_counts: Lines of code by extension
        - largest_files: List of (path, size) tuples for largest files
        - max_depth: Maximum directory depth
    """
    ext_counts = defaultdict(int)
    line_counts = defaultdict(int)
    all_files = []
    max_depth = 0
    
    # Skip common non-code directories
    skip_dirs = {
        '.git', '.svn', '__pycache__', 'node_modules', '.venv', 'venv',
        'env', '.idea', '.vscode', 'dist', 'build', 'target', 'bin', 'obj'
    }
    
    # Binary file extensions to skip for line counting
    binary_extensions = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', '.dat',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.pdf',
        '.zip', '.tar', '.gz', '.7z', '.rar', '.mp3', '.mp4', '.avi', '.mov',
        '.woff', '.woff2', '.ttf', '.eot', '.class', '.jar', '.war'
    }
    
    root_path = Path(root_path).resolve()
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden and common non-code directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith('.')]
        
        # Calculate depth
        rel_path = Path(dirpath).relative_to(root_path)
        depth = len(rel_path.parts) if str(rel_path) != '.' else 0
        max_depth = max(max_depth, depth)
        
        for filename in filenames:
            filepath = Path(dirpath) / filename
            
            # Skip hidden files
            if filename.startswith('.'):
                continue
                
            # Get extension
            ext = filepath.suffix.lower()
            if not ext:
                ext = '(no extension)'
            
            # Count files
            ext_counts[ext] += 1
            
            # Get file size
            try:
                size = filepath.stat().st_size
                all_files.append((str(filepath.relative_to(root_path)), size))
            except (OSError, PermissionError):
                pass
            
            # Count lines (skip binary files)
            if ext not in binary_extensions:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        line_counts[ext] += lines
                except (OSError, PermissionError, UnicodeDecodeError):
                    pass
    
    # Get top 10 largest files
    largest_files = sorted(all_files, key=lambda x: x[1], reverse=True)[:10]
    
    return dict(ext_counts), dict(line_counts), largest_files, max_depth


def generate_pie_chart(data: Dict[str, int], title: str) -> str:
    """Generate SVG pie chart."""
    if not data:
        return '<div class="chart-placeholder">No data available</div>'
    
    total = sum(data.values())
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9'
    ]
    
    # Sort by count and take top 8, group rest as "Other"
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_items) > 8:
        top_items = sorted_items[:7]
        other_count = sum(item[1] for item in sorted_items[7:])
        top_items.append(('Other', other_count))
        sorted_items = top_items
    
    # Generate SVG paths
    paths = []
    current_angle = -90  # Start from top
    
    for i, (label, count) in enumerate(sorted_items):
        percentage = count / total
        angle = percentage * 360
        color = colors[i % len(colors)]
        
        # Calculate path
        if percentage >= 0.999:  # Full circle
            path = f'<circle cx="100" cy="100" r="80" fill="{color}" />'
        else:
            start_rad = (current_angle * 3.14159) / 180
            end_rad = ((current_angle + angle) * 3.14159) / 180
            
            x1 = 100 + 80 * (3.14159/180 - start_rad) if start_rad < 0 else 100 + 80 * (start_rad if start_rad < 90 else 180-start_rad if start_rad < 180 else start_rad-180 if start_rad < 270 else 360-start_rad)
            y1 = 100 + 80 * (start_rad if start_rad < 90 else 180-start_rad if start_rad < 180 else start_rad-180 if start_rad < 270 else 360-start_rad)
            
            # Use trigonometry for proper coordinates
            x1 = 100 + 80 * (3.14159/180 * (90 + current_angle) if current_angle >= -90 else 0)
            
            # Simpler approach using sin/cos
            start_x = 100 + 80 * (3.14159/180 * (current_angle + 90) if False else 0)
            
            # Proper calculation
            def get_coords(angle_deg):
                rad = (angle_deg - 90) * 3.14159 / 180
                return 100 + 80 * (rad if False else 0), 100 + 80 * (rad if False else 0)
            
            def get_xy(angle_deg):
                rad = angle_deg * 3.14159 / 180
                return 100 + 80 * rad, 100 - 80 * (1 - rad) if False else 100 + 80 * rad
            
            # Actually correct calculation
            start_rad = current_angle * 3.14159 / 180
            end_rad = (current_angle + angle) * 3.14159 / 180
            
            sx = 100 + 80 * (3.14159/180 * (current_angle) if False else 0)
            
            # Final correct version
            import math
            sx = 100 + 80 * math.cos(math.radians(current_angle - 90))
            sy = 100 + 80 * math.sin(math.radians(current_angle - 90))
            ex = 100 + 80 * math.cos(math.radians(current_angle + angle - 90))
            ey = 100 + 80 * math.sin(math.radians(current_angle + angle - 90))
            
            large_arc = 1 if angle > 180 else 0
            
            if angle >= 359.9:
                path = f'<circle cx="100" cy="100" r="80" fill="{color}" />'
            else:
                path = f'<path d="M100,100 L{sx},{sy} A80,80 0 {large_arc},1 {ex},{ey} Z" fill="{color}" />'
        
        paths.append(f'<g class="slice" data-label="{label}" data-count="{count}" data-percentage="{percentage:.1%}">{path}</g>')
        current_angle += angle
    
    # Legend
    legend_items = []
    for i, (label, count) in enumerate(sorted_items):
        color = colors[i % len(colors)]
        legend_items.append(f'''
            <div class="legend-item">
                <span class="legend-color" style="background-color: {color}"></span>
                <span class="legend-label">{label}</span>
                <span class="legend-value">{count} ({count/total:.1%})</span>
            </div>
        ''')
    
    return f'''
        <div class="chart-container">
            <h3>{title}</h3>
            <div class="pie-wrapper">
                <svg viewBox="0 0 200 200" class="pie-chart">
                    {"".join(paths)}
                </svg>
                <div class="pie-tooltip" id="pie-tooltip"></div>
            </div>
            <div class="legend">
                {"".join(legend_items)}
            </div>
        </div>
    '''


def generate_bar_chart(data: Dict[str, int], title: str) -> str:
    """Generate SVG bar chart."""
    if not data:
        return '<div class="chart-placeholder">No data available</div>'
    
    # Sort and take top 10
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    
    max_value = max(item[1] for item in sorted_items)
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    bars = []
    chart_height = 200
    chart_width = 500
    bar_width = (chart_width - 60) / len(sorted_items)
    max_bar_height = chart_height - 40
    
    for i, (label, count) in enumerate(sorted_items):
        bar_height = (count / max_value) * max_bar_height
        x = 40 + i * bar_width
        y = chart_height - 20 - bar_height
        color = colors[i % len(colors)]
        
        # Truncate long labels
        display_label = label[:10] + '...' if len(label) > 10 else label
        
        bars.append(f'''
            <g class="bar-group" data-label="{label}" data-count="{count:,}">
                <rect class="bar" x="{x + 5}" y="{y}" width="{bar_width - 10}" height="{bar_height}" fill="{color}" rx="4">
                    <animate attributeName="height" from="0" to="{bar_height}" dur="0.5s" fill="freeze" />
                    <animate attributeName="y" from="{chart_height - 20}" to="{y}" dur="0.5s" fill="freeze" />
                </rect>
                <text class="bar-label" x="{x + bar_width/2}" y="{chart_height - 5}" text-anchor="middle">{display_label}</text>
                <text class="bar-value" x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle">{count:,}</text>
            </g>
        ''')
    
    return f'''
        <div class="chart-container">
            <h3>{title}</h3>
            <svg viewBox="0 0 {chart_width} {chart_height}" class="bar-chart">
                {"".join(bars)}
            </svg>
        </div>
    '''


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def generate_html(ext_counts: Dict[str, int], line_counts: Dict[str, int], 
                  largest_files: List[Tuple[str, int]], max_depth: int) -> str:
    """Generate the complete HTML infographic."""
    
    total_files = sum(ext_counts.values())
    total_lines = sum(line_counts.values())
    total_size = sum(size for _, size in largest_files)
    
    pie_chart = generate_pie_chart(ext_counts, "Files by Type")
    bar_chart = generate_bar_chart(line_counts, "Lines of Code by Type")
    
    # Generate largest files list
    largest_files_html = []
    for i, (filepath, size) in enumerate(largest_files):
        largest_files_html.append(f'''
            <div class="file-item">
                <span class="file-rank">#{i + 1}</span>
                <span class="file-path" title="{filepath}">{filepath}</span>
                <span class="file-size">{format_size(size)}</span>
            </div>
        ''')
    
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
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
            padding: 40px 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: #8892b0;
            font-size: 1.1rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4ECDC4, #44A08D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #8892b0;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        @media (max-width: 768px) {{
            .charts-section {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-container h3 {{
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #e0e0e0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .chart-container h3::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 2px;
        }}
        
        .pie-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            flex-wrap: wrap;
        }}
        
        .pie-chart {{
            width: 250px;
            height: 250px;
            filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.3));
        }}
        
        .slice {{
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        
        .slice:hover {{
            transform: scale(1.05);
            transform-origin: center;
        }}
        
        .pie-tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.9rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 100;
        }}
        
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-width: 200px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            transition: background 0.2s ease;
        }}
        
        .legend-item:hover {{
            background: rgba(255, 255, 255, 0.08);
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            flex-shrink: 0;
        }}
        
        .legend-label {{
            flex: 1;
            font-size: 0.9rem;
        }}
        
        .legend-value {{
            font-weight: 600;
            font-size: 0.85rem;
            color: #8892b0;
        }}
        
        .bar-chart {{
            width: 100%;
            height: auto;
            max-height: 250px;
        }}
        
        .bar {{
            transition: opacity 0.2s ease;
            cursor: pointer;
        }}
        
        .bar:hover {{
            opacity: 0.8;
        }}
        
        .bar-label {{
            fill: #8892b0;
            font-size: 11px;
        }}
        
        .bar-value {{
            fill: #e0e0e0;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .files-section {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .files-section h3 {{
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #e0e0e0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .files-section h3::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(135deg, #f093fb, #f5576c);
            border-radius: 2px;
        }}
        
        .file-item {{
            display: grid;
            grid-template-columns: 40px 1fr 100px;
            gap: 15px;
            align-items: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            margin-bottom: 10px;
            transition: background 0.2s ease;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.08);
        }}
        
        .file-rank {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.1rem;
        }}
        
        .file-path {{
            color: #e0e0e0;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .file-size {{
            text-align: right;
            font-weight: 600;
            color: #4ECDC4;
        }}
        
        .chart-placeholder {{
            text-align: center;
            padding: 40px;
            color: #8892b0;
            font-style: italic;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: #8892b0;
            font-size: 0.9rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 30px;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .stat-card {{
            animation: fadeIn 0.6s ease forwards;
        }}
        
        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.4s; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your project structure</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_files:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_lines:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{max_depth}</div>
                <div class="stat-label">Max Directory Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(ext_counts)}</div>
                <div class="stat-label">File Types</div>
            </div>
        </div>
        
        <div class="charts-section">
            {pie_chart}
            {bar_chart}
        </div>
        
        <div class="files-section">
            <h3>Largest Files</h3>
            {"".join(largest_files_html) if largest_files else '<p class="chart-placeholder">No files found</p>'}
        </div>
        
        <footer>
            Generated with Git Stats Infographic Generator
        </footer>
    </div>
    
    <script>
        // Pie chart tooltip interactions
        const slices = document.querySelectorAll('.slice');
        const tooltip = document.getElementById('pie-tooltip');
        
        slices.forEach(slice => {{
            slice.addEventListener('mouseenter', (e) => {{
                const label = slice.dataset.label;
                const count = parseInt(slice.dataset.count);
                const percentage = slice.dataset.percentage;
                
                tooltip.innerHTML = `<strong>${{label}}</strong><br>${{count.toLocaleString()}} files (${{percentage}})`;
                tooltip.style.opacity = '1';
            }});
            
            slice.addEventListener('mousemove', (e) => {{
                tooltip.style.left = e.pageX + 10 + 'px';
                tooltip.style.top = e.pageY + 10 + 'px';
            }});
            
            slice.addEventListener('mouseleave', () => {{
                tooltip.style.opacity = '0';
            }});
        }});
        
        // Bar chart interactions
        const barGroups = document.querySelectorAll('.bar-group');
        
        barGroups.forEach(group => {{
            const bar = group.querySelector('.bar');
            const value = group.querySelector('.bar-value');
            
            bar.addEventListener('mouseenter', () => {{
                value.style.opacity = '1';
            }});
            
            bar.addEventListener('mouseleave', () => {{
                value.style.opacity = '0.7';
            }});
        }});
        
        // Animate stats on load
        const statValues = document.querySelectorAll('.stat-value');
        statValues.forEach(stat => {{
            const finalValue = stat.textContent;
            const isNumeric = !isNaN(parseInt(finalValue.replace(/,/g, '')));
            
            if (isNumeric) {{
                const target = parseInt(finalValue.replace(/,/g, ''));
                let current = 0;
                const increment = target / 50;
                const duration = 1000;
                const stepTime = duration / 50;
                
                const counter = setInterval(() => {{
                    current += increment;
                    if (current >= target) {{
                        current = target;
                        clearInterval(counter);
                    }}
                    stat.textContent = Math.floor(current).toLocaleString();
                }}, stepTime);
            }}
        }});
    </script>
</body>
</html>'''
    
    return html


def main():
    """Main entry point."""
    print("🔍 Scanning directory...")
    
    # Get current directory or use provided path
    scan_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    if not os.path.exists(scan_path):
        print(f"❌ Error: Directory '{scan_path}' does not exist.")
        sys.exit(1)
    
    # Scan and collect statistics
    ext_counts, line_counts, largest_files, max_depth = scan_directory(scan_path)
    
    print(f"✅ Found {sum(ext_counts.values())} files")
    print(f"📊 Calculated {sum(line_counts.values())} lines of code")
    print(f"📁 Maximum depth: {max_depth}")
    
    # Generate HTML
    print("🎨 Generating infographic...")
    html = generate_html(ext_counts, line_counts, largest_files, max_depth)
    
    # Write to file
    output_path = os.path.join(scan_path, "stats.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✨ Done! Open {output_path} to view your Codebase Fingerprint")


if __name__ == "__main__":
    main()