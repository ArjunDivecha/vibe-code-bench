import os
import re
import json

# Calculate file counts by extension
file_counts = {}
for root, dirs, files in os.walk("."):
    for file in files:
        ext = os.path.splitext(file)[1]
        if ext not in file_counts:
            file_counts[ext] = 1
        else:
            file_counts[ext] += 1

# Calculate total lines of code
total_lines = 0
for root, dirs, files in os.walk("."):
    for file in files:
        if os.path.splitext(file)[1] in ['.py', '.js', '.java', '.cpp', '.c']:
            with open(os.path.join(root, file), 'r') as f:
                total_lines += sum(1 for line in f)

# Calculate largest files
largest_files = []
for root, dirs, files in os.walk("."):
    for file in files:
        size = os.path.getsize(os.path.join(root, file))
        if size > 1000000:
            largest_files.append((os.path.join(root, file), size))

# Calculate directory depth
def get_depth(path):
    return len(path.split('/'))

# Generate HTML infographic
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Fingerprint</title>
    <style>
        body {
            background-color: #333;
            color: #fff;
            font-family: Arial, sans-serif;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-gap: 20px;
            padding: 20px;
        }
        .chart {
            width: 100%;
            height: 200px;
            border: 1px solid #fff;
        }
        .pie-chart {
            width: 100%;
            height: 100%;
            position: relative;
        }
        .pie-chart .slice {
            fill: #fff;
            transition: transform 0.5s;
        }
        .pie-chart:hover .slice {
            transform: rotate(45deg);
        }
        .bar-chart {
            width: 100%;
            height: 100%;
            position: relative;
        }
        .bar-chart .bar {
            width: 0%;
            height: 100%;
            background-color: #fff;
            transition: width 0.5s;
        }
        .bar-chart:hover .bar {
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="chart">
            <svg class="pie-chart">
                <circle cx="50" cy="50" r="40" />
                """
for ext, count in file_counts.items():
    html += f"""
                <circle class="slice" cx="50" cy="50" r="40" fill="#{hex(ext)[2:]}" />
                <text x="50" y="80" fill="#fff">{ext}: {count}</text>
                """
html += """
            </svg>
        </div>
        <div class="chart">
            <svg class="bar-chart">
                <rect x="10" y="10" width="0" height="80" fill="#fff" />
                <text x="10" y="90" fill="#fff">Total lines of code: {total_lines}</text>
                """
for file, size in largest_files:
    html += f"""
                <rect class="bar" x="10" y="10" width="{size/1000000*100}%" height="80" fill="#fff" />
                <text x="10" y="90" fill="#fff">{os.path.basename(file)}: {size/1000000} MB</text>
                """
html += """
            </svg>
        </div>
        <div class="chart">
            <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                <rect x="50" y="50" width="100" height="100" fill="#fff" />
                """
for file in largest_files:
    html += f"""
                <circle cx="50" cy="50" r="40" fill="#{hex(os.path.getsize(file))[2:]}"></circle>
                <text x="50" y="120" fill="#fff">{os.path.basename(file)}</text>
                """
html += """
            </svg>
        </div>
    </div>
</body>
</html>
"""

# Save HTML infographic to file
with open("stats.html", "w") as f:
    f.write(html)

# Generate JavaScript for interactions
js = """
    <script>
        const charts = document.querySelectorAll('.chart');
        charts.forEach(chart => {
            chart.addEventListener('mouseover', () => {
                chart.classList.add('hover');
            });
            chart.addEventListener('mouseout', () => {
                chart.classList.remove('hover');
            });
        });
    </script>
"""

# Save JavaScript to file
with open("stats.js", "w") as f:
    f.write(js)

print("Git Stats Infographic Generator built successfully!")