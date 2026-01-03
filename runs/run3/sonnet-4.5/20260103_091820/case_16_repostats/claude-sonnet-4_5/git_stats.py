#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans directory and creates a beautiful HTML dashboard
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
import json

def get_file_stats(root_path="."):
    """Recursively scan directory and collect statistics"""
    stats = {
        'extensions': defaultdict(int),
        'lines_by_ext': defaultdict(int),
        'total_lines': 0,
        'total_files': 0,
        'largest_files': [],
        'max_depth': 0,
        'total_size': 0
    }
    
    # Common text file extensions to count lines
    text_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.rb', '.go', '.rs', '.php', '.html', '.css', '.scss', '.sass',
        '.json', '.xml', '.yaml', '.yml', '.md', '.txt', '.sh', '.bash',
        '.sql', '.r', '.m', '.swift', '.kt', '.scala', '.pl', '.lua'
    }
    
    file_sizes = []
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden directories and common ignore patterns
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
        
        # Calculate depth
        depth = dirpath.replace(root_path, '').count(os.sep)
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
                
            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower() or 'no_ext'
            
            stats['extensions'][ext] += 1
            stats['total_files'] += 1
            
            try:
                size = os.path.getsize(filepath)
                stats['total_size'] += size
                file_sizes.append((filepath, size))
                
                # Count lines for text files
                if ext in text_extensions:
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                            stats['lines_by_ext'][ext] += lines
                            stats['total_lines'] += lines
                    except:
                        pass
            except:
                pass
    
    # Get top 10 largest files
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    stats['largest_files'] = file_sizes[:10]
    
    return stats

def format_size(size):
    """Format size in bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def generate_html(stats):
    """Generate beautiful HTML infographic"""
    
    # Prepare data for charts
    ext_data = sorted(stats['extensions'].items(), key=lambda x: x[1], reverse=True)[:8]
    lines_data = sorted(stats['lines_by_ext'].items(), key=lambda x: x[1], reverse=True)[:8]
    
    # Colors for charts
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']
    
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            font-size: 3em;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .subtitle {{
            color: #a0a0a0;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .stat-label {{
            color: #a0a0a0;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #4ECDC4;
        }}
        
        .files-list {{
            background: rgba(255, 255, 255, 0.05);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            border-left: 3px solid #4ECDC4;
        }}
        
        .file-name {{
            color: #e0e0e0;
            font-family: monospace;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 15px;
        }}
        
        .file-size {{
            color: #FF6B6B;
            font-weight: bold;
            white-space: nowrap;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9em;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
        }}
        
        svg {{
            max-width: 100%;
            height: auto;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2em;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stat-value {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Codebase Fingerprint</h1>
            <p class="subtitle">A visual journey through your code</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Files</div>
                <div class="stat-value" style="color: #FF6B6B;">{stats['total_files']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Lines of Code</div>
                <div class="stat-value" style="color: #4ECDC4;">{stats['total_lines']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">File Types</div>
                <div class="stat-value" style="color: #45B7D1;">{len(stats['extensions'])}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Max Depth</div>
                <div class="stat-value" style="color: #FFA07A;">{stats['max_depth']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Size</div>
                <div class="stat-value" style="color: #98D8C8;">{format_size(stats['total_size'])}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h2 class="chart-title">📊 File Distribution</h2>
                <svg id="pieChart" viewBox="0 0 400 400" style="max-height: 400px;">
                </svg>
                <div class="legend" id="pieLegend"></div>
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">📈 Lines by File Type</h2>
                <svg id="barChart" viewBox="0 0 500 400" style="max-height: 400px;">
                </svg>
            </div>
        </div>
        
        <div class="files-list">
            <h2 class="chart-title">📁 Largest Files</h2>
            {''.join([f'<div class="file-item"><span class="file-name">{Path(f[0]).name}</span><span class="file-size">{format_size(f[1])}</span></div>' for f in stats['largest_files']])}
        </div>
    </div>
    
    <script>
        // Data
        const extData = {json.dumps([(ext, count) for ext, count in ext_data])};
        const linesData = {json.dumps([(ext, count) for ext, count in lines_data])};
        const colors = {json.dumps(colors)};
        
        // Draw Pie Chart
        function drawPieChart() {{
            const svg = document.getElementById('pieChart');
            const centerX = 200;
            const centerY = 200;
            const radius = 120;
            
            const total = extData.reduce((sum, item) => sum + item[1], 0);
            let currentAngle = -90;
            
            extData.forEach((item, index) => {{
                const [ext, count] = item;
                const percentage = count / total;
                const angle = percentage * 360;
                const endAngle = currentAngle + angle;
                
                // Draw slice
                const startRad = (currentAngle * Math.PI) / 180;
                const endRad = (endAngle * Math.PI) / 180;
                
                const x1 = centerX + radius * Math.cos(startRad);
                const y1 = centerY + radius * Math.sin(startRad);
                const x2 = centerX + radius * Math.cos(endRad);
                const y2 = centerY + radius * Math.sin(endRad);
                
                const largeArc = angle > 180 ? 1 : 0;
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', `M ${{centerX}},${{centerY}} L ${{x1}},${{y1}} A ${{radius}},${{radius}} 0 ${{largeArc}},1 ${{x2}},${{y2}} Z`);
                path.setAttribute('fill', colors[index % colors.length]);
                path.setAttribute('opacity', '0.9');
                path.setAttribute('stroke', '#1a1a2e');
                path.setAttribute('stroke-width', '2');
                
                // Hover effect
                path.addEventListener('mouseenter', function() {{
                    this.setAttribute('opacity', '1');
                    this.setAttribute('transform', `scale(1.05) translate(${{(centerX * 0.05) * Math.cos((startRad + endRad) / 2)}},${{(centerY * 0.05) * Math.sin((startRad + endRad) / 2)}})`);
                    this.style.transformOrigin = 'center';
                }});
                
                path.addEventListener('mouseleave', function() {{
                    this.setAttribute('opacity', '0.9');
                    this.setAttribute('transform', '');
                }});
                
                svg.appendChild(path);
                
                // Add label
                const midAngle = (startRad + endRad) / 2;
                const labelX = centerX + (radius * 0.7) * Math.cos(midAngle);
                const labelY = centerY + (radius * 0.7) * Math.sin(midAngle);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', labelX);
                text.setAttribute('y', labelY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dominant-baseline', 'middle');
                text.setAttribute('fill', '#fff');
                text.setAttribute('font-size', '12');
                text.setAttribute('font-weight', 'bold');
                text.textContent = `${{(percentage * 100).toFixed(1)}}%`;
                svg.appendChild(text);
                
                currentAngle = endAngle;
                
                // Add legend
                const legend = document.getElementById('pieLegend');
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                legendItem.innerHTML = `
                    <div class="legend-color" style="background: ${{colors[index % colors.length]}}"></div>
                    <span>${{ext}} (${{count}})</span>
                `;
                legend.appendChild(legendItem);
            }});
        }}
        
        // Draw Bar Chart
        function drawBarChart() {{
            const svg = document.getElementById('barChart');
            const padding = {{ top: 20, right: 20, bottom: 60, left: 80 }};
            const chartWidth = 500 - padding.left - padding.right;
            const chartHeight = 400 - padding.top - padding.bottom;
            
            if (linesData.length === 0) return;
            
            const maxLines = Math.max(...linesData.map(d => d[1]));
            const barWidth = chartWidth / linesData.length;
            
            linesData.forEach((item, index) => {{
                const [ext, lines] = item;
                const barHeight = (lines / maxLines) * chartHeight;
                const x = padding.left + index * barWidth;
                const y = padding.top + chartHeight - barHeight;
                
                // Draw bar
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x + barWidth * 0.1);
                rect.setAttribute('y', y);
                rect.setAttribute('width', barWidth * 0.8);
                rect.setAttribute('height', barHeight);
                rect.setAttribute('fill', colors[index % colors.length]);
                rect.setAttribute('opacity', '0.8');
                rect.setAttribute('rx', '4');
                
                rect.addEventListener('mouseenter', function() {{
                    this.setAttribute('opacity', '1');
                }});
                
                rect.addEventListener('mouseleave', function() {{
                    this.setAttribute('opacity', '0.8');
                }});
                
                svg.appendChild(rect);
                
                // Draw label
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', x + barWidth / 2);
                label.setAttribute('y', padding.top + chartHeight + 20);
                label.setAttribute('text-anchor', 'middle');
                label.setAttribute('fill', '#e0e0e0');
                label.setAttribute('font-size', '12');
                label.textContent = ext;
                svg.appendChild(label);
                
                // Draw value
                const value = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                value.setAttribute('x', x + barWidth / 2);
                value.setAttribute('y', y - 5);
                value.setAttribute('text-anchor', 'middle');
                value.setAttribute('fill', '#4ECDC4');
                value.setAttribute('font-size', '11');
                value.setAttribute('font-weight', 'bold');
                value.textContent = lines.toLocaleString();
                svg.appendChild(value);
            }});
            
            // Draw axes
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxis.setAttribute('x1', padding.left);
            xAxis.setAttribute('y1', padding.top + chartHeight);
            xAxis.setAttribute('x2', padding.left + chartWidth);
            xAxis.setAttribute('y2', padding.top + chartHeight);
            xAxis.setAttribute('stroke', '#666');
            xAxis.setAttribute('stroke-width', '2');
            svg.appendChild(xAxis);
            
            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxis.setAttribute('x1', padding.left);
            yAxis.setAttribute('y1', padding.top);
            yAxis.setAttribute('x2', padding.left);
            yAxis.setAttribute('y2', padding.top + chartHeight);
            yAxis.setAttribute('stroke', '#666');
            yAxis.setAttribute('stroke-width', '2');
            svg.appendChild(yAxis);
            
            // Y-axis label
            const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            yLabel.setAttribute('x', 20);
            yLabel.setAttribute('y', padding.top + chartHeight / 2);
            yLabel.setAttribute('text-anchor', 'middle');
            yLabel.setAttribute('fill', '#a0a0a0');
            yLabel.setAttribute('font-size', '12');
            yLabel.setAttribute('transform', `rotate(-90, 20, ${{padding.top + chartHeight / 2}})`);
            yLabel.textContent = 'Lines of Code';
            svg.appendChild(yLabel);
        }}
        
        // Initialize charts
        drawPieChart();
        drawBarChart();
    </script>
</body>
</html>'''
    
    return html

def main():
    print("🔍 Scanning codebase...")
    
    # Get statistics
    stats = get_file_stats(".")
    
    print(f"✓ Found {stats['total_files']} files")
    print(f"✓ Counted {stats['total_lines']:,} lines of code")
    print(f"✓ Analyzed {len(stats['extensions'])} file types")
    
    # Generate HTML
    print("\n📊 Generating infographic...")
    html = generate_html(stats)
    
    # Write to file
    output_file = "stats.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Created {output_file}")
    print(f"\n🌐 Open {output_file} in your browser to view the infographic!")

if __name__ == "__main__":
    main()