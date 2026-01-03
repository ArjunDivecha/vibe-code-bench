import os
import json
from collections import defaultdict
import re

def calculate_stats():
    file_counts = defaultdict(int)
    total_lines = 0
    largest_files = []
    max_depth = 0

    for root, dirs, files in os.walk("."):
        depth = root.count("/")
        if depth > max_depth:
            max_depth = depth

        for file in files:
            path = os.path.join(root, file)
            file_counts[os.path.splitext(file)[1][1:] + " files"] += 1
            with open(path, "r") as f:
                lines = sum(1 for line in f)
                total_lines += lines
                if lines > 1000:
                    largest_files.append((lines, path))

    return {
        "file_counts": dict(file_counts),
        "total_lines": total_lines,
        "largest_files": largest_files,
        "max_depth": max_depth,
    }

def generate_html(stats):
    html = """
    <html>
    <head>
    <title>Codebase Fingerprint</title>
    <style>
    body {
        background-color: #2f343a;
        color: #f7f7f7;
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        grid-gap: 20px;
    }
    .chart {
        width: 200px;
        height: 200px;
    }
    </style>
    </head>
    <body>
    <h1>Codebase Fingerprint</h1>
    <div class="grid">
    <div>
    <h2>File Types</h2>
    <svg class="chart" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="45" fill="#3498db" />
    <circle cx="50" cy="50" r="35" fill="#2ecc71" />
    <circle cx="50" cy="50" r="25" fill="#f1c40f" />
    <circle cx="50" cy="50" r="15" fill="#e74c3c" />
    <circle cx="50" cy="50" r="5" fill="#9b59b6" />
    </svg>
    <div>
    <p>%.2f%% Python files</p>
    <p>%.2f%% JavaScript files</p>
    <p>%.2f%% CSS files</p>
    <p>%.2f%% Other files</p>
    </div>
    </div>
    <div>
    <h2>Line Counts</h2>
    <svg class="chart" viewBox="0 0 100 100">
    <rect x="10" y="10" width="80" height="80" fill="#3498db" />
    <rect x="10" y="10" width="60" height="60" fill="#2ecc71" />
    <rect x="10" y="10" width="40" height="40" fill="#f1c40f" />
    <rect x="10" y="10" width="20" height="20" fill="#e74c3c" />
    </svg>
    <div>
    <p>%.2fK lines</p>
    <p>%.2fK lines</p>
    <p>%.2fK lines</p>
    <p>%.2fK lines</p>
    </div>
    </div>
    </div>
    <div>
    <h2>Largest Files</h2>
    <ul>
    """ % (
        stats["file_counts"][".py"] / sum(stats["file_counts"].values()) * 100,
        stats["file_counts"][".js"] / sum(stats["file_counts"].values()) * 100,
        stats["file_counts"][".css"] / sum(stats["file_counts"].values()) * 100,
        100 - sum(stats["file_counts"].values()) / sum(stats["file_counts"].values()) * 100,
        stats["total_lines"] / 1000,
        stats["largest_files"][1][0] / 1000,
        stats["largest_files"][2][0] / 1000,
        stats["largest_files"][3][0] / 1000,
    )

    for lines, path in stats["largest_files"]:
        html += f"<li>{path}: {lines} lines</li>"

    html += """
    </ul>
    </div>
    <div>
    <h2>Directory Depth</h2>
    <p>Max depth: {max_depth}</p>
    </div>
    </body>
    </html>
    """.format(max_depth=stats["max_depth"])

    return html

def main():
    stats = calculate_stats()
    with open("stats.html", "w") as f:
        f.write(generate_html(stats))

if __name__ == "__main__":
    main()