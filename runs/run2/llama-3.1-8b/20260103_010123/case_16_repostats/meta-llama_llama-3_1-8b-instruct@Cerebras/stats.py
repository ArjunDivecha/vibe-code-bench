import os
import re

def get_file_count_by_extension():
    file_count = {}
    for root, dirs, files in os.walk("."):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in file_count:
                file_count[ext] += 1
            else:
                file_count[ext] = 1
    return file_count

def get_total_lines_of_code():
    total_lines = 0
    for root, dirs, files in os.walk("."):
        for file in files:
            with open(os.path.join(root, file), "r") as f:
                total_lines += sum(1 for line in f)
    return total_lines

def get_largest_files():
    largest_files = {}
    for root, dirs, files in os.walk("."):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if file_size in largest_files:
                largest_files[file_size].append(file_path)
            else:
                largest_files[file_size] = [file_path]
    return largest_files

def get_directory_depth():
    depth = 0
    current_path = os.getcwd()
    while True:
        depth += 1
        if current_path == os.path.dirname(current_path):
            break
        current_path = os.path.dirname(current_path)
    return depth

def generate_html(file_count, total_lines, largest_files, directory_depth):
    html = """
    <html>
    <head>
    <title>Codebase Fingerprint</title>
    <style>
    body {
      background-color: #1a1a1a;
      color: #ffffff;
      font-family: Arial, sans-serif;
    }
    #dashboard {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      grid-gap: 20px;
      padding: 20px;
    }
    #file-types {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    #file-types svg {
      width: 100px;
      height: 100px;
    }
    #total-lines {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    #total-lines svg {
      width: 100px;
      height: 100px;
    }
    #largest-files {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    #largest-files svg {
      width: 100px;
      height: 100px;
    }
    #directory-depth {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    #directory-depth svg {
      width: 100px;
      height: 100px;
    }
    </style>
    </head>
    <body>
    <div id="dashboard">
    <div id="file-types">
    <h2>File Types</h2>
    <svg width="100%" height="100%">
    <pie-chart data="{}</svg>
    </div>
    <div id="total-lines">
    <h2>Total Lines of Code</h2>
    <svg width="100%" height="100%">
    <bar-chart data="{}" />
    </svg>
    </div>
    <div id="largest-files">
    <h2>Largest Files</h2>
    <svg width="100%" height="100%">
    <bar-chart data="{}" />
    </svg>
    </div>
    <div id="directory-depth">
    <h2>Directory Depth</h2>
    <svg width="100%" height="100%">
    <bar-chart data="{}" />
    </svg>
    </div>
    </div>
    <script>
    const fileTypes = {};
    const totalLines = {};
    const largestFiles = {};
    const directoryDepth = {};
    for (const ext in {}) {{
      fileTypes[ext] = {};
    }}
    for (const file in {}) {{
      totalLines[file] = {};
    }}
    for (const fileSize in {}) {{
      largestFiles[fileSize] = {};
    }}
    for (const depth in {}) {{
      directoryDepth[depth] = {};
    }}
    const pieChart = document.getElementById("file-types").children[0];
    const barChart1 = document.getElementById("total-lines").children[0];
    const barChart2 = document.getElementById("largest-files").children[0];
    const barChart3 = document.getElementById("directory-depth").children[0];
    pieChart.innerHTML = ``;
    barChart1.innerHTML = ``;
    barChart2.innerHTML = ``;
    barChart3.innerHTML = ``;
    for (const ext in fileTypes) {{
      const sectorAngle = 360 / Object.keys(fileTypes).length;
      const sectorStartAngle = sectorAngle * Object.keys(fileTypes).indexOf(ext);
      const sectorEndAngle = sectorStartAngle + sectorAngle;
      const sectorColor = "#" + Math.floor(Math.random() * 16777215).toString(16);
      const label = document.createElement("text");
      label.setAttribute("x", 50);
      label.setAttribute("y", 50);
      label.textContent = ext + ": " + file_count[ext];
      pieChart.appendChild(label);
    }}
    for (const file in totalLines) {{
      const barHeight = totalLines[file] / total_lines * 100;
      const barLabel = document.createElement("text");
      barLabel.setAttribute("x", 50);
      barLabel.setAttribute("y", 50);
      barLabel.textContent = file + ": " + totalLines[file];
      barChart1.appendChild(barLabel);
    }}
    for (const fileSize in largestFiles) {{
      const barHeight = largestFiles[fileSize].length / total_lines * 100;
      const barLabel = document.createElement("text");
      barLabel.setAttribute("x", 50);
      barLabel.setAttribute("y", 50);
      barLabel.textContent = fileSize + ": " + largestFiles[fileSize].length;
      barChart2.appendChild(barLabel);
    }}
    for (const depth in directoryDepth) {{
      const barHeight = directoryDepth[depth] / directory_depth * 100;
      const barLabel = document.createElement("text");
      barLabel.setAttribute("x", 50);
      barLabel.setAttribute("y", 50);
      barLabel.textContent = depth + ": " + directoryDepth[depth];
      barChart3.appendChild(barLabel);
    }}
    </script>
    </body>
    </html>
    """

    # Populate HTML with data
    file_types_svg = "<svg><path d='M 50 50 L 50 0 A 50 50 0 1 1 0 50 Z' fill='#{}' /></svg>".format("#" + file_count.keys()[0])
    pie_chart = """
    <svg>
    <pie-chart>
    {}
    </pie-chart>
    </svg>
    """.format(file_types_svg)
    total_lines_svg = """
    <svg>
    <bar-chart>
    {}
    </bar-chart>
    </svg>
    """.format("".join("<rect y='{}' height='{}' fill='#{}' />".format(50 + i * 10, 10, "#{}") for i in range(total_lines)))
    largest_files_svg = """
    <svg>
    <bar-chart>
    {}
    </bar-chart>
    </svg>
    """.format("".join("<rect y='{}' height='{}' fill='#{}' />".format(50 + i * 10, 10, "#{}") for i in range(len(largest_files))))
    directory_depth_svg = """
    <svg>
    <bar-chart>
    {}
    </bar-chart>
    </svg>
    """.format("".join("<rect y='{}' height='{}' fill='#{}' />".format(50 + i * 10, 10, "#{}") for i in range(directory_depth)))

    # Replace placeholders with data
    html = html.format(pie_chart, total_lines_svg, largest_files_svg, directory_depth_svg)

    return html

# Execute function
file_count = get_file_count_by_extension()
total_lines = get_total_lines_of_code()
largest_files = get_largest_files()
directory_depth = get_directory_depth()
html = generate_html(file_count, total_lines, largest_files, directory_depth)

# Save HTML to file
with open("stats.html", "w") as f:
    f.write(html)