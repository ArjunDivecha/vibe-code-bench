import os
import json
import math
from collections import Counter

def get_stats():
    stats = {
        "file_types": Counter(),
        "total_lines": 0,
        "largest_files": [],
        "max_depth": 0,
        "total_files": 0,
        "dir_structure": {}
    }
    
    root_path = os.getcwd()
    
    for root, dirs, files in os.walk(root_path):
        # Calculate depth
        depth = root.replace(root_path, '').count(os.sep)
        if depth > stats["max_depth"]:
            stats["max_depth"] = depth
            
        for file in files:
            # Skip hidden files and common ignore patterns
            if file.startswith('.') or 'node_modules' in root or '__pycache__' in root:
                continue
                
            stats["total_files"] += 1
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower() or 'no ext'
            stats["file_types"][ext] += 1
            
            try:
                size = os.path.getsize(file_path)
                stats["largest_files"].append({
                    "name": file,
                    "size": size,
                    "path": os.path.relpath(file_path, root_path)
                })
                
                # Count lines
                with open(file_path, 'rb') as f:
                    lines = sum(1 for _ in f)
                    stats["total_lines"] += lines
            except (UnicodeDecodeError, PermissionError, OSError):
                pass

    # Sort and trim largest files
    stats["largest_files"].sort(key=lambda x: x['size'], reverse=True)
    stats["largest_files"] = stats["largest_files"][:5]
    
    return stats

def generate_html(stats):
    # Prepare data for charts
    file_labels = list(stats['file_types'].keys())
    file_values = list(stats['file_types'].values())
    
    # Sort for the pie chart
    sorted_types = sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)[:8]
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --accent-2: #818cf8;
            --accent-3: #fb7185;
            --text: #f1f5f9;
            --text-dim: #94a3b8;
        }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            max-width: 1100px;
            width: 100%;
        }}
        header {{
            margin-bottom: 2rem;
            border-left: 4px solid var(--accent);
            padding-left: 1rem;
        }}
        h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -0.025em; }}
        .subtitle {{ color: var(--text-dim); }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        .stat-main {{
            font-size: 3rem;
            font-weight: bold;
            color: var(--accent);
            margin: 0.5rem 0;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 250px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        td {{
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.9rem;
        }}
        .size-tag {{
            color: var(--accent-2);
            font-family: monospace;
        }}
        
        svg {{ overflow: visible; }}
        .slice:hover {{ opacity: 0.8; cursor: pointer; }}
        
        .legend {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-top: 1rem;
            font-size: 0.8rem;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 0.5rem; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p class="subtitle">Scanned: {os.getcwd()}</p>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Total Lines</h3>
                <div class="stat-main">{stats['total_lines']:,}</div>
                <p class="subtitle">Across {stats['total_files']} files</p>
            </div>
            <div class="card">
                <h3>Max Depth</h3>
                <div class="stat-main">{stats['max_depth']}</div>
                <p class="subtitle">Directory nesting levels</p>
            </div>
            <div class="card">
                <h3>File Composition</h3>
                <div class="chart-container" id="pie-chart"></div>
                <div class="legend" id="pie-legend"></div>
            </div>
            <div class="card">
                <h3>Largest Files</h3>
                <table>
                    {"".join(f"<tr><td>{f['name']}<br><small style='color:var(--text-dim)'>{f['path']}</small></td><td class='size-tag' align='right'>{f['size'] / 1024:.1f} KB</td></tr>" for f in stats['largest_files'])}
                </table>
            </div>
            <div class="card" style="grid-column: span 1">
                <h3>Top Extensions</h3>
                <div class="chart-container" id="bar-chart"></div>
            </div>
        </div>
    </div>

    <script>
        const colors = ['#38bdf8', '#818cf8', '#fb7185', '#34d399', '#fbbf24', '#a78bfa', '#f472b6', '#94a3b8'];
        
        // Data from Python
        const fileData = {json.dumps(dict(sorted_types))};
        
        function createPie() {{
            const container = document.getElementById('pie-chart');
            const legend = document.getElementById('pie-legend');
            const total = Object.values(fileData).reduce((a, b) => a + b, 0);
            
            let svg = `<svg viewBox="-1 -1 2 2" style="transform: rotate(-90deg); width: 180px; height: 180px;">`;
            let cumulativePercent = 0;

            Object.entries(fileData).forEach(([ext, val], i) => {{
                const percent = val / total;
                const [startX, startY] = getCoordinatesForPercent(cumulativePercent);
                cumulativePercent += percent;
                const [endX, endY] = getCoordinatesForPercent(cumulativePercent);
                const largeArcFlag = percent > 0.5 ? 1 : 0;
                const pathData = [
                    `M ${{startX}} ${{startY}}`,
                    `A 1 1 0 ${{largeArcFlag}} 1 ${{endX}} ${{endY}}`,
                    `L 0 0`,
                ].join(' ');
                
                svg += `<path d="${{pathData}}" fill="${{colors[i % colors.length]}}" class="slice"></path>`;
                
                // Legend
                legend.innerHTML += `
                    <div class="legend-item">
                        <div class="dot" style="background:${{colors[i % colors.length]}}"></div>
                        <span>${{ext}} (${{val}})</span>
                    </div>
                `;
            }});
            
            svg += `</svg>`;
            container.innerHTML = svg;
        }}

        function getCoordinatesForPercent(percent) {{
            const x = Math.cos(2 * Math.PI * percent);
            const y = Math.sin(2 * Math.PI * percent);
            return [x, y];
        }}

        function createBar() {{
            const container = document.getElementById('bar-chart');
            const entries = Object.entries(fileData);
            const max = Math.max(...Object.values(fileData));
            
            let svg = `<svg width="100%" height="200">`;
            entries.forEach(([ext, val], i) => {{
                const barHeight = (val / max) * 150;
                const x = i * (100 / entries.length);
                svg += `
                    <rect x="${{x + 1}}%" y="${{180 - barHeight}}" width="${{(100 / entries.length) - 2}}%" height="${{barHeight}}" fill="${{colors[i % colors.length]}}" rx="4"/>
                    <text x="${{x + 5}}%" y="195" fill="var(--text-dim)" font-size="10">${{ext}}</text>
                `;
            }});
            svg += `</svg>`;
            container.innerHTML = svg;
        }}

        createPie();
        createBar();
    </script>
</body>
</html>
    """
    return html_template

if __name__ == "__main__":
    print("🔍 Scanning codebase...")
    data = get_stats()
    html_content = generate_html(data)
    
    output_file = "stats.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"✅ Success! Infographic generated at: {os.path.abspath(output_file)}")