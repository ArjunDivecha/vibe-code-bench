import os
import json
import collections
import math

def get_stats():
    stats = {
        "extensions": collections.defaultdict(int),
        "total_lines": 0,
        "file_count": 0,
        "largest_files": [],
        "max_depth": 0,
        "dir_structure": collections.defaultdict(int)
    }

    root_dir = os.getcwd()

    for root, dirs, files in os.walk(root_dir):
        # Calculate depth
        rel_path = os.path.relpath(root, root_dir)
        depth = 0 if rel_path == "." else len(rel_path.split(os.sep))
        stats["max_depth"] = max(stats["max_depth"], depth)

        for file in files:
            # Skip hidden files and common ignore patterns
            if file.startswith('.') or 'node_modules' in root or '__pycache__' in root:
                continue

            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                ext = os.path.splitext(file)[1].lower() or "no-ext"
                
                stats["file_count"] += 1
                stats["extensions"][ext] += 1
                
                # Try to read lines for common text files
                if ext in ['.py', '.js', '.html', '.css', '.md', '.txt', '.json', '.c', '.cpp', '.java', '.ts', '.go']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        stats["total_lines"] += lines
                
                stats["largest_files"].append({
                    "name": file,
                    "path": os.path.relpath(file_path, root_dir),
                    "size": file_size
                })
            except (PermissionError, OSError):
                continue

    # Sort largest files
    stats["largest_files"].sort(key=lambda x: x["size"], reverse=True)
    stats["largest_files"] = stats["largest_files"][:5]

    # Sort extensions
    stats["extensions"] = dict(sorted(stats["extensions"].items(), key=lambda x: x[1], reverse=True)[:8])
    
    return stats

def generate_html(stats):
    # Prepare data for JS/SVG charts
    ext_labels = list(stats["extensions"].keys())
    ext_values = list(stats["extensions"].values())
    
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
            --text: #f1f5f9;
            --muted: #94a3b8;
            --chart1: #818cf8;
            --chart2: #fb7185;
            --chart3: #34d399;
            --chart4: #fbbf24;
            --chart5: #a78bfa;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            max-width: 1000px;
            width: 100%;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        h1 {{
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .stat-box {{
            text-align: center;
            padding: 15px;
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
        }}
        .stat-value {{
            display: block;
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent);
        }}
        .stat-label {{
            font-size: 0.8rem;
            color: var(--muted);
            text-transform: uppercase;
        }}
        h2 {{
            font-size: 1.2rem;
            margin-top: 0;
            margin-bottom: 20px;
            color: var(--muted);
            border-left: 4px solid var(--accent);
            padding-left: 10px;
        }}
        .file-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .file-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.9rem;
        }}
        .file-name {{ color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }}
        .file-size {{ color: var(--muted); }}
        
        /* SVG Chart Styles */
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 200px;
        }}
        .bar {{ fill: var(--chart1); transition: opacity 0.2s; }}
        .bar:hover {{ opacity: 0.8; }}
        .pie-slice {{ transition: transform 0.2s; cursor: pointer; }}
        .pie-slice:hover {{ transform: scale(1.05); }}
        text {{ fill: var(--muted); font-size: 10px; }}
        .legend {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
            font-size: 0.8rem;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Codebase Fingerprint</h1>
            <p style="color: var(--muted)">Repository Analysis Report</p>
        </header>

        <div class="dashboard">
            <!-- Overview Stats -->
            <div class="card">
                <h2>Overview</h2>
                <div class="stat-grid">
                    <div class="stat-box">
                        <span class="stat-value">{stats['file_count']}</span>
                        <span class="stat-label">Files</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">{stats['total_lines']:,}</span>
                        <span class="stat-label">Lines</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">{stats['max_depth']}</span>
                        <span class="stat-label">Max Depth</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">{len(stats['extensions'])}</span>
                        <span class="stat-label">Languages</span>
                    </div>
                </div>
            </div>

            <!-- Language Breakdown (Pie Chart) -->
            <div class="card">
                <h2>Language Distribution</h2>
                <div class="chart-container">
                    <svg id="pieChart" width="200" height="200" viewBox="-100 -100 200 200"></svg>
                </div>
                <div id="pieLegend" class="legend"></div>
            </div>

            <!-- Largest Files -->
            <div class="card">
                <h2>Heavyweights</h2>
                <ul class="file-list">
                    {"".join([f'<li class="file-item"><span class="file-name" title="{f["path"]}">{f["name"]}</span><span class="file-size">{f["size"]/1024:.1f} KB</span></li>' for f in stats['largest_files']])}
                </ul>
            </div>

            <!-- File Activity (Bar Chart) -->
            <div class="card">
                <h2>Top Extensions</h2>
                <div class="chart-container">
                    <svg id="barChart" width="280" height="180"></svg>
                </div>
            </div>
        </div>
    </div>

    <script>
        const extData = {json.dumps(stats['extensions'])};
        const colors = ['#818cf8', '#fb7185', '#34d399', '#fbbf24', '#a78bfa', '#22d3ee', '#f472b6', '#94a3b8'];

        // Draw Pie Chart
        function drawPie() {{
            const svg = document.getElementById('pieChart');
            const legend = document.getElementById('pieLegend');
            const total = Object.values(extData).reduce((a, b) => a + b, 0);
            let startAngle = 0;

            Object.entries(extData).forEach(([label, value], i) => {{
                const sliceAngle = (value / total) * 2 * Math.PI;
                const x1 = Math.cos(startAngle) * 90;
                const y1 = Math.sin(startAngle) * 90;
                const x2 = Math.cos(startAngle + sliceAngle) * 90;
                const y2 = Math.sin(startAngle + sliceAngle) * 90;
                
                const largeArc = sliceAngle > Math.PI ? 1 : 0;
                const pathData = `M 0 0 L ${{x1}} ${{y1}} A 90 90 0 ${{largeArc}} 1 ${{x2}} ${{y2}} Z`;
                
                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                path.setAttribute("d", pathData);
                path.setAttribute("fill", colors[i % colors.length]);
                path.setAttribute("class", "pie-slice");
                svg.appendChild(path);

                // Add legend
                const item = document.createElement('div');
                item.className = 'legend-item';
                item.innerHTML = `<div class="dot" style="background:${{colors[i % colors.length]}}"></div><span>${{label}} (${{Math.round(value/total*100)}}%)</span>`;
                legend.appendChild(item);

                startAngle += sliceAngle;
            }});
        }}

        // Draw Bar Chart
        function drawBars() {{
            const svg = document.getElementById('barChart');
            const data = Object.entries(extData);
            const maxVal = Math.max(...data.map(d => d[1]));
            const barWidth = 30;
            const gap = 5;

            data.forEach(([label, value], i) => {{
                const barHeight = (value / maxVal) * 140;
                const x = i * (barWidth + gap) + 20;
                const y = 150 - barHeight;

                const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                rect.setAttribute("x", x);
                rect.setAttribute("y", y);
                rect.setAttribute("width", barWidth);
                rect.setAttribute("height", barHeight);
                rect.setAttribute("class", "bar");
                rect.setAttribute("rx", "4");
                svg.appendChild(rect);

                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", x + barWidth/2);
                text.setAttribute("y", 165);
                text.setAttribute("text-anchor", "middle");
                text.textContent = label;
                svg.appendChild(text);
            }});
        }}

        drawPie();
        drawBars();
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
    
    print(f"✨ Success! Infographic generated at: {os.path.abspath(output_file)}")