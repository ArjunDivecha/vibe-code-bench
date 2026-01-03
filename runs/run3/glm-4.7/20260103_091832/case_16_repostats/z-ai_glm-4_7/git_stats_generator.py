#!/usr/bin/env python3
"""
Git Stats Infographic Generator
Scans the current directory and generates a beautiful HTML infographic.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from html import escape


class CodebaseAnalyzer:
    """Analyzes a codebase and collects statistics."""
    
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir).resolve()
        self.file_count_by_ext = defaultdict(int)
        self.lines_by_ext = defaultdict(int)
        self.total_lines = 0
        self.total_files = 0
        self.largest_files = []
        self.max_depth = 0
        self.dir_count = 0
        
    def is_text_file(self, filepath):
        """Check if a file is likely a text/source file."""
        text_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh',
            '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.html', '.htm', '.xml',
            '.xhtml', '.css', '.scss', '.sass', '.less', '.json', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.conf', '.md', '.markdown', '.rst', '.txt',
            '.sql', '.graphql', '.dockerfile', '.makefile', '.cmake', '.pyi',
            '.vue', '.svelte', '.astro', '.elm', '.pug', '.jade', '.lua', '.perl',
            '.pl', '.pm', '.tcl', '.r', '.R', '.m', '.mm', '.nim', '.dart', '.groovy',
            '.clj', '.cljs', '.hs', '.lhs', '.fs', '.fsi', '.fsx', '.v', '.sv',
            '.vhdl', '.verilog', '.ml', '.mli', '.ex', '.exs', '.erl', '.hrl',
            '.lisp', '.lsp', '.scm', '.rkt', '.f90', '.f95', '.f03', '.cob', '.cbl',
            '.pas', '.pp', '.adb', '.ads', '.asm', '.s', '.nasm', '.y', '.lex', '.l'
        }
        # Also check common text file names without extensions
        text_filenames = {
            'Dockerfile', 'Makefile', 'CMakeLists.txt', '.gitignore', '.gitattributes',
            '.env', '.env.example', 'README', 'LICENSE', 'AUTHORS', 'CHANGELOG'
        }
        
        ext = filepath.suffix.lower()
        name = filepath.name
        
        return ext in text_extensions or name in text_filenames
    
    def count_lines(self, filepath):
        """Count lines in a file, excluding empty lines."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0
    
    def scan(self):
        """Recursively scan the directory tree."""
        print(f"Scanning {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip hidden directories and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'venv', 'env', '.venv',
                'dist', 'build', 'target', 'bin', 'obj', 'out',
                '.git', '.svn', '.hg', 'vendor', 'third_party'
            }]
            
            self.dir_count += len(dirs)
            depth = root.count(os.sep) - str(self.root_dir).count(os.sep)
            self.max_depth = max(self.max_depth, depth)
            
            for filename in files:
                filepath = Path(root) / filename
                
                if not self.is_text_file(filepath):
                    continue
                
                self.total_files += 1
                lines = self.count_lines(filepath)
                self.total_lines += lines
                
                ext = filepath.suffix.lower()
                if not ext:
                    ext = '.no_ext'
                
                self.file_count_by_ext[ext] += 1
                self.lines_by_ext[ext] += lines
                
                # Track largest files (top 10)
                self.largest_files.append((filepath, lines))
        
        # Sort largest files and keep top 10
        self.largest_files.sort(key=lambda x: x[1], reverse=True)
        self.largest_files = self.largest_files[:10]
        
        print(f"Found {self.total_files} files, {self.total_lines} lines of code")


