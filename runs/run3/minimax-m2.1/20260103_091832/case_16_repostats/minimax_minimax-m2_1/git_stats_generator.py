#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans directories and generates a beautiful HTML infographic
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import html

# Configuration
OUTPUT_FILE = "stats.html"
EXTENSION_COLORS = {
    'py': '#3572A5', 'js': '#f1e05a', 'ts': '#2b7489', 'html': '#e34c26',
    'css': '#563d7c', 'java': '#b07219', 'go': '#00ADD8', 'rs': '#dea584',
    'rb': '#701516', 'php': '#4F5D95', 'swift': '#F05138', 'c': '#555555',
    'cpp': '#f34b7d', 'cs': '#178600', 'vue': '#41b883', 'jsx': '#61dafb',
    'tsx': '#61dafb', 'json': '#292929', 'md': '#083fa1', 'sql': '#e38c00',
    'sh': '#89e051', 'yaml': '#cb171e', 'yml': '#cb171e', 'xml': '#0060ac',
    'svg': '#ff9900', 'png': '#199c27', 'jpg': '#199c27', 'jpeg': '#199c27',
    'gif': '#199c27', 'ico': '#199c27', 'ttf': '#a0a0a0', 'otf': '#a0a0a0',
    'woff': '#a0a0a0', 'woff2': '#a0a0a0', 'lock': '#8f8f8f', 'env': '#a0a0a0',
    'gitignore': '#a0a0a0', 'dockerfile': '#2496ED', 'ex': '#4e2a8e',
    'erl': '#b83998', 'hs': '#5e5086', 'ml': '#e67e00', 'scala': '#c22d40',
    'clj': '#91dc47', 'lua': '#000080', 'r': '#198ce7', 'jl': '#a270ba',
    'pl': '#0298c3', 'pm': '#0298c3', 'awk': '#c10c26', 'bat': '#4d4d4d',
    'ps1': '#012456', 'asm': '#6e4c13', 's': '#a0a0a0', 'h': '#555555',
    'hpp': '#f34b7d', 'cxx': '#f34b7d', 'cc': '#f34b7d', 'hh': '#f34b7d',
    'dart': '#00B4AB', 'kt': '#A97BFF', 'kts': '#A97BFF', 'nim': '#ffc200',
    'cr': '#000000', 'exs': '#4e2a8e', 'fs': '#7b8bb0', 'fsi': '#7b8bb0',
    'fsx': '#7b8bb0', 'elm': '#60B5BC', 'purs': '#f1e05a', 'agc': '#f1e05a',
    'applescript': '#6d414c', 'cson': '#199c27', 'ini': '#d1d1d1',
    'cfg': '#d1d1d1', 'conf': '#d1d1d1', 'toml': '#9c4221', 'gradle': '#02303a'
}

DEFAULT_COLOR = '#6e7681'
BINARY_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'ico', 'ttf', 'otf', 'woff', 'woff2', 'svg', 'lock', 'zip', 'gz', 'tar', 'bz2', 'xz', '7z', 'rar', 'pdf', 'bin', 'exe', 'dll', 'so', 'dylib', 'a', 'o', 'obj'}


def count_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except (IOError, OSError):
        return 0


