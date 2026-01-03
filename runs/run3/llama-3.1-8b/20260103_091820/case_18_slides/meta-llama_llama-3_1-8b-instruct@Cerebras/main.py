import os

def generate_report(directory):
    # Read all .txt files in the directory
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    # Create a report HTML
    with open('report.html', 'w') as f:
        f.write('<html>')
        
        # Generate Table of Contents
        f.write('<div class="table-of-contents">')
        f.write('<h1>Table of Contents</h1>')
        f.write('<ul>')
        for file in files:
            f.write('<li>{}</li>'.format(file))
        f.write('</ul>')
        f.write('</div>')
        
        # Generate Summary
        f.write('<div class="summary">')
        f.write('<h2>Summary</h2>')
        f.write('<p>This is a summary of the slides:</p>')
        for file in files:
            with open(os.path.join(directory, file), 'r') as sf:
                lines = sf.readlines()[:2]  # Take the first 2 lines
                f.write('<p>{}: {}</p>'.format(file, lines[0].strip()))
                f.write('<p>{}: {}</p>'.format(file, lines[1].strip()))
        f.write('</div>')
        
        # Generate Slide Cards
        f.write('<button class="print-button" onclick="window.print()">Print to PDF</button>')
        f.write('<div class="cards">')
        for file in files:
            with open(os.path.join(directory, file), 'r') as sf:
                lines = sf.readlines()
                f.write('<div class="card">')
                f.write('<h2>{}</h2>'.format(file))
                for line in lines:
                    f.write('<p>{}</p>'.format(line.strip()))
                f.write('</div>')
        f.write('</div>')
        f.write('</html>')

# Usage
generate_report('slides')