class HTMLGenerator:
    """Generates the HTML infographic."""
    
    # Vibrant color palette for dark mode
    COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9',
        '#92A8D1', '#955251', '#B565A7', '#009B77', '#DD4124'
    ]
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        
    def generate_pie_chart(self, data, title):
        """Generate an SVG pie chart."""
        total = sum(data.values())
        if total == 0:
            return '<div class="chart-placeholder">No data available</div>'
        
        # Sort by value and get top 8, group rest as "Other"
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        top_items = sorted_items[:8]
        other_count = sum(v for k, v in sorted_items[8:])
        
        if other_count > 0:
            top_items.append(('.other', other_count))
        
        svg_parts = []
        current_angle = 0
        center_x, center_y = 150, 150
        radius = 120
        
        svg_parts.append(f'<div class="chart-container">')
        svg_parts.append(f'<h3>{title}</h3>')
        svg_parts.append(f'<svg viewBox="0 0 300 300" class="pie-chart">')
        
        # Create pie slices
        for idx, (label, value) in enumerate(top_items):
            if value == 0:
                continue
            
            percentage = value / total
            angle = percentage * 2 * 3.14159
            
            # Calculate slice path
            x1 = center_x + radius * 0.5 * 3.14159 * (current_angle / 3.14159)
            y1 = center_y
            
            end_angle = current_angle + angle
            x2 = center_x + radius * 0.5 * 3.14159 * (end_angle / 3.14159)
            y2 = center_y
            
            # Use simpler arc calculation
            start_x = center_x + radius * 3.14159 * (current_angle / 3.14159)
            start_y = center_y
            
            color = self.COLORS[idx % len(self.COLORS)]
            
            # Calculate coordinates on circle
            start_x = center_x + radius * (3.14159 if idx == 0 else 1) * (1 if idx % 2 == 0 else -1)
            start_y = center_y
            
            # Use cumulative percentage for positioning
            cum_pct = sum(v for k, v in top_items[:idx]) / total if idx > 0 else 0
            mid_pct = cum_pct + percentage / 2
            
            # Simple pie slice using stroke-dasharray
            circumference = 2 * 3.14159 * 50
            dash_length = (percentage * circumference)
            
            svg_parts.append(f'''
                <circle cx="150" cy="150" r="50" fill="none" stroke="{color}" stroke-width="100"
                    stroke-dasharray="{dash_length} {circumference}"
                    transform="rotate({(cum_pct * 360) - 90} 150 150)"
                    class="pie-slice" data-label="{label}" data-value="{value}" data-pct="{percentage*100:.1f}%"
                />
            ''')
            current_angle += angle
        
        # Add center hole for donut chart
        svg_parts.append(f'<circle cx="150" cy="150" r="60" fill="#1a1a2e" />')
        svg_parts.append(f'<text x="150" y="145" text-anchor="middle" fill="#ffffff" font-size="24" font-weight="bold">{total}</text>')
        svg_parts.append(f'<text x="150" y="170" text-anchor="middle" fill="#8888aa" font-size="12">files</text>')
        
        svg_parts.append('</svg>')
        
        # Add legend
        svg_parts.append('<div class="legend">')
        for idx, (label, value) in enumerate(top_items):
            color = self.COLORS[idx % len(self.COLORS)]
            pct = (value / total) * 100
            display_label = label[1:] if label.startswith('.') else label
            svg_parts.append(f'''
                <div class="legend-item">
                    <span class="legend-color" style="background: {color}"></span>
                    <span class="legend-label">{display_label}</span>
                    <span class="legend-value">{value} ({pct:.1f}%)</span>
                </div>
            ''')
        svg_parts.append('</div>')
        svg_parts.append('</div>')
        
        return ''.join(svg_parts)
    
    def generate_bar_chart(self, data, title, max_bars=10):
        """Generate an SVG bar chart."""
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_bars]
        
        if not sorted_items:
            return '<div class="chart-placeholder">No data available</div>'
        
        max_value = max(v for k, v in sorted_items)
        bar_height = 30
        bar_spacing = 10
        chart_height = len(sorted_items) * (bar_height + bar_spacing) + 40
        chart_width = 400
        
        svg_parts = []
        svg_parts.append(f'<div class="chart-container">')
        svg_parts.append(f'<h3>{title}</h3>')
        svg_parts.append(f'<svg viewBox="0 0 {chart_width} {chart_height}" class="bar-chart">')
        
        for idx, (label, value) in enumerate(sorted_items):
            bar_width = (value / max_value) * (chart_width - 100)
            y = 30 + idx * (bar_height + bar_spacing)
            color = self.COLORS[idx % len(self.COLORS)]
            display_label = label[1:] if label.startswith('.') else label
            
            # Background bar
            svg_parts.append(f'<rect x="80" y="{y}" width="{chart_width - 100}" height="{bar_height}" fill="#2a2a4a" rx="4" />')
            # Value bar
            svg_parts.append(f'''
                <rect x="80" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4">
                    <animate attributeName="width" from="0" to="{bar_width}" dur="0.5s" fill="freeze" />
                </rect>
            ''')
            # Label
            svg_parts.append(f'<text x="70" y="{y + bar_height/2 + 4}" text-anchor="end" fill="#aaaaaa" font-size="12">{display_label}</text>')
            # Value
            svg_parts.append(f'<text x="{bar_width + 90}" y="{y + bar_height/2 + 4}" text-anchor="start" fill="#ffffff" font-size="12" font-weight="bold">{value:,}</text>')
        
        svg_parts.append('</svg>')
        svg_parts.append('</div>')
        
        return ''.join(svg_parts)
    
    def generate_stats_cards(self):
        """Generate statistics cards."""
        a = self.analyzer
        
        # Calculate average lines per file
        avg_lines = a.total_lines / a.total_files if a.total_files > 0 else 0
        
        cards = [
            ('Total Files', f'{a.total_files:,}', '#FF6B6B'),
            ('Total Lines', f'{a.total_lines:,}', '#4ECDC4'),
            ('Directories', f'{a.dir_count:,}', '#45B7D1'),
            ('Max Depth', f'{a.max_depth}', '#96CEB4'),
            ('Avg Lines/File', f'{avg_lines:.1f}', '#FFEAA7'),
            ('File Types', f'{len(a.file_count_by_ext)}', '#DDA0DD'),
        ]
        
        html = '<div class="stats-grid">'
        for title, value, color in cards:
            html += f'''
                <div class="stat-card" style="border-top: 3px solid {color}">
                    <div class="stat-value">{value}</div>
                    <div class="stat-label">{title}</div>
                </div>
            '''
        html += '</div>'
        return html
    
    def generate_largest_files(self):
        """Generate largest files table."""
        if not self.analyzer.largest_files:
            return '<div class="section"><h3>Largest Files</h3><p>No files found.</p></div>'
        
        html = '<div class="section"><h3>Largest Files (by lines)</h3>'
        html += '<div class="file-list">'
        
        for idx, (filepath, lines) in enumerate(self.analyzer.largest_files):
            # Make path relative to root
            try:
                rel_path = filepath.relative_to(self.analyzer.root_dir)
            except ValueError:
                rel_path = filepath.name
            
            html += f'''
                <div class="file-item" style="border-left: 3px solid {self.COLORS[idx % len(self.COLORS)]}">
                    <span class="file-name">{escape(str(rel_path))}</span>
                    <span class="file-lines">{lines:,} lines</span>
                </div>
            '''
        
        html += '</div></div>'
        return html
    
    def generate(self, output_file="stats.html"):
        """Generate the complete HTML file."""
        a = self.analyzer
        
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
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #3a3a5a;
            margin-bottom: 40px;
        }}
        
        h1 {{
            font-size: 3rem;
            background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #8888aa;
            font-size: 1.1rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #8888aa;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
        }}
        
        .chart-container h3 {{
            margin-bottom: 20px;
            color: #ffffff;
            font-size: 1.2rem;
        }}
        
        .pie-chart {{
            display: block;
            margin: 0 auto;
            max-width: 100%;
        }}
        
        .pie-slice {{
            transition: opacity 0.3s ease;
            cursor: pointer;
        }}
        
        .pie-slice:hover {{
            opacity: 0.8;
        }}
        
        .legend {{
            margin-top: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.85rem;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
            margin-right: 8px;
        }}
        
        .legend-label {{
            flex: 1;
            color: #aaaaaa;
        }}
        
        .legend-value {{
            color: #ffffff;
            font-weight: bold;
        }}
        
        .bar-chart {{
            display: block;
            max-width: 100%;
        }}
        
        .section {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        
        .section h3 {{
            margin-bottom: 20px;
            color: #ffffff;
            font-size: 1.3rem;
        }}
        
        .file-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            transition: background 0.3s ease;
        }}
        
        .file-item:hover {{
            background: rgba(255, 255, 255, 0.08);
        }}
        
        .file-name {{
            color: #cccccc;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
        }}
        
        .file-lines {{
            color: #4ECDC4;
            font-weight: bold;
        }}
        
        .chart-placeholder {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 60px;
            text-align: center;
            color: #666688;
        }}
        
        footer {{
            text-align: center;
            padding: 40px 0;
            color: #666688;
            font-size: 0.9rem;
            border-top: 1px solid #3a3a5a;
            margin-top: 40px;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            
            .charts-section {{
                grid-template-columns: 1fr;
            }}
            
            .stat-value {{
                font-size: 2rem;
            }}
        }}
        
        /* Tooltip */
        .tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.85rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 1000;
        }}
        
        .tooltip.visible {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Analysis of {escape(str(a.root_dir))}</p>
        </header>
        
        {self.generate_stats_cards()}
        
        <div class="charts-section">
            {self.generate_pie_chart(dict(a.file_count_by_ext), 'Files by Extension')}
            {self.generate_bar_chart(dict(a.lines_by_ext), 'Lines of Code by Extension')}
        </div>
        
        {self.generate_largest_files()}
        
        <footer>
            <p>Generated by Git Stats Infographic Generator</p>
        </footer>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        // Add tooltip functionality
        const tooltip = document.getElementById('tooltip');
        const pieSlices = document.querySelectorAll('.pie-slice');
        
        pieSlices.forEach(slice => {{
            slice.addEventListener('mouseenter', (e) => {{
                const label = e.target.dataset.label;
                const value = e.target.dataset.value;
                const pct = e.target.dataset.pct;
                
                tooltip.innerHTML = `<strong>${label}</strong><br>${value} files (${pct})`;
                tooltip.classList.add('visible');
            }});
            
            slice.addEventListener('mousemove', (e) => {{
                tooltip.style.left = e.pageX + 15 + 'px';
                tooltip.style.top = e.pageY + 15 + 'px';
            }});
            
            slice.addEventListener('mouseleave', () => {{
                tooltip.classList.remove('visible');
            }});
        }});
        
        // Add entrance animations
        document.addEventListener('DOMContentLoaded', () => {{
            const cards = document.querySelectorAll('.stat-card');
            cards.forEach((card, index) => {{
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {{
                    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }});
    </script>
</body>
</html>'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Generated {output_file}")


def main():
    """Main entry point."""
    # Check if a directory argument is provided
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a valid directory")
        sys.exit(1)
    
    # Analyze the codebase
    analyzer = CodebaseAnalyzer(target_dir)
    analyzer.scan()
    
    # Generate the HTML infographic
    generator = HTMLGenerator(analyzer)
    generator.generate("stats.html")
    
    print("\n✓ Done! Open 'stats.html' in your browser to view the infographic.")


if __name__ == "__main__":
    main()