def get_file_extension(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return 'none'


def scan_directory(base_path='.'):
    stats = {
        'files_by_ext': defaultdict(int),
        'total_files': 0,
        'total_lines': 0,
        'largest_files': [],
        'directory_depth': 0,
        'code_files': 0,
        'code_lines': 0,
        'all_files': []
    }
    
    code_extensions = {'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'go', 'rs', 'rb', 'php', 'swift', 'c', 'cpp', 'cs', 'vue', 'html', 'css', 'json', 'md', 'sql', 'sh', 'yaml', 'yml', 'xml', 'cson', 'ini', 'cfg', 'conf', 'toml', 'gradle', 'ex', 'erl', 'hs', 'ml', 'scala', 'clj', 'lua', 'r', 'jl', 'pl', 'pm', 'awk', 'bat', 'ps1', 'asm', 's', 'h', 'hpp', 'dart', 'kt', 'kts', 'nim', 'cr', 'exs', 'fs', 'fsi', 'fsx', 'elm', 'purs', 'agc', 'applescript', 'dockerfile', 'env', 'gitignore', 'lock'}
    
    for root, dirs, files in os.walk(base_path, followlinks=False):
        rel_path = os.path.relpath(root, base_path)
        depth = rel_path.count(os.sep) if rel_path != '.' else 0
        stats['directory_depth'] = max(stats['directory_depth'], depth)
        
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
                ext = get_file_extension(filename)
                lines = count_lines(filepath) if ext not in BINARY_EXTS else 0
                
                stats['total_files'] += 1
                stats['files_by_ext'][ext] += 1
                stats['total_lines'] += lines
                
                if ext in code_extensions:
                    stats['code_files'] += 1
                    stats['code_lines'] += lines
                
                stats['all_files'].append({'name': filename, 'path': rel_path, 'ext': ext, 'size': size, 'lines': lines})
                
            except (OSError, IOError):
                continue
    
    stats['largest_files'] = sorted(stats['all_files'], key=lambda x: x['size'], reverse=True)[:10]
    return stats


def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def generate_html(stats):
    ext_data = sorted(stats['files_by_ext'].items(), key=lambda x: x[1], reverse=True)[:12]
    
    pie_segments = []
    for ext, count in ext_data:
        color = EXTENSION_COLORS.get(ext, DEFAULT_COLOR)
        percentage = (count / stats['total_files']) * 100 if stats['total_files'] > 0 else 0
        pie_segments.append({'ext': ext, 'count': count, 'percentage': percentage, 'color': color})
    
    other_count = stats['total_files'] - sum(count for _, count in ext_data)
    if other_count > 0:
        pie_segments.append({'ext': 'other', 'count': other_count, 'percentage': (other_count / stats['total_files']) * 100 if stats['total_files'] > 0 else 0, 'color': DEFAULT_COLOR})
    
    pie_json = json.dumps(pie_segments)
    bar_data = [{'ext': ext, 'count': count} for ext, count in ext_data if ext != 'other']
    bar_json = json.dumps(bar_data)
    
    # Build HTML step by step to avoid format conflicts
    html_parts = []
    
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html lang="en">')
    html_parts.append('<head>')
    html_parts.append('<meta charset="UTF-8">')
    html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_parts.append('<title>Codebase Fingerprint</title>')
    html_parts.append('<style>')
    html_parts.append('* { margin: 0; padding: 0; box-sizing: border-box; }')
    html_parts.append('body { font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%); min-height: 100vh; color: #c9d1d9; padding: 20px; }')
    html_parts.append('.container { max-width: 1400px; margin: 0 auto; }')
    html_parts.append('header { text-align: center; padding: 40px 20px; margin-bottom: 30px; }')
    html_parts.append('h1 { font-size: 3rem; background: linear-gradient(90deg, #58a6ff, #8b949e, #f78166); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px; letter-spacing: -1px; }')
    html_parts.append('.subtitle { color: #8b949e; font-size: 1.1rem; }')
    html_parts.append('.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }')
    html_parts.append('.stat-card { background: rgba(22, 27, 34, 0.8); border: 1px solid #30363d; border-radius: 12px; padding: 24px; backdrop-filter: blur(10px); transition: transform 0.3s ease, box-shadow 0.3s ease; }')
    html_parts.append('.stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4); }')
    html_parts.append('.stat-value { font-size: 2.5rem; font-weight: 700; color: #58a6ff; margin-bottom: 8px; }')
    html_parts.append('.stat-label { color: #8b949e; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }')
    html_parts.append('.charts-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }')
    html_parts.append('.chart-card { background: rgba(22, 27, 34, 0.8); border: 1px solid #30363d; border-radius: 12px; padding: 24px; }')
    html_parts.append('.chart-title { font-size: 1.2rem; color: #f78166; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #30363d; }')
    html_parts.append('.chart-container { display: flex; justify-content: center; align-items: center; }')
    html_parts.append('.pie-chart { width: 280px; height: 280px; }')
    html_parts.append('.bar-chart { width: 100%; height: 250px; }')
    html_parts.append('.legend { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; justify-content: center; }')
    html_parts.append('.legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }')
    html_parts.append('.legend-color { width: 12px; height: 12px; border-radius: 3px; }')
    html_parts.append('.largest-files { background: rgba(22, 27, 34, 0.8); border: 1px solid #30363d; border-radius: 12px; padding: 24px; margin-bottom: 30px; }')
    html_parts.append('.files-table { width: 100%; border-collapse: collapse; }')
    html_parts.append('.files-table th { text-align: left; padding: 12px 16px; color: #8b949e; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #30363d; }')
    html_parts.append('.files-table td { padding: 14px 16px; border-bottom: 1px solid #21262d; }')
    html_parts.append('.files-table tr:hover td { background: rgba(48, 54, 61, 0.3); }')
    html_parts.append('.files-table tr:last-child td { border-bottom: none; }')
    html_parts.append('.file-name { color: #58a6ff; font-weight: 500; }')
    html_parts.append('.file-path { color: #8b949e; font-size: 0.85rem; }')
    html_parts.append('.file-size { color: #f78166; }')
    html_parts.append('.file-lines { color: #7ee787; }')
    html_parts.append('.ext-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; background: rgba(88, 166, 255, 0.15); color: #58a6ff; }')
    html_parts.append('.directory-tree { background: rgba(22, 27, 34, 0.8); border: 1px solid #30363d; border-radius: 12px; padding: 24px; }')
    html_parts.append('.depth-bar { display: flex; align-items: center; gap: 15px; margin-top: 15px; }')
    html_parts.append('.depth-track { flex: 1; height: 12px; background: #21262d; border-radius: 6px; overflow: hidden; }')
    html_parts.append('.depth-fill { height: 100%; background: linear-gradient(90deg, #58a6ff, #f78166); border-radius: 6px; transition: width 1s ease; }')
    html_parts.append('.depth-value { font-size: 1.5rem; font-weight: 700; color: #58a6ff; }')
    html_parts.append('.progress-section { margin-top: 20px; }')
    html_parts.append('.progress-bar { height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; margin-top: 10px; }')
    html_parts.append('.progress-fill { height: 100%; background: linear-gradient(90deg, #7ee787, #58a6ff); border-radius: 4px; transition: width 1.5s ease; }')
    html_parts.append('footer { text-align: center; padding: 30px; color: #8b949e; font-size: 0.9rem; }')
    html_parts.append('@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }')
    html_parts.append('.stat-card, .chart-card, .largest-files, .directory-tree { animation: fadeIn 0.6s ease forwards; }')
    html_parts.append('.stat-card:nth-child(1) { animation-delay: 0.1s; }')
    html_parts.append('.stat-card:nth-child(2) { animation-delay: 0.2s; }')
    html_parts.append('.stat-card:nth-child(3) { animation-delay: 0.3s; }')
    html_parts.append('.stat-card:nth-child(4) { animation-delay: 0.4s; }')
    html_parts.append('@media (max-width: 768px) { h1 { font-size: 2rem; } .charts-section { grid-template-columns: 1fr; } .stat-value { font-size: 2rem; } }')
    html_parts.append('</style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append('<div class="container">')
    html_parts.append('<header>')
    html_parts.append('<h1>Codebase Fingerprint</h1>')
    html_parts.append('<p class="subtitle">A visual analysis of your project structure</p>')
    html_parts.append('</header>')
    html_parts.append('<div class="stats-grid">')
    html_parts.append('<div class="stat-card">')
    html_parts.append('<div class="stat-value">{:,}</div>'.format(stats['total_files']))
    html_parts.append('<div class="stat-label">Total Files</div>')
    html_parts.append('</div>')
    html_parts.append('<div class="stat-card">')
    html_parts.append('<div class="stat-value">{:,}</div>'.format(stats['total_lines']))
    html_parts.append('<div class="stat-label">Total Lines</div>')
    html_parts.append('</div>')
    html_parts.append('<div class="stat-card">')
    html_parts.append('<div class="stat-value">{:,}</div>'.format(stats['code_files']))
    html_parts.append('<div class="stat-label">Code Files</div>')
    html_parts.append('</div>')
    html_parts.append('<div class="stat-card">')
    html_parts.append('<div class="stat-value">{:,}</div>'.format(stats['code_lines']))
    html_parts.append('<div class="stat-label">Code Lines</div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('<div class="charts-section">')
    html_parts.append('<div class="chart-card">')
    html_parts.append('<h2 class="chart-title">File Distribution by Type</h2>')
    html_parts.append('<div class="chart-container">')
    html_parts.append('<svg class="pie-chart" viewBox="0 0 100 100">')
    html_parts.append('<defs>')
    html_parts.append('<filter id="glow">')
    html_parts.append('<feGaussianBlur stdDeviation="0.5" result="coloredBlur"/>')
    html_parts.append('<feMerge>')
    html_parts.append('<feMergeNode in="coloredBlur"/>')
    html_parts.append('<feMergeNode in="SourceGraphic"/>')
    html_parts.append('</feMerge>')
    html_parts.append('</filter>')
    html_parts.append('</defs>')
    html_parts.append('<g id="pie-slices" filter="url(#glow)"></g>')
    html_parts.append('</svg>')
    html_parts.append('</div>')
    html_parts.append('<div class="legend" id="pie-legend"></div>')
    html_parts.append('</div>')
    html_parts.append('<div class="chart-card">')
    html_parts.append('<h2 class="chart-title">Top Extensions by File Count</h2>')
    html_parts.append('<div class="chart-container">')
    html_parts.append('<svg class="bar-chart" viewBox="0 0 400 250">')
    html_parts.append('<defs>')
    html_parts.append('<linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">')
    html_parts.append('<stop offset="0%" style="stop-color:#58a6ff;stop-opacity:1" />')
    html_parts.append('<stop offset="100%" style="stop-color:#f78166;stop-opacity:1" />')
    html_parts.append('</linearGradient>')
    html_parts.append('</defs>')
    html_parts.append('<g id="bar-chart-bars"></g>')
    html_parts.append('</svg>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('<div class="largest-files">')
    html_parts.append('<h2 class="chart-title">Largest Files by Size</h2>')
    html_parts.append('<table class="files-table">')
    html_parts.append('<thead>')
    html_parts.append('<tr>')
    html_parts.append('<th>File</th>')
    html_parts.append('<th>Extension</th>')
    html_parts.append('<th>Size</th>')
    html_parts.append('<th>Lines</th>')
    html_parts.append('</tr>')
    html_parts.append('</thead>')
    html_parts.append('<tbody>')
    
    for f in stats['largest_files']:
        html_parts.append('<tr>')
        html_parts.append('<td>')
        html_parts.append('<div class="file-name">{}</div>'.format(html.escape(f['name'])))
        html_parts.append('<div class="file-path">{}</div>'.format(html.escape(f['path'])))
        html_parts.append('</td>')
        html_parts.append('<td><span class="ext-badge">{}</span></td>'.format(html.escape(f['ext'])))
        html_parts.append('<td class="file-size">{}</td>'.format(format_size(f['size'])))
        html_parts.append('<td class="file-lines">{:,}</td>'.format(f['lines']))
        html_parts.append('</tr>')
    
    code_coverage = ((stats['code_files'] / stats['total_files']) * 100) if stats['total_files'] > 0 else 0
    depth_width = min(stats['directory_depth'] * 10, 100)
    
    html_parts.append('</tbody>')
    html_parts.append('</table>')
    html_parts.append('</div>')
    html_parts.append('<div class="directory-tree">')
    html_parts.append('<h2 class="chart-title">Directory Analysis</h2>')
    html_parts.append('<div class="depth-bar">')
    html_parts.append('<span>Max Depth:</span>')
    html_parts.append('<span class="depth-value">{}</span>'.format(stats['directory_depth']))
    html_parts.append('<div class="depth-track">')
    html_parts.append('<div class="depth-fill" style="width: {}%"></div>'.format(depth_width))
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('<div class="progress-section">')
    html_parts.append('<div style="display: flex; justify-content: space-between; color: #8b949e; margin-bottom: 5px;">')
    html_parts.append('<span>Code Coverage</span>')
    html_parts.append('<span>{:.1f}%</span>'.format(code_coverage))
    html_parts.append('</div>')
    html_parts.append('<div class="progress-bar">')
    html_parts.append('<div class="progress-fill" style="width: {:.1f}%"></div>'.format(code_coverage))
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('<footer>')
    html_parts.append('<p>Generated with Git Stats Infographic Generator</p>')
    html_parts.append('</footer>')
    html_parts.append('</div>')
    html_parts.append('<script>')
    html_parts.append('const pieData = ' + pie_json + ';')
    html_parts.append('function generatePieChart() {')
    html_parts.append('const svg = document.getElementById("pie-slices");')
    html_parts.append('const centerX = 50; const centerY = 50; const radius = 45;')
    html_parts.append('let cumulativeAngle = 0;')
    html_parts.append('pieData.forEach((segment) => {')
    html_parts.append('const startAngle = cumulativeAngle * Math.PI / 180;')
    html_parts.append('const endAngle = (cumulativeAngle + segment.percentage * 3.6) * Math.PI / 180;')
    html_parts.append('const x1 = centerX + radius * Math.sin(startAngle);')
    html_parts.append('const y1 = centerY - radius * Math.cos(startAngle);')
    html_parts.append('const x2 = centerX + radius * Math.sin(endAngle);')
    html_parts.append('const y2 = centerY - radius * Math.cos(endAngle);')
    html_parts.append('const largeArc = segment.percentage > 50 ? 1 : 0;')
    html_parts.append('const path = document.createElementNS("http://www.w3.org/2000/svg", "path");')
    html_parts.append('path.setAttribute("d", `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`);')
    html_parts.append('path.setAttribute("fill", segment.color);')
    html_parts.append('path.setAttribute("stroke", "#0d1117");')
    html_parts.append('path.setAttribute("stroke-width", "0.5");')
    html_parts.append('path.style.transition = "opacity 0.3s ease, transform 0.3s ease";')
    html_parts.append('path.style.cursor = "pointer";')
    html_parts.append('path.style.transformOrigin = "center";')
    html_parts.append('path.addEventListener("mouseenter", function() { this.style.transform = "scale(1.05)"; this.style.opacity = "0.9"; });')
    html_parts.append('path.addEventListener("mouseleave", function() { this.style.transform = "scale(1)"; this.style.opacity = "1"; });')
    html_parts.append('svg.appendChild(path);')
    html_parts.append('cumulativeAngle += segment.percentage * 3.6;')
    html_parts.append('});')
    html_parts.append('const legend = document.getElementById("pie-legend");')
    html_parts.append('pieData.forEach(segment => {')
    html_parts.append('const item = document.createElement("div");')
    html_parts.append('item.className = "legend-item";')
    html_parts.append('item.innerHTML = `<span class="legend-color" style="background: ${segment.color}"></span><span>.${segment.ext} (${segment.count})</span>`;')
    html_parts.append('legend.appendChild(item);')
    html_parts.append('});')
    html_parts.append('}')
    html_parts.append('const barData = ' + bar_json + ';')
    html_parts.append('function generateBarChart() {')
    html_parts.append('const svg = document.getElementById("bar-chart-bars");')
    html_parts.append('const maxCount = Math.max(...barData.map(d => d.count));')
    html_parts.append('const barWidth = 280 / barData.length - 10;')
    html_parts.append('const startX = 20; const startY = 220; const chartHeight = 180;')
    html_parts.append('barData.forEach((d, i) => {')
    html_parts.append('const barHeight = (d.count / maxCount) * chartHeight;')
    html_parts.append('const x = startX + i * (barWidth + 10);')
    html_parts.append('const y = startY - barHeight;')
    html_parts.append('const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");')
    html_parts.append('bar.setAttribute("x", x); bar.setAttribute("y", y); bar.setAttribute("width", barWidth);')
    html_parts.append('bar.setAttribute("height", barHeight); bar.setAttribute("fill", "url(#barGradient)"); bar.setAttribute("rx", "4");')
    html_parts.append('bar.style.transition = "height 0.5s ease, y 0.5s ease"; bar.style.cursor = "pointer";')
    html_parts.append('bar.addEventListener("mouseenter", function() { this.style.filter = "brightness(1.2)"; });')
    html_parts.append('bar.addEventListener("mouseleave", function() { this.style.filter = "brightness(1)"; });')
    html_parts.append('svg.appendChild(bar);')
    html_parts.append('const label = document.createElementNS("http://www.w3.org/2000/svg", "text");')
    html_parts.append('label.setAttribute("x", x + barWidth / 2); label.setAttribute("y", startY + 18);')
    html_parts.append('label.setAttribute("text-anchor", "middle"); label.setAttribute("fill", "#8b949e");')
    html_parts.append('label.setAttribute("font-size", "11"); label.textContent = "." + d.ext;')
    html_parts.append('svg.appendChild(label);')
    html_parts.append('const value = document.createElementNS("http://www.w3.org/2000/svg", "text");')
    html_parts.append('value.setAttribute("x", x + barWidth / 2); value.setAttribute("y", y - 8);')
    html_parts.append('value.setAttribute("text-anchor", "middle"); value.setAttribute("fill", "#c9d1d9");')
    html_parts.append('value.setAttribute("font-size", "10"); value.textContent = d.count;')
    html_parts.append('svg.appendChild(value);')
    html_parts.append('});')
    html_parts.append('}')
    html_parts.append('document.addEventListener("DOMContentLoaded", function() { generatePieChart(); generateBarChart(); });')
    html_parts.append('</script>')
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    return '\n'.join(html_parts)


def main():
    print("Scanning directory for code statistics...")
    print("=" * 50)
    
    stats = scan_directory('.')
    
    print(f"Total Files: {stats['total_files']:,}")
    print(f"Total Lines: {stats['total_lines']:,}")
    print(f"Code Files: {stats['code_files']:,}")
    print(f"Code Lines: {stats['code_lines']:,}")
    print(f"Max Directory Depth: {stats['directory_depth']}")
    print()
    print("Top Extensions:")
    for ext, count in sorted(stats['files_by_ext'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   .{ext}: {count:,} files")
    
    print()
    print("Generating HTML infographic...")
    
    html_content = generate_html(stats)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Successfully created {OUTPUT_FILE}")
    print("Open it in your browser to view the infographic!")
    print("=" * 50)


if __name__ == "__main__":
    main()