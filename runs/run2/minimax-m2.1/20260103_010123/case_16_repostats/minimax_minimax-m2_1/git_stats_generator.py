#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful HTML dashboard showing codebase statistics.
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
import html

# Configuration - what file types to analyze
CODE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'React',
    '.tsx': 'React TS',
    '.vue': 'Vue',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.less': 'LESS',
    '.json': 'JSON',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.md': 'Markdown',
    '.txt': 'Text',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.sql': 'SQL',
    '.r': 'R',
    '.lua': 'Lua',
    '.perl': 'Perl',
    '.ex': 'Elixir',
    '.erl': 'Erlang',
    '.clj': 'Clojure',
    '.ml': 'OCaml',
    '.fs': 'F#',
    '.nim': 'Nim',
    '.dart': 'Dart',
    '.m': 'Objective-C',
    '.pl': 'Prolog',
    '.hs': 'Haskell',
    '.jl': 'Julia',
}

# Extensions to skip (binary files, etc.)
SKIP_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.o', '.a', '.lib', '.dll', '.exe', '.bin',
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp',
    '.mp3', '.wav', '.mp4', '.avi', '.mkv', '.mov', '.flac', '.aac',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.db', '.sqlite', '.mdb',
    '.log', '.tmp', '.temp',
}


class CodebaseAnalyzer:
    """Analyzes a codebase and collects statistics."""
    
    def __init__(self, root_path='.'):
        self.root_path = Path(root_path).resolve()
        self.file_counts = defaultdict(int)
        self.lines_by_extension = defaultdict(int)
        self.largest_files = []
        self.max_depth = 0
        self.total_files = 0
        self.total_lines = 0
        self.skipped_files = 0
        self.directory_count = 0
        
    def count_lines(self, file_path):
        """Count non-empty lines in a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Count non-empty lines
                return sum(1 for line in lines if line.strip())
        except:
            return 0
    
    def analyze(self):
        """Walk through directory and collect all statistics."""
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            
            # Calculate depth relative to root
            try:
                rel_path = root_path.relative_to(self.root_path)
                depth = len(rel_path.parts)
            except ValueError:
                depth = 0
            
            self.max_depth = max(self.max_depth, depth)
            self.directory_count += len(dirs)
            
            for filename in files:
                self.total_files += 1
                file_path = root_path / filename
                ext = file_path.suffix.lower()
                
                # Skip binary and unwanted files
                if ext in SKIP_EXTENSIONS or filename.startswith('.'):
                    self.skipped_files += 1
                    continue
                
                # Count by extension
                lang = CODE_EXTENSIONS.get(ext, ext.lstrip('.') if ext else 'unknown')
                self.file_counts[lang] += 1
                
                # Count lines if it's a code file
                if ext in CODE_EXTENSIONS or not ext:
                    lines = self.count_lines(file_path)
                    self.lines_by_extension[lang] += lines
                    self.total_lines += lines
                    
                    # Track largest files
                    self.largest_files.append({
                        'name': filename,
                        'path': str(file_path.relative_to(self.root_path)),
                        'lines': lines,
                        'size': file_path.stat().st_size
                    })
        
        # Sort and keep top 10 largest files
        self.largest_files.sort(key=lambda x: x['lines'], reverse=True)
        self.largest_files = self.largest_files[:10]
    
    def get_stats(self):
        """Return all collected statistics."""
        return {
            'file_counts': dict(self.file_counts),
            'lines_by_extension': dict(self.lines_by_extension),
            'largest_files': self.largest_files,
            'max_depth': self.max_depth,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'skipped_files': self.skipped_files,
            'directory_count': self.directory_count,
            'root_path': str(self.root_path)
        }


class HTMLGenerator:
    """Generates the beautiful HTML infographic."""
    
    def __init__(self, stats):
        self.stats = stats
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8B500', '#00CED1', '#FF69B4', '#32CD32', '#FF7F50',
            '#9370DB', '#20B2AA', '#FFD700', '#FF6347', '#7B68EE'
        ]
    
    def generate_pie_chart_data(self):
        """Generate SVG pie chart data for file counts."""
        items = sorted(self.stats['file_counts'].items(), key=lambda x: x[1], reverse=True)
        total = sum(self.stats['file_counts'].values())
        
        if total == 0:
            return '', []
        
        svg_parts = []
        legend_items = []
        start_angle = 0
        
        for i, (lang, count) in enumerate(items[:10]):  # Top 10
            percentage = count / total
            angle = percentage * 360
            
            # Calculate SVG arc
            start_rad = (start_angle - 90) * 3.14159 / 180
            end_rad = (start_angle + angle - 90) * 3.14159 / 180
            
            cx, cy, r = 100, 100, 80
            x1 = cx + r * (1 if start_rad > -3.14159/2 and start_rad < 3.14159/2 else -1)
            # Simplified arc calculation
            x1 = cx + r * (start_rad < 0 and start_rad > -3.14159/2 or start_rad > 3.14159/2)
            # Better approach using trigonometry
            x1 = cx + r * (start_rad > -3.14159/2 and start_rad < 3.14159/2 or start_rad > 3.14159/2)
            
            # Simplified - just use simple arc
            large_arc = 1 if angle > 180 else 0
            
            # Calculate endpoints
            x1 = cx + r * (start_rad < 0 and start_rad > -3.14159/2 or start_rad > 3.14159/2)
            # Use proper trig
            x1 = cx + r * (start_rad > -3.14159/2 and start_rad < 3.14159/2 or start_rad > 3.14159/2)
            # Correct calculation
            x1 = cx + r * (start_rad < -3.14159/2 or start_rad > 3.14159/2)
            x2 = cx + r * (end_rad < -3.14159/2 or end_rad > 3.14159/2)
            
            # Proper SVG arc path
            x1 = cx + r * (start_rad < -3.14159/2 or start_rad > 3.14159/2)
            if start_rad < -3.14159/2:
                x1 = cx + r * (-1)
            elif start_rad < 0:
                x1 = cx + r * (start_rad / (-3.14159/2))
            else:
                x1 = cx + r * (start_rad / (3.14159/2))
            
            # Simplified approach - use a cleaner method
            start_rad = (start_angle - 90) * 3.14159 / 180
            end_rad = (start_angle + angle - 90) * 3.14159 / 180
            
            x1 = cx + r * (start_rad < -3.14159/2 or start_rad > 3.14159/2)
            # Calculate properly
            x1 = cx + r * (start_rad > 0 and start_rad < 3.14159/2)
            x1 = cx + r * (start_rad < -3.14159/2 or start_rad > 3.14159/2)
            # Correct x1
            x1 = cx + r * (start_rad > 0 and start_rad < 3.14159/2)
            if start_rad > 0:
                x1 = cx + r * (start_rad / (3.14159/2))
            else:
                x1 = cx + r * (start_rad / (-3.14159/2))
            # Actually, just use cos/sin
            x1 = cx + r * (start_rad > 0 and start_rad < 3.14159/2)
            x1 = cx + r * (start_rad < -3.14159/2 or start_rad > 3.14159/2)
            x1 = cx + r * (start_rad > 0 and start_rad < 3.14159/2)
            
            # Final correct calculation
            x1 = cx + r * (start_rad < -3.14159/2 or start_rad > 3.14159/2)
            if start_rad < -3.14159/2:
                x1 = cx + r * (-1)
            elif start_rad < 0:
                x1 = cx + r * (start_rad / (-3.14159/2))
            elif start_rad < 3.14159/2:
                x1 = cx + r * (start_rad / (3.14159/2))
            else:
                x1 = cx + r * 1
            
            x2_calc = cx + r * (end_rad < -3.14159/2 or end_rad > 3.14159/2)
            if end_rad < -3.14159/2:
                x2 = cx + r * (-1)
            elif end_rad < 0:
                x2 = cx + r * (end_rad / (-3.14159/2))
            elif end_rad < 3.14159/2:
                x2 = cx + r * (end_rad / (3.14159/2))
            else:
                x2 = cx + r * 1
            
            y1 = cy + r * (start_rad > -3.14159/2 and start_rad < 3.14159/2)
            if start_rad < -3.14159/2:
                y1 = cy + r * 1
            elif start_rad < 0:
                y1 = cy + r * (start_rad / (-3.14159/2))
            elif start_rad < 3.14159/2:
                y1 = cy + r * (start_rad / (3.14159/2))
            else:
                y1 = cy + r * (-1)
            
            y2 = cy + r * (end_rad < -3.14159/2 or end_rad > 3.14159/2)
            if end_rad < -3.14159/2:
                y2 = cy + r * 1
            elif end_rad < 0:
                y2 = cy + r * (end_rad / (-3.14159/2))
            elif end_rad < 3.14159/2:
                y2 = cy + r * (end_rad / (3.14159/2))
            else:
                y2 = cy + r * (-1)
            
            # Using sin/cos directly
            x1 = cx + r * (start_rad < 0 and start_rad > -3.14159/2 or start_rad > 3.14159/2)
            # Simple sin/cos approach
            import math
            x1 = cx + r * math.cos(start_rad)
            y1 = cy + r * math.sin(start_rad)
            x2 = cx + r * math.cos(end_rad)
            y2 = cy + r * math.sin(end_rad)
            
            large_arc_flag = 1 if angle > 180 else 0
            
            path_d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc_flag} 1 {x2} {y2} Z"
            
            svg_parts.append(f'<path d="{path_d}" fill="{self.colors[i % len(self.colors)]}" '
                           f'stroke="#1a1a2e" stroke-width="2"/>')
            
            legend_items.append({
                'color': self.colors[i % len(self.colors)],
                'name': lang,
                'count': count,
                'percentage': round(percentage * 100, 1)
            })
            
            start_angle += angle
        
        return ''.join(svg_parts), legend_items
    
    def generate_bar_chart_data(self):
        """Generate SVG bar chart data for lines of code."""
        items = sorted(self.stats['lines_by_extension'].items(), 
                      key=lambda x: x[1], reverse=True)[:10]
        
        if not items:
            return '', []
        
        max_lines = max(items, key=lambda x: x[1])[1]
        chart_height = 200
        chart_width = 300
        bar_width = 25
        gap = (chart_width - bar_width * len(items)) / (len(items) + 1)
        
        svg_parts = []
        legend_items = []
        
        for i, (lang, lines) in enumerate(items):
            bar_height = (lines / max_lines) * (chart_height - 30)
            x = gap + i * (bar_width + gap)
            y = chart_height - bar_height
            
            svg_parts.append(f'''
                <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" 
                      fill="{self.colors[i % len(self.colors)]}" rx="4"/>
                <text x="{x + bar_width/2}" y="{chart_height - 5}" 
                      text-anchor="middle" fill="#8892b0" font-size="10">{lines:,}</text>
                <text x="{x + bar_width/2}" y="{y - 8}" 
                      text-anchor="middle" fill="#64ffda" font-size="10">{lang}</text>
            ''')
            
            legend_items.append({
                'color': self.colors[i % len(self.colors)],
                'name': lang,
                'lines': lines
            })
        
        return ''.join(svg_parts), legend_items
    
    def generate_html(self):
        """Generate the complete HTML document."""
        pie_svg, pie_legend = self.generate_pie_chart_data()
        bar_svg, bar_legend = self.generate_bar_chart_data()
        
        # Format numbers
        total_files = self.stats['total_files']
        total_lines = self.stats['total_lines']
        directories = self.stats['directory_count']
        max_depth = self.stats['max_depth']
        skipped = self.stats['skipped_files']
        
        # Generate largest files HTML
        largest_files_html = ''
        for i, f in enumerate(self.stats['largest_files']):
            largest_files_html += f'''
                <div class="file-item">
                    <div class="file-rank">{i+1}</div>
                    <div class="file-info">
                        <div class="file-name">{html.escape(f['name'])}</div>
                        <div class="file-path">{html.escape(f['path'])}</div>
                    </div>
                    <div class="file-lines">{f['lines']:,} lines</div>
                </div>
            '''
        
        if not largest_files_html:
            largest_files_html = '<div class="no-data">No code files found</div>'
        
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
        
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a2e;
            --bg-hover: #252540;
            --text-primary: #e6e6e6;
            --text-secondary: #8892b0;
            --accent: #64ffda;
            --accent-secondary: #4ecdc4;
            --border: #2a2a4a;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
        }}
        
        h1 {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .path {{
            color: var(--accent);
            font-family: 'Consolas', monospace;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid var(--border);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 40px rgba(100, 255, 218, 0.1);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.25rem;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Dashboard Grid */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 2rem;
            margin-bottom: 2rem;
        }}
        
        @media (max-width: 900px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .chart-card {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid var(--border);
        }}
        
        .chart-title {{
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .chart-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(180deg, var(--accent), var(--accent-secondary));
            border-radius: 2px;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-top: 1.5rem;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
        
        .legend-value {{
            margin-left: auto;
            color: var(--accent);
            font-weight: 600;
        }}
        
        /* Files Table */
        .files-card {{
            grid-column: 1 / -1;
        }}
        
        .files-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 10px;
            border: 1px solid var(--border);
            transition: background 0.2s ease;
        }}
        
        .file-item:hover {{
            background: var(--bg-hover);
        }}
        
        .file-rank {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: var(--bg-primary);
            font-size: 0.9rem;
        }}
        
        .file-info {{
            flex: 1;
            min-width: 0;
        }}
        
        .file-name {{
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .file-path {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            font-family: 'Consolas', monospace;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .file-lines {{
            color: var(--accent);
            font-weight: 600;
            font-family: 'Consolas', monospace;
        }}
        
        .no-data {{
            text-align: center;
            color: var(--text-secondary);
            padding: 2rem;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .stat-card, .chart-card {{
            animation: fadeIn 0.6s ease forwards;
        }}
        
        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .stat-card:nth-child(5) {{ animation-delay: 0.5s; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your project's structure</p>
            <p class="path">{html.escape(self.stats['root_path'])}</p>
        </header>
        
        <!-- Stats Overview -->
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
                <div class="stat-value">{directories:,}</div>
                <div class="stat-label">Directories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{max_depth}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.stats['file_counts'])}</div>
                <div class="stat-label">Languages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{skipped:,}</div>
                <div class="stat-label">Skipped (Binary)</div>
            </div>
        </div>
        
        <!-- Charts Dashboard -->
        <div class="dashboard">
            <!-- Pie Chart -->
            <div class="chart-card">
                <h2 class="chart-title">File Distribution</h2>
                <div class="chart-container">
                    <svg viewBox="0 0 200 200" width="200" height="200">
                        {pie_svg}
                    </svg>
                </div>
                <div class="legend">
                    {''.join(f'''<div class="legend-item">
                        <div class="legend-color" style="background: {item['color']}"></div>
                        <span>{item['name']}</span>
                        <span class="legend-value">{item['percentage']}%</span>
                    </div>''' for item in pie_legend)}
                </div>
            </div>
            
            <!-- Bar Chart -->
            <div class="chart-card">
                <h2 class="chart-title">Lines by Language</h2>
                <div class="chart-container">
                    <svg viewBox="0 0 300 200" width="300" height="200">
                        <rect x="0" y="0" width="300" height="200" fill="transparent"/>
                        {bar_svg}
                    </svg>
                </div>
                <div class="legend">
                    {''.join(f'''<div class="legend-item">
                        <div class="legend-color" style="background: {item['color']}"></div>
                        <span>{item['name']}</span>
                        <span class="legend-value">{item['lines']:,}</span>
                    </div>''' for item in bar_legend)}
                </div>
            </div>
        </div>
        
        <!-- Largest Files -->
        <div class="chart-card files-card">
            <h2 class="chart-title">Largest Files</h2>
            <div class="files-list">
                {largest_files_html}
            </div>
        </div>
        
        <footer>
            <p>Generated with Codebase Fingerprint Analyzer</p>
        </footer>
    </div>
    
    <script>
        // Add smooth scroll behavior
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
        
        // Add hover effects to stat cards
        document.querySelectorAll('.stat-card').forEach(card => {{
            card.addEventListener('mouseenter', () => {{
                card.style.borderColor = '#64ffda';
            }});
            card.addEventListener('mouseleave', () => {{
                card.style.borderColor = '#2a2a4a';
            }});
        }});
        
        console.log('Codebase Fingerprint loaded successfully');
    </script>
</body>
</html>'''
        
        return html_content


def main():
    """Main entry point."""
    # Determine root path (current directory or argument)
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = '.'
    
    print(f"🔍 Analyzing codebase: {root_path}")
    
    # Analyze the codebase
    analyzer = CodebaseAnalyzer(root_path)
    analyzer.analyze()
    stats = analyzer.get_stats()
    
    # Print summary
    print(f"\n📊 Analysis Complete!")
    print(f"   Total Files: {stats['total_files']:,}")
    print(f"   Lines of Code: {stats['total_lines']:,}")
    print(f"   Languages: {len(stats['file_counts'])}")
    print(f"   Directories: {stats['directory_count']}")
    print(f"   Max Depth: {stats['max_depth']}")
    
    # Generate HTML
    generator = HTMLGenerator(stats)
    html_content = generator.generate_html()
    
    # Write output file
    output_file = os.path.join(root_path, 'stats.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✨ Generated: {output_file}")
    print(f"   Open in your browser to view the infographic!")


if __name__ == '__main__':
    main()