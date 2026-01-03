#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful, single-file HTML infographic of your codebase.
"""

import os
import re
from collections import defaultdict
from html import escape
from typing import Dict, List, Tuple

# File extensions to ignore
IGNORED_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.idea', '.vscode'}
IGNORED_FILES = {'.gitignore', '.DS_Store', 'Thumbs.db'}

# Language colors for the infographic
LANGUAGE_COLORS = {
    'py': '#3776AB',
    'js': '#F7DF1E',
    'ts': '#3178C6',
    'html': '#E34F26',
    'css': '#1572B6',
    'java': '#ED8B00',
    'c': '#A8B9CC',
    'cpp': '#00599C',
    'go': '#00ADD8',
    'rs': '#DEA584',
    'rb': '#CC342D',
    'php': '#777BB4',
    'swift': '#FA7343',
    'kt': '#7F52FF',
    'rs': '#DEA584',
    'scala': '#DC322F',
    'lua': '#000080',
    'r': '#276DC3',
    'jl': '#9558B2',
    'ex': '#4E2A8E',
    'erl': '#B83998',
    'hs': '#5E5086',
    'ml': '#DF7F93',
    'clj': '#91DC47',
    'sc': '#234A8E',
    'yaml': '#CB171E',
    'yml': '#CB171E',
    'json': '#000000',
    'xml': '#F80',
    'md': '#083FA1',
    'txt': '#CCCCCC',
    'sh': '#89E051',
    'bat': '#4D4D4D',
    'sql': '#E38C00',
    'dockerfile': '#2496ED',
    'makefile': '#6D8086',
    'cmake': '#DA3434',
    'csv': '#237346',
    'png': '#E97451',
    'jpg': '#E97451',
    'jpeg': '#E97451',
    'gif': '#E97451',
    'svg': '#FF9900',
    'pdf': '#F40F02',
    'zip': '#0066CC',
    'tar': '#0066CC',
    'gz': '#0066CC',
}

# Default color for unknown extensions
DEFAULT_COLOR = '#6366F1'

# Chart colors - vibrant palette for dark mode
CHART_COLORS = [
    '#F472B6', '#22D3EE', '#A78BFA', '#34D399', '#FBBF24',
    '#F87171', '#FB923C', '#60A5FA', '#A3E635', '#C084FC',
    '#2DD4BF', '#FCD34D', '#FCA5A5', '#93C5FD', '#86EFAC',
]


class CodebaseAnalyzer:
    """Analyzes a codebase and collects statistics."""
    
    def __init__(self):
        self.file_counts = defaultdict(int)
        self.total_lines = 0
        self.total_files = 0
        self.largest_files = []
        self.max_depth = 0
        self.files_by_size = []
    
    def get_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            ext = parts[1].lower()
            # Handle common multi-part extensions
            multi_ext = {'cmake': 'cmake', 'dockerfile': 'dockerfile', 'makefile': 'makefile'}
            if filename.lower() in multi_ext:
                return multi_ext[filename.lower()]
            return ext
        return 'unknown'
    
    def count_lines(self, filepath: str) -> int:
        """Count lines in a file efficiently."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def analyze_directory(self, path: str = '.', current_depth: int = 0):
        """Recursively analyze a directory."""
        if current_depth > 50:  # Prevent infinite recursion
            return
            
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return
        
        for entry in entries:
            if entry.startswith('.'):
                # Check for special files that should be ignored
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path) and entry not in IGNORED_DIRS:
                    self.analyze_directory(full_path, current_depth + 1)
                elif entry in IGNORED_FILES:
                    continue
            else:
                full_path = os.path.join(path, entry)
                
                if os.path.isfile(full_path):
                    try:
                        size = os.path.getsize(full_path)
                        ext = self.get_extension(entry)
                        self.file_counts[ext] += 1
                        self.total_files += 1
                        
                        lines = self.count_lines(full_path)
                        self.total_lines += lines
                        
                        self.files_by_size.append({
                            'name': os.path.join(path, entry),
                            'size': size,
                            'lines': lines,
                            'extension': ext
                        })
                        
                        if current_depth > self.max_depth:
                            self.max_depth = current_depth
                            
                    except (PermissionError, OSError):
                        pass
    
    def get_top_extensions(self, n: int = 10) -> List[Tuple[str, int]]:
        """Get top N extensions by file count."""
        sorted_ext = sorted(self.file_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_ext[:n]
    
    def get_largest_files(self, n: int = 10) -> List[Dict]:
        """Get largest files by size."""
        sorted_files = sorted(self.files_by_size, key=lambda x: x['size'], reverse=True)
        return sorted_files[:n]
    
    def get_files_by_lines(self, n: int = 10) -> List[Dict]:
        """Get files with most lines of code."""
        code_files = [f for f in self.files_by_size if f['lines'] > 0]
        sorted_files = sorted(code_files, key=lambda x: x['lines'], reverse=True)
        return sorted_files[:n]
    
    def format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class HTMLGenerator:
    """Generates the HTML infographic."""
    
    def __init__(self, analyzer: CodebaseAnalyzer):
        self.analyzer = analyzer
    
    def generate_pie_chart(self, data: List[Tuple[str, int]]) -> str:
        """Generate an SVG pie chart for extension distribution."""
        if not data:
            return '<text x="100" y="110" text-anchor="middle" fill="#94A3B8">No data available</text>'
        
        total = sum(count for _, count in data)
        if total == 0:
            return '<text x="100" y="110" text-anchor="middle" fill="#94A3B8">No files found</text>'
        
        svg_parts = []
        current_angle = -90  # Start from top
        cx, cy, r = 120, 120, 100
        
        for i, (ext, count) in enumerate(data):
            percentage = count / total
            angle = percentage * 360
            end_angle = current_angle + angle
            
            # Calculate coordinates
            start_rad = current_angle * 3.14159 / 180
            end_rad = end_angle * 3.14159 / 180
            
            x1 = cx + r * (1 if abs(start_rad) < 3.14159/2 else -1) * abs(cos(start_rad))
            y1 = cy + r * (1 if start_rad < 0 else -1) * abs(sin(start_rad))
            x2 = cx + r * (1 if abs(end_rad) < 3.14159/2 else -1) * abs(cos(end_rad))
            y2 = cy + r * (1 if end_rad < 0 else -1) * abs(sin(end_rad))
            
            large_arc = 1 if angle > 180 else 0
            
            color = CHART_COLORS[i % len(CHART_COLORS)]
            
            path_d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"
            
            svg_parts.append(f'<path d="{path_d}" fill="{color}" stroke="#0F172A" stroke-width="2">')
            svg_parts.append(f'<title>{ext}: {count} files ({percentage*100:.1f}%)</title>')
            svg_parts.append('</path>')
            
            current_angle = end_angle
        
        # Add center circle for donut effect
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="45" fill="#0F172A"/>')
        
        return ''.join(svg_parts)
    
    def generate_bar_chart(self, data: List[Dict], key: str = 'lines') -> str:
        """Generate an SVG bar chart for line counts or file sizes."""
        if not data:
            return '<text x="150" y="100" text-anchor="middle" fill="#94A3B8">No data available</text>'
        
        max_value = max(item[key] for item in data)
        if max_value == 0:
            max_value = 1
        
        bars = []
        bar_height = 30
        bar_gap = 10
        chart_height = len(data) * (bar_height + bar_gap) + 40
        chart_width = 500
        label_width = 150
        chart_area = chart_width - label_width - 50
        
        for i, item in enumerate(data):
            y = 30 + i * (bar_height + bar_gap)
            value = item[key]
            bar_width = (value / max_value) * chart_area
            name = os.path.basename(item['name'])
            if len(name) > 20:
                name = name[:17] + '...'
            
            color = CHART_COLORS[i % len(CHART_COLORS)]
            
            # Bar
            bars.append(f'<rect x="{label_width}" y="{y}" width="{bar_width}" height="{bar_height}" rx="4" fill="{color}">')
            bars.append(f'<title>{item["name"]}: {value:,}</title>')
            bars.append('</rect>')
            
            # Label
            bars.append(f'<text x="{label_width - 10}" y="{y + bar_height/2 + 5}" text-anchor="end" fill="#E2E8F0" font-size="12">{escape(name)}</text>')
            
            # Value
            if key == 'lines':
                value_text = f"{value:,} lines"
            else:
                value_text = self.analyzer.format_size(value)
            bars.append(f'<text x="{label_width + bar_width + 8}" y="{y + bar_height/2 + 5}" fill="#94A3B8" font-size="12">{value_text}</text>')
        
        return ''.join(bars)
    
    def generate_html(self) -> str:
        """Generate the complete HTML document."""
        top_ext = self.analyzer.get_top_extensions(10)
        largest_files = self.analyzer.get_largest_files(10)
        most_lines = self.analyzer.get_files_by_lines(10)
        
        # Calculate stats
        total_size = sum(f['size'] for f in self.analyzer.files_by_size)
        
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #0F172A 100%);
            min-height: 100vh;
            color: #E2E8F0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #F472B6, #22D3EE, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }
        
        .subtitle {
            color: #94A3B8;
            font-size: 1.1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #94A3B8;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .card-pink .stat-value { color: #F472B6; }
        .card-cyan .stat-value { color: #22D3EE; }
        .card-purple .stat-value { color: #A78BFA; }
        .card-green .stat-value { color: #34D399; }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .chart-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .chart-icon {
            width: 24px;
            height: 24px;
        }
        
        .pie-container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .pie-legend {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        
        .legend-count {
            color: #94A3B8;
            margin-left: auto;
            padding-left: 15px;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        .bar-chart {
            width: 100%;
            overflow-x: auto;
        }
        
        .file-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
        }
        
        .list-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .file-item:last-child {
            border-bottom: none;
        }
        
        .file-name {
            color: #E2E8F0;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .file-meta {
            display: flex;
            gap: 15px;
            margin-left: 15px;
        }
        
        .file-lines {
            color: #22D3EE;
            font-size: 0.85rem;
        }
        
        .file-size {
            color: #94A3B8;
            font-size: 0.85rem;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: #64748B;
            font-size: 0.9rem;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 2rem; }
            .dashboard { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ Codebase Fingerprint</h1>
            <p class="subtitle">A visual exploration of your codebase's DNA</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card card-pink">
                <div class="stat-value">''' + f"{self.analyzer.total_files:,}" + '''</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card card-cyan">
                <div class="stat-value">''' + f"{self.analyzer.total_lines:,}" + '''</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card card-purple">
                <div class="stat-value">''' + f"{len(self.analyzer.file_counts)}" + '''</div>
                <div class="stat-label">File Types</div>
            </div>
            <div class="stat-card card-green">
                <div class="stat-value">''' + self.analyzer.format_size(total_size) + '''</div>
                <div class="stat-label">Total Size</div>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="chart-card">
                <h2 class="chart-title">
                    <svg class="chart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 2a10 10 0 0 1 10 10"/>
                        <path d="M12 2a10 10 0 0 0-10 10"/>
                    </svg>
                    File Types Distribution
                </h2>
                <div class="pie-container">
                    <svg width="240" height="240" viewBox="0 0 240 240">
                        ''' + self.generate_pie_chart(top_ext) + '''
                    </svg>
                    <div class="pie-legend">
'''
        
        # Add legend items
        for i, (ext, count) in enumerate(top_ext):
            color = CHART_COLORS[i % len(CHART_COLORS)]
            percentage = count / self.analyzer.total_files * 100 if self.analyzer.total_files > 0 else 0
            html += f'''                        <div class="legend-item">
                            <div class="legend-color" style="background: {color}"></div>
                            <span>.{escape(ext)}</span>
                            <span class="legend-count">{count} ({percentage:.1f}%)</span>
                        </div>
'''
        
        html += '''                    </div>
                </div>
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">
                    <svg class="chart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <line x1="3" y1="9" x2="21" y2="9"/>
                        <line x1="9" y1="21" x2="9" y2="9"/>
                    </svg>
                    Code Volume by File
                </h2>
                <div class="bar-chart">
                    <svg width="100%" height="''' + str(len(most_lines) * 40 + 50) + '''" viewBox="0 0 500 ''' + str(len(most_lines) * 40 + 50) + '''">
                        ''' + self.generate_bar_chart(most_lines, 'lines') + '''
                    </svg>
                </div>
            </div>
            
            <div class="chart-card">
                <h2 class="chart-title">
                    <svg class="chart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                    </svg>
                    Largest Files
                </h2>
                <div class="bar-chart">
                    <svg width="100%" height="''' + str(len(largest_files) * 40 + 50) + '''" viewBox="0 0 500 ''' + str(len(largest_files) * 40 + 50) + '''">
                        ''' + self.generate_bar_chart(largest_files, 'size') + '''
                    </svg>
                </div>
            </div>
        </div>
        
        <div class="file-list">
            <div class="list-card full-width">
                <h2 class="chart-title">
                    <svg class="chart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    Top Files by Line Count
                </h2>
'''
        
        for i, f in enumerate(most_lines[:15]):
            name = f['name']
            if len(name) > 60:
                name = name[:57] + '...'
            html += f'''                <div class="file-item">
                    <span class="file-name">{escape(name)}</span>
                    <div class="file-meta">
                        <span class="file-lines">{f['lines']:,} lines</span>
                        <span class="file-size">{self.analyzer.format_size(f['size'])}</span>
                    </div>
                </div>
'''
        
        html += '''            </div>
        </div>
        
        <div class="footer">
            <p>Generated with ❤️ using Codebase Fingerprint</p>
        </div>
    </div>
    
    <script>
        // Add smooth scroll behavior
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // Add hover effects to stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.02)';
            });
            card.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
        });
        
        // Animate numbers on load
        function animateValue(element, start, end, duration) {
            const startTime = performance.now();
            const isInteger = Number.isInteger(start) && Number.isInteger(end);
            
            function update(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(start + (end - start) * easeOut);
                
                element.textContent = isInteger ? current.toLocaleString() : current.toFixed(1);
                
                if (progress < 1) {
                    requestAnimationFrame(update);
                }
            }
            
            requestAnimationFrame(update);
        }
        
        // Trigger animations after page load
        window.addEventListener('load', function() {
            document.querySelectorAll('.stat-value').forEach(el => {
                const text = el.textContent;
                const hasComma = text.includes(',');
                const hasDecimal = text.includes('.');
                
                let value;
                if (hasDecimal) {
                    value = parseFloat(text.replace(/[^\\d.]/g, ''));
                } else {
                    value = parseInt(text.replace(/[^\\d]/g, ''));
                }
                
                if (!isNaN(value)) {
                    const multiplier = hasDecimal ? 1 : 100;
                    animateValue(el, 0, value * multiplier, 1500);
                }
            });
        });
    </script>
</body>
</html>'''
        
        return html


def cos(angle):
    """Calculate cosine of angle in degrees."""
    import math
    return math.cos(angle * 3.14159 / 180)


def sin(angle):
    """Calculate sine of angle in degrees."""
    import math
    return math.sin(angle * 3.14159 / 180)


def main():
    """Main function to run the analyzer and generate the infographic."""
    print("🔍 Scanning codebase...")
    
    analyzer = CodebaseAnalyzer()
    analyzer.analyze_directory('.')
    
    print(f"   Found {analyzer.total_files:,} files")
    print(f"   {analyzer.total_lines:,} lines of code")
    print(f"   {len(analyzer.file_counts)} file types")
    
    print("\n🎨 Generating infographic...")
    
    generator = HTMLGenerator(analyzer)
    html_content = generator.generate_html()
    
    output_file = 'stats.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ Generated: {output_file}")
    print(f"\n📊 Open {output_file} in your browser to view the infographic!")


if __name__ == '__main__':
    main()