x1 = cx + radius * 0.7 * cos(start_rad)
            y1 = cy + radius * 0.7 * sin(start_rad)
            x2 = cx + radius * 0.7 * cos(end_rad)
            y2 = cy + radius * 0.7 * sin(end_rad)
            
            large_arc = 1 if angle > 180 else 0
            
            path = f"M {cx} {cy} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z"
            
            svg += f'<path d="{path}" fill="{colors[i]}" filter="url(#glow)" stroke="#1A202C" stroke-width="2"/>'
            
            # Add percentage label
            mid_angle = (start_angle + end_angle) / 2
            label_x = cx + (radius + 30) * cos((mid_angle - 90) * 3.14159 / 180)
            label_y = cy + (radius + 30) * sin((mid_angle - 90) * 3.14159 / 180)
            percentage = round((value / total) * 100)
            
            svg += f'<text x="{label_x}" y="{label_y}" text-anchor="middle" fill="#E2E8F0" font-size="12" font-weight="bold">{label} ({percentage}%)</text>'
            
            start_angle = end_angle
        
        svg += '</svg>'
        return svg
    
    def create_bar_chart_svg(self, data, title):
        """Create SVG bar chart"""
        max_value = max(data.values())
        colors = self.generate_colors(len(data))
        
        svg = f'<svg viewBox="0 0 500 300" xmlns="http://www.w3.org/2000/svg">'
        svg += '<defs><filter id="barGlow"><feGaussianBlur stdDeviation="2" result="coloredBlur"/>'
        svg += '<feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
        
        # Add title
        svg += f'<text x="250" y="20" text-anchor="middle" fill="#E2E8F0" font-size="16" font-weight="bold">{title}</text>'
        
        bar_width = 400 / len(data)
        max_height = 200
        
        for i, (label, value) in enumerate(data.items()):
            x = 50 + i * bar_width
            height = (value / max_value) * max_height
            y = 250 - height
            
            # Draw bar
            svg += f'<rect x="{x + 5}" y="{y}" width="{bar_width - 10}" height="{height}" fill="{colors[i]}" filter="url(#barGlow)" stroke="#1A202C" stroke-width="1"/>'
            
            # Add value label
            svg += f'<text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" fill="#E2E8F0" font-size="10">{value}</text>'
            
            # Add label
            label_text = label[:8] + '...' if len(label) > 8 else label
            svg += f'<text x="{x + bar_width/2}" y="270" text-anchor="middle" fill="#A0AEC0" font-size="9">{label_text}</text>'
        
        svg += '</svg>'
        return from math import cos, sin
    
    def generate_html_report(self):
        """Generate complete HTML report"""
        top_ext = self.get_top_extensions()
        largest_files = self.get_largest_files()
        
        html_content = f'''<!DOCTYPE html>
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
            background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%);
            color: #E2E8F0;
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
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header h1 {{
            font-size: 3rem;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2rem;
            color: #A0AEC0;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
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
            color: #4ECDC4;
            margin-bottom: 20px;
            font-size: 1.5rem;
            text-align: center;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 20px;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(255, 107, 107, 0.2);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #FF6B6B;
            display: block;
        }}
        
        .stat-label {{
            color: #A0AEC0;
            font-size: 0.9rem;
            margin-top: 5px;
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
            background: rgba(255, 255, 255, 0.02);
            border-radius: 5px;
            border-left: 3px solid #4ECDC4;
        }}
        
        .file-name {{
            font-weight: 500;
            color: #E2E8F0;
        }}
        
        .file-stats {{
            color: #A0AEC0;
            font-size: 0.9rem;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 350px;
        }}
        
        .ext-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 10px;
        }}
        
        .ext-item {{
            text-align: center;
            padding: 10px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .ext-count {{
            font-size: 1.2rem;
            font-weight: bold;
            color: #45B7D1;
        }}
        
        .ext-name {{
            color: #A0AEC0;
            font-size: 0.8rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Codebase Fingerprint</h1>
            <p>Comprehensive analysis of your repository structure and statistics</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-number">{self.total_files}</span>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-item">
                <span class="stat-number">{self.total_lines:,}</span>
                <div class="stat-label">Total Lines</div>
            </div>
            <div class="stat-item">
                <span class="stat-number">{len(self.file_stats)}</span>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-item">
                <span class="stat-number">{self.max_depth}</span>
                <div class="stat-label">Max Depth</div>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h2>📊 File Type Distribution</h2>
                <div class="chart-container">
                    {self.create_pie_chart_svg(top_ext, "File Types")}
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Lines of Code by Extension</h2>
                <div class="chart-container">
                    {self.create_bar_chart_svg(dict(list(self.line_counts.items())[:8]), "LOC by Extension")}
                </div>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h2>🔍 Top Extensions</h2>
                <div class="ext-list">
                    {''.join([f'<div class="ext-item"><div class="ext-count">{count}</div><div class="ext-name">{ext if ext else "no_ext"}</div></div>' for ext, count in list(top_ext.items())[:12]])}
                </div>
            </div>
            
            <div class="card">
                <h2>🏆 Largest Files</h2>
                <div class="file-list">
                    {''.join([f'<div class="file-item"><div class="file-name">{html.escape(file["name"])}</div><div class="file-stats">{file["lines"]:,} lines</div></div>' for file in largest_files[:10]])}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Add some interactive features
        document.addEventListener('DOMContentLoaded', function() {{
            // Animate numbers on load
            const statNumbers = document.querySelectorAll('.stat-number');
            statNumbers.forEach(num => {{
                const finalValue = parseInt(num.textContent.replace(/,/g, ''));
                let currentValue = 0;
                const increment = finalValue / 50;
                const timer = setInterval(() => {{
                    currentValue += increment;
                    if (currentValue >= finalValue) {{
                        currentValue = finalValue;
                        clearInterval(timer);
                    }}
                    num.textContent = Math.floor(currentValue).toLocaleString();
                }}, 20);
            }});
            
            // Add click to copy functionality for file names
            const fileItems = document.querySelectorAll('.file-item');
            fileItems.forEach(item => {{
                item.addEventListener('click', function() {{
                    const fileName = this.querySelector('.file-name').textContent;
                    navigator.clipboard.writeText(fileName).then(() => {{
                        const original = this.style.backgroundColor;
                        this.style.backgroundColor = 'rgba(76, 237, 196, 0.2)';
                        setTimeout(() => {{
                            this.style.backgroundColor = original;
                        }}, 1000);
                    }});
                }});
            }});
        }});
    </script>
</body>
</html>'''
        
        return html_content
    
    def generate_report(self, output_file='stats.html'):
        """Generate and save the HTML report"""
        self.scan_directory()
        html_content = self.generate_html_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Report generated successfully: {output_file}")
        print(f"📊 Total files analyzed: {self.total_files}")
        print(f"📈 Total lines of code: {self.total_lines:,}")
        print(f"🔍 File types found: {len(self.file_stats)}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Git Stats Infographic Generator')
    parser.add_argument('--path', default='.', help='Directory path to analyze (default: current directory)')
    parser.add_argument('--output', default='stats.html', help='Output HTML file (default: stats.html)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"❌ Error: Directory '{args.path}' does not exist")
        return 1
    
    generator = GitStatsGenerator()
    generator.generate_report(args.output)
    
    return 0

if __name__ == '__main__':
    exit(main())