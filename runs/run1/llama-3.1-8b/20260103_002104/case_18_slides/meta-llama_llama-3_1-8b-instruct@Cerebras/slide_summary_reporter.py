import os

def read_slides(directory):
    slides = {}
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), "r") as file:
                content = file.read()
                title = filename.replace(".txt", "")
                slides[title] = content
    return slides

def generate_report(slides):
    with open("report.html", "w") as report_file:
        report_file.write("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Slide Summary Reporter</title>
            <style>
                /* Premium CSS */
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f0f0f0;
                }
                .container {
                    max-width: 800px;
                    margin: 20px auto;
                    padding: 20px;
                    background-color: #fff;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .card {
                    background-color: #fff;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .card h2 {
                    margin-top: 0;
                }
                .summary {
                    background-color: #f5f5f5;
                    padding: 10px;
                    margin-bottom: 20px;
                }
                .toc {
                    background-color: #f5f5f5;
                    padding: 10px;
                    margin-bottom: 20px;
                }
                .print-button {
                    background-color: #4CAF50;
                    color: #fff;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                .print-button:hover {
                    background-color: #3e8e41;
                }
                @media print {
                    body {
                        margin: 0;
                        padding: 0;
                    }
                    .container {
                        margin: 0;
                        padding: 0;
                    }
                    .card {
                        page-break-inside: avoid;
                    }
                    .summary {
                        display: none;
                    }
                    .toc {
                        display: none;
                    }
                    .print-button {
                        display: none;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="summary">
                    <h2>Summary</h2>
                    <p id="summary-text"></p>
                </div>
                <div class="toc">
                    <h2>Table of Contents</h2>
                    <ul id="toc">
                    </ul>
                </div>
                <div class="cards">
                </div>
                <button class="print-button" onclick="window.print()">Print to PDF</button>
            </div>

            <script>
                function generateReport() {
                    const files = document.querySelector('.cards');
                    const summaryText = document.getElementById('summary-text');
                    const toc = document.getElementById('toc');

                    const slides = {};
                    const summary = [];

                    const filesArray = Array.from(document.querySelectorAll('.card'));
                    filesArray.forEach((file) => {
                        const title = file.querySelector('h2').textContent;
                        const content = file.querySelector('p').textContent;
                        slides[title] = content;
                        summary.push(content.split('\n')[0]);
                    });

                    summaryText.textContent = summary.join('\n');
                    toc.innerHTML = '';
                    Object.keys(slides).forEach((title, index) => {
                        toc.innerHTML += `<li><a href="#${title}">${title}</a></li>`;
                    });

                    files.innerHTML = '';
                    Object.keys(slides).forEach((title) => {
                        const card = document.createElement('div');
                        card.classList.add('card');
                        const h2 = document.createElement('h2');
                        h2.id = title;
                        h2.textContent = title;
                        card.appendChild(h2);
                        const p = document.createElement('p');
                        p.textContent = slides[title];
                        card.appendChild(p);
                        files.appendChild(card);
                    });
                }

                generateReport();
            </script>
        </body>
        </html>
        """)

        with open("report.html", "a") as report_file:
            for title, content in slides.items():
                report_file.write(f"""
                <div class="card" id="{title}">
                    <h2>{title}</h2>
                    <p>{content}</p>
                </div>
                """)

def main():
    directory = input("Enter the directory path: ")
    slides = read_slides(directory)
    generate_report(slides)

if __name__ == "__main__":
    main()