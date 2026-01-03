#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans current directory and generates a beautiful HTML infographic with codebase statistics
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

def scan_directory(path='.'):
    """Recursively scan directory and collect statistics"""
    stats = {
        'files_by_ext': Counter(),
        'total_lines': 0,
        'files': [],
        'dirs': [],
        'max_depth': 0
    }
    
    base_path = Path(path).resolve()
    
    for root, dirs, files in os.walk(path):
        # Calculate directory depth
        current_path = Path(root).resolve()
        rel_path = current_path.relative_to(base_path)
        depth = len(rel_path.parts) if str(rel_path) != '.' else 0
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        # Store directory info
        stats['dirs'].append({
            'path': str(rel_path),
            'depth': depth,
            'file_count': len(files)
        })
        
        # Process files
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            if not ext:
                ext = 'no_extension'
            
            # Count lines in text files
            lines = 0
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
            except:
                lines = 0
            
            stats['files_by_ext'][ext] += 1
            stats['total_lines'] += lines
            
            stats['files'].append({
                'name': file,
                'path': str(file_path.relative_to(base_path)),
                'ext': ext,
                'size': file_path.stat().st_size,
                'lines': lines
            })
    
    return stats

def generate_html(stats):
    """Generate HTML infographic with embedded CSS and JavaScript"""
    
    # Calculate top file extensions
    top_extensions = dict(stats['files_by_ext'].most_common(8))
    
    # Calculate top files by size and lines
    top_files_by_size = sorted(stats['files'], key=lambda x: x['size'], reverse=True)[:10]
    top_files_by_lines = sorted(stats['files'], key=lambda x: x['lines'], reverse=True)[:10]
    
    # Calculate pie chart data for file types
    pie_data = []
    for ext, count in top_extensions.items():
        pie_data.append({
            'label': ext if ext != 'no_extension' else 'No Extension',
            'value': count,
            'percentage': (count / sum(stats['files_by_ext'].values())) * 100
        })
    
    # Calculate bar chart data for directories
    dir_data = []
    for d in sorted(stats['dirs'], key=lambda x: x['file_count'], reverse=True)[:10]:
        dir_data.append({
            'name': d['path'][:30] + '...' if len(d['path']) > 30 else d['path'],
            'files': d['file_count']
        })
    
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e94560;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #e94560, #f27121);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header p {{
            font-size: 1.2em;
            color: #a8dadc;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .card h2 {{
            color: #f27121;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #e94560;
            padding-bottom: 10px;
        }}
        
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-item {{
            background: rgba(233, 69, 96, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(233, 69, 96, 0.3);
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #f27121;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #a8dadc;
            margin-top: 5px;
        }}
        
        .chart-container {{
            width: 100%;
            height: 300px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .file-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin-bottom: 5px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            border-left: 3px solid #e94560;
        }}
        
        .file-name {{
            font-weight: 500;
            color: #a8dadc;
        }}
        
        .file-size {{
            color: #f27121;
            font-weight: bold;
        }}
        
        .extension-tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
            background: #e94560;
            color: white;
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Codebase Fingerprint</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h2>📊 Overall Statistics</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{len(stats['files'])}</div>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(stats['dirs'])}</div>
                        <div class="stat-label">Directories</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats['total_lines']:,}</div>
                        <div class="stat-label">Total Lines</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats['max_depth']}</div>
                        <div class="stat-label">Max Depth</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🥧 File Types Distribution</h2>
                <div class="chart-container">
                    <svg id="pieChart" width="250" height="250" viewBox="0 0 250 250">
                        <!-- Pie chart will be drawn here by JavaScript -->
                    </svg>
                </div>
            </div>
            
            <div class="card">
                <h2>📁 Top Extensions</h2>
                <div class="file-list">
                    {''.join([f'''
                    <div class="file-item">
                        <div>
                            <span class="extension-tag">{ext if ext != "no_extension" else "No Ext"}</span>
                            <span class="file-name">{count} files</span>
                        </div>
                        <div class="file-size">{count/sum(stats['files_by_ext'].values())*100:.1f}%</div>
                    </div>
                    ''' for ext, count in top_extensions.items()])}
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Largest Files</h2>
                <div class="file-list">
                    {''.join([f'''
                    <div class="file-item">
                        <div class="file-name">{file['name']}</div>
                        <div class="file-size">{file['size']:,} bytes</div>
                    </div>
                    ''' for file in top_files_by_size[:8]])}
                </div>
            </div>
            
            <div class="card">
                <h2>📝 Files with Most Lines</h2>
                <div class="file-list">
                    {''.join([f'''
                    <div class="file-item">
                        <div class="file-name">{file['name']}</div>
                        <div class="file-size">{file['lines']:,} lines</div>
                    </div>
                    ''' for file in top_files_by_lines[:8]])}
                </div>
            </div>
            
            <div class="card">
                <h2>📂 Directory File Count</h2>
                <div class="file-list">
                    {''.join([f'''
                    <div class="file-item">
                        <div class="file-name">{d['name']}</div>
                        <div class="file-size">{d['files']} files</div>
                    </div>
                    ''' for d in dir_data])}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Pie chart data
        const pieData = {json.dumps(pie_data)};
        
        // Draw pie chart
        function drawPieChart() {{
            const svg = document.getElementById('pieChart');
            const centerX = 125;
            const centerY = 125;
            const radius = 100;
            
            let currentAngle = 0;
            const colors = ['#e94560', '#f27121', '#a8dadc', '#457b9d', '#1d3557', '#f1faee', '#e63946', '#a1c181'];
            
            pieData.forEach((item, index) => {{
                const angle = (item.percentage / 100) * 360;
                const startAngle = currentAngle;
                const endAngle = currentAngle + angle;
                
                const x1 = centerX + radius * Math.cos((startAngle - 90) * Math.PI / 180);
                const y1 = centerY + radius * Math.sin((startAngle - 90) * Math.PI / 180);
                const x2 = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180);
                const y2 = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180);
                
                const largeArcFlag = angle > 180 ? 1 : 0;
                
                const pathData = [
                    `M ${centerX} ${centerY}`,
                    `L ${x1} ${y1}`,
                    `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                    'Z'
                ].join(' ');
                
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', pathData);
                path.setAttribute('fill', colors[index % colors.length]);
                path.setAttribute('stroke', '#1a1a2e');
                path.setAttribute('stroke-width', '2');
                path.style.transition = 'opacity 0.3s ease';
                
                // Add hover effect
                path.addEventListener('mouseenter', function() {{
                    this.style.opacity = '0.8';
                }});
                
                path.addEventListener('mouseleave', function() {{
                    this.style.opacity = '1';
                }});
                
                svg.appendChild(path);
                
                // Add label
                const labelAngle = startAngle + angle / 2;
                const labelRadius = radius * 0.7;
                const labelX = centerX + labelRadius * Math.cos((labelAngle - 90) * Math.PI / 180);
                const labelY = centerY + labelRadius * Math.sin((labelAngle - 90) * Math.PI / 180);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', labelX);
                text.setAttribute('y', labelY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dominant-baseline', 'middle');
                text.setAttribute('fill', '#f1faee');
                text.setAttribute('font-size', '12');
                text.setAttribute('font-weight', 'bold');
                text.textContent = item.label;
                
                svg.appendChild(text);
                
                currentAngle += angle;
            }});
        }}
        
        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            drawPieChart();
        }});
    </script>
</body>
</html>'''
    
    return html

def main():
    """Main function to generate the stats infographic"""
    print("🔍 Scanning directory...")
    stats = scan_directory()
    
    print("📊 Generating HTML infographic...")
    html_content = generate_html(stats)
    
    # Write HTML file
    with open('stats.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Stats infographic generated: stats.html")
    print(f"📈 Found {len(stats['files'])} files across {len(stats['dirs'])} directories")
    print(f"📝 Total lines of code: {stats['total_lines']:,}")

if __name__ == "__main__":
    main()