import os
import json

def generate_report():
    slides = []
    with open('slides.json', 'w') as f:
        for filename in os.listdir('.'):
            if filename.endswith('.txt'):
                with open(filename, 'r') as file:
                    slides.append(file.read())
        json.dump(slides, f, indent=4)

    with open('report.html', 'w') as f:
        with open('report.html.template', 'r') as template:
            content = template.read()
            f.write(content.replace('<%= slides_json %>', json.dumps(slides)))

if __name__ == '__main__':
    generate_report()