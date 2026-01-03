#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Generates a beautiful single-file HTML dashboard showing codebase statistics.
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import html

class CodebaseStats:
    def __init__(self, root_path='.'):
        self.root_path = Path(root_path).resolve()
        self.file_counts = defaultdict(int)
        self.total_lines = 0
        self.total_files = 0
        self.largest_files = []
        self.max_depth = 0
        self.lines_by_extension = defaultdict(int)
        self.directory_info = []
        
    def scan_directory(self):
        """Recursively scan directory and collect statistics."""
        self._scan_recursive(self.root_path, 0)
        self.largest_files.sort(key=lambda x: x['lines'], reverse=True)
        self.directory_info.sort(key=lambda x: x['files'], reverse=True)
    
    def _scan_recursive(self, path, depth):
        """Recursively scan a directory."""
        try:
            items = list(path.iterdir())
        except (PermissionError, OSError):
            return
        
        dir_files = 0
        dir_dirs = 0
        
        for item in items:
            try:
                if item.is_file():
                    self.total_files += 1
                    dir_files += 1
                    self._process_file(item)
                elif item.is_dir():
                    dir_dirs += 1
                    self._scan_recursive(item, depth + 1)
            except (PermissionError, OSError):
                continue
        
        if dir_files > 0 or dir_dirs > 0:
            self.directory_info.append({
                'path': str(path.relative_to(self.root_path)) if path != self.root_path else '.',
                'files': dir_files,
                'dirs': dir_dirs,
                'depth': depth
            })
        
        self.max_depth = max(self.max_depth, depth)
    
    def _process_file(self, file_path):
        """Process a single file and update statistics."""
        # Count by extension
        ext = file_path.suffix.lower()
        if ext:
            self.file_counts[ext] += 1
        else:
            self.file_counts['(no ext)'] += 1
        
        # Count lines
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = len(f.readlines())
                self.total_lines += lines
                self.lines_by_extension[ext if ext else '(no ext)'] += lines
        except (UnicodeDecodeError, OSError, PermissionError):
            lines = 0
        
        # Track largest files
        try:
            size = file_path.stat().st_size
            self.largest_files.append({
                'name': file_path.name,
                'path': str(file_path.relative_to(self.root_path)),
                'lines': lines,
                'size': size
            })
        except (OSError, PermissionError):
            pass
    
    def get_stats(self):
        """Return all collected statistics as a dictionary."""
        return {
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'file_counts': dict(self.file_counts),
            'lines_by_extension': dict(self.lines_by_extension),
            'largest_files': self.largest_files[:10],
            'max_depth': self.max_depth,
            'directory_info': self.directory_info[:10],
            'root_path': str(self.root_path)
        }


class HTMLGenerator:
    """Generates the HTML infographic."""
    
    COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
        '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
        '#BB8FCE', '#85C1E9', '#F8B500', '#00CED1'
    ]
    
    def __init__(self, stats):
        self.stats = stats
    
    def generate(self):
        """Generate the complete HTML document."""
        overview_section = self._generate_overview_section()
        pie_chart_section = self._generate_pie_chart_section()
        bar_chart_section = self._generate_bar_chart_section()
        file_list_section = self._generate_file_list_section()
        directory_section = self._generate_directory_section()
        
        html_content = '''<!DOCTYPE html>
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
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
            min-height: 100vh;
            color: #e6edf3;
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
            background: linear-gradient(90deg, #58a6ff, #a371f7, #f778ba);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }
        
        .subtitle {
            color: #8b949e;
            font-size: 1.1rem;
        }
        
        .path {
            color: #58a6ff;
            font-family: 'Courier New', monospace;
            margin-top: 10px;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            padding: 20px 0;
        }
        
        .card {
            background: rgba(22, 27, 34, 0.8);
            border: 1px solid #30363d;
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }
        
        .card h2 {
            font-size: 1.2rem;
            color: #58a6ff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-icon {
            width: 24px;
            height: 24px;
            fill: currentColor;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, rgba(88, 166, 255, 0.1), rgba(163, 113, 247, 0.1));
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(88, 166, 255, 0.2);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #58a6ff, #a371f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            color: #8b949e;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        .wide-card {
            grid-column: span 2;
        }
        
        @media (max-width: 700px) {
            .wide-card {
                grid-column: span 1;
            }
        }
        
        .pie-container {
            display: flex;
            align-items: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .pie-chart {
            width: 200px;
            height: 200px;
        }
        
        .pie-legend {
            flex: 1;
            min-width: 200px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #30363d;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
        
        .legend-text {
            flex: 1;
            font-size: 0.9rem;
        }
        
        .legend-value {
            color: #8b949e;
            font-size: 0.85rem;
        }
        
        .bar-chart {
            width: 100%;
            height: 250px;
            margin-top: 20px;
        }
        
        .file-list {
            list-style: none;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #30363d;
            gap: 15px;
        }
        
        .file-item:last-child {
            border-bottom: none;
        }
        
        .file-rank {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .file-info {
            flex: 1;
            min-width: 0;
        }
        
        .file-name {
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .file-path {
            color: #8b949e;
            font-size: 0.8rem;
            font-family: monospace;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .file-stats {
            text-align: right;
        }
        
        .file-lines {
            font-weight: 600;
            color: #58a6ff;
        }
        
        .file-size {
            font-size: 0.8rem;
            color: #8b949e;
        }
        
        .depth-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 0;
        }
        
        .depth-indicator {
            width: 40px;
            font-size: 0.8rem;
            color: #8b949e;
        }
        
        .depth-visual {
            height: 8px;
            background: linear-gradient(90deg, #58a6ff, #a371f7);
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .depth-path {
            flex: 1;
            font-family: monospace;
            font-size: 0.9rem;
        }
        
        .depth-count {
            color: #8b949e;
            font-size: 0.85rem;
        }
        
        footer {
            text-align: center;
            padding: 40px 20px;
            color: #8b949e;
            font-size: 0.9rem;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .card {
            animation: fadeIn 0.6s ease forwards;
        }
        
        .card:nth-child(1) { animation-delay: 0.1s; }
        .card:nth-child(2) { animation-delay: 0.2s; }
        .card:nth-child(3) { animation-delay: 0.3s; }
        .card:nth-child(4) { animation-delay: 0.4s; }
        .card:nth-child(5) { animation-delay: 0.5s; }
        .card:nth-child(6) { animation-delay: 0.6s; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">A visual analysis of your project's structure</p>
            <p class="path">PATH_PLACEHOLDER</p>
        </header>
        
        <div class="dashboard">
            OVERVIEW_SECTION
            PIE_CHART_SECTION
            BAR_CHART_SECTION
            FILE_LIST_SECTION
            DIRECTORY_SECTION
        </div>
        
        <footer>
            <p>Generated with Codebase Fingerprint</p>
        </footer>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.stat-box').forEach(box => {
                box.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.05)';
                });
                box.addEventListener('mouseleave', function() {
                    this.style.transform = 'scale(1)';
                });
            });
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.querySelector('.depth-visual').style.width = 
                            Math.min(100, entry.target.dataset.depth * 20) + '%';
                    }
                });
            }, { threshold: 0.5 });
            
            document.querySelectorAll('.depth-bar').forEach(bar => {
                observer.observe(bar);
            });
        });
    </script>
</body>
</html>'''
        
        # Replace placeholders with actual content
        html_content = html_content.replace('PATH_PLACEHOLDER', html.escape(self.stats['root_path']))
        html_content = html_content.replace('OVERVIEW_SECTION', overview_section)
        html_content = html_content.replace('PIE_CHART_SECTION', pie_chart_section)
        html_content = html_content.replace('BAR_CHART_SECTION', bar_chart_section)
        html_content = html_content.replace('FILE_LIST_SECTION', file_list_section)
        html_content = html_content.replace('DIRECTORY_SECTION', directory_section)
        
        return html_content
    
    def _generate_overview_section(self):
        """Generate the overview stats section."""
        return '''
            <div class="card wide-card">
                <h2>
                    <svg class="card-icon" viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zm0 2v12h16V6H4zm2 2h12v2H6V8zm0 4h8v2H6v-2z"/></svg>
                    Project Overview
                </h2>
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-number">%s</div>
                        <div class="stat-label">Total Files</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">%s</div>
                        <div class="stat-label">Lines of Code</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">%s</div>
                        <div class="stat-label">File Types</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">%s</div>
                        <div class="stat-label">Max Depth</div>
                    </div>
                </div>
            </div>
        ''' % (
            format(self.stats['total_files'], ','),
            format(self.stats['total_lines'], ','),
            len(self.stats['file_counts']),
            self.stats['max_depth']
        )
    
    def _generate_pie_chart_section(self):
        """Generate SVG pie chart for file types."""
        file_counts = self.stats['file_counts']
        total = sum(file_counts.values())
        
        if total == 0:
            return '''
                <div class="card">
                    <h2>
                        <svg class="card-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
                        File Types
                    </h2>
                    <p style="color: #8b949e;">No files found</p>
                </div>
            '''
        
        # Sort by count and take top 8
        sorted_items = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        other_count = total - sum(c for _, c in sorted_items)
        if other_count > 0:
            sorted_items.append(('(other)', other_count))
        
        # Build pie chart with stroke-dasharray technique
        svg_slices = ""
        cumulative = 0
        for i, (ext, count) in enumerate(sorted_items):
            percent = count / total
            color = self.COLORS[i % len(self.COLORS)]
            svg_slices += '''
                <circle cx="80" cy="80" r="40" fill="transparent" stroke="%s" 
                        stroke-width="40" stroke-dasharray="%.1f 251.2" 
                        stroke-dashoffset="%.1f" 
                        transform="rotate(-90 80 80)"/>
            ''' % (color, percent * 251.2, -cumulative * 251.2)
            cumulative += percent
        
        legend_items = ""
        for i, (ext, count) in enumerate(sorted_items):
            percent = count / total * 100
            color = self.COLORS[i % len(self.COLORS)]
            legend_items += '''
                <div class="legend-item">
                    <div class="legend-color" style="background: %s"></div>
                    <span class="legend-text">%s</span>
                    <span class="legend-value">%d (%.1f%%)</span>
                </div>
            ''' % (color, ext, count, percent)
        
        return '''
            <div class="card">
                <h2>
                    <svg class="card-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
                    File Types
                </h2>
                <div class="pie-container">
                    <svg class="pie-chart" viewBox="0 0 160 160">
                        <circle cx="80" cy="80" r="40" fill="#161b22"/>
                        %s
                    </svg>
                    <div class="pie-legend">
                        %s
                    </div>
                </div>
            </div>
        ''' % (svg_slices, legend_items)
    
    def _generate_bar_chart_section(self):
        """Generate SVG bar chart for lines by extension."""
        lines_data = self.stats['lines_by_extension']
        
        if not lines_data:
            return '''
                <div class="card">
                    <h2>
                        <svg class="card-icon" viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
                        Lines by Type
                    </h2>
                    <p style="color: #8b949e;">No data available</p>
                </div>
            '''
        
        # Sort and take top 8
        sorted_items = sorted(lines_data.items(), key=lambda x: x[1], reverse=True)[:8]
        max_lines = sorted_items[0][1]
        
        chart_height = 200
        chart_width = 100
        bar_width = chart_width / len(sorted_items) - 10
        
        bars = ""
        for i, (ext, lines) in enumerate(sorted_items):
            bar_height = (lines / max_lines) * (chart_height - 40)
            x = i * (chart_width / len(sorted_items)) + 5
            y = chart_height - bar_height - 20
            text_x = x + bar_width / 2
            color = self.COLORS[i % len(self.COLORS)]
            
            bars += '''
                <g class="bar-group">
                    <rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" 
                          fill="%s" rx="4"/>
                    <text x="%.2f" y="%d" 
                          text-anchor="middle" fill="#8b949e" font-size="10">%s</text>
                    <text x="%.2f" y="%.2f" 
                          text-anchor="middle" fill="#e6edf3" font-size="10">%d</text>
                </g>
            ''' % (x, y, bar_width, bar_height, color, text_x, chart_height - 5, ext[:8], text_x, y - 5, lines)
        
        return '''
            <div class="card">
                <h2>
                    <svg class="card-icon" viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
                    Lines by Type
                </h2>
                <svg class="bar-chart" viewBox="0 0 %d %d">
                    <line x1="30" y1="10" x2="30" y2="%d" stroke="#30363d" stroke-width="1"/>
                    <line x1="30" y1="%d" x2="%d" y2="%d" stroke="#30363d" stroke-width="1"/>
                    %s
                </svg>
            </div>
        ''' % (chart_width, chart_height, chart_height - 20, chart_height - 20, chart_width, chart_height - 20, bars)
    
    def _generate_file_list_section(self):
        """Generate list of largest files."""
        files = self.stats['largest_files']
        
        if not files:
            return '''
                <div class="card wide-card">
                    <h2>
                        <svg class="card-icon" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                        Largest Files
                    </h2>
                    <p style="color: #8b949e;">No files found</p>
                </div>
            '''
        
        items = ""
        for i, f in enumerate(files[:8]):
            color = self.COLORS[i % len(self.COLORS)]
            size_str = self._format_size(f['size'])
            
            items += '''
                <li class="file-item">
                    <div class="file-rank" style="background: %s20; color: %s">%d</div>
                    <div class="file-info">
                        <div class="file-name">%s</div>
                        <div class="file-path">%s</div>
                    </div>
                    <div class="file-stats">
                        <div class="file-lines">%d lines</div>
                        <div class="file-size">%s</div>
                    </div>
                </li>
            ''' % (color, color, i + 1, html.escape(f['name']), html.escape(f['path']), f['lines'], size_str)
        
        return '''
            <div class="card wide-card">
                <h2>
                    <svg class="card-icon" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                    Largest Files
                </h2>
                <ul class="file-list">
                    %s
                </ul>
            </div>
        ''' % items
    
    def _generate_directory_section(self):
        """Generate directory structure visualization."""
        dirs = self.stats['directory_info']
        
        if not dirs:
            return '''
                <div class="card wide-card">
                    <h2>
                        <svg class="card-icon" viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
                        Directory Structure
                    </h2>
                    <p style="color: #8b949e;">No directories found</p>
                </div>
            '''
        
        items = ""
        for d in dirs[:8]:
            depth_level = d['depth'] + 1
            width_pct = min(100, depth_level * 12)
            items += '''
                <div class="depth-bar" data-depth="%d">
                    <span class="depth-indicator">L%d</span>
                    <div class="depth-visual" style="width: %d%%"></div>
                    <span class="depth-path">%s</span>
                    <span class="depth-count">%d files</span>
                </div>
            ''' % (depth_level, depth_level, width_pct, html.escape(d['path']), d['files'])
        
        return '''
            <div class="card wide-card">
                <h2>
                    <svg class="card-icon" viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
                    Directory Structure
                </h2>
                %s
            </div>
        ''' % items
    
    def _format_size(self, size):
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return "%.1f %s" % (size, unit)
            size /= 1024
        return "%.1f TB" % size


def main():
    """Main function to run the stats generator."""
    print("Scanning directory for codebase statistics...")
    
    # Scan current directory
    stats = CodebaseStats('.')
    stats.scan_directory()
    
    # Generate HTML
    print("Generating HTML infographic...")
    generator = HTMLGenerator(stats.get_stats())
    html_content = generator.generate()
    
    # Write output file
    output_file = 'stats.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Successfully generated: %s" % output_file)
    print("\nStatistics Summary:")
    print("  - Total files: %s" % format(stats.total_files, ','))
    print("  - Total lines: %s" % format(stats.total_lines, ','))
    print("  - File types: %d" % len(stats.file_counts))
    print("  - Max depth: %d" % stats.max_depth)


if __name__ == '__main__':
    main()