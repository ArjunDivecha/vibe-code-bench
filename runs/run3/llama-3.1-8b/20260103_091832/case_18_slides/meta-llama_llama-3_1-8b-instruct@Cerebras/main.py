import os

def create_report():
    with open("report.html", "w") as f:
        with open("report.html") as g:
            html = g.read()
            toc = ""
            summary = ""
            files = os.listdir()
            for file in files:
                if file.endswith(".txt"):
                    with open(file) as h:
                        contents = h.read()
                        heading = contents.split("\n")[0]
                        toc += f"<li>{heading}</li>\n"
                        summary += heading + "<br>"
                        text = contents.split("\n")[1:]
                        text = "<br>".join(text)
                        html = html.replace("<p id='summary-text'></p>", f"<p id='summary-text'>{summary}</p>")
                        html = html.replace("<ul id='toc'></ul>", f"<ul id='toc'>{toc}</ul>")
                        html = html.replace("<div id='slides'></div>", f"<div id='slides'><div class='card'>{text}</div></div>")
            f.write(html)

if __name__ == "__main__":
    create_report()