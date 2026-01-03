# Slide Summary Reporter

A Python tool that converts text slides into a beautiful HTML report with premium styling.

## Usage

1. Place your slide text files in a directory (e.g., `slide1.txt`, `slide2.txt`, etc.)

2. Run the generator:
```bash
python generate_report.py [directory]
```

If no directory is specified, it uses the current directory.

3. Open the generated `report.html` in a browser

4. Click "Print to PDF" to save as a PDF file

## Features

- **Executive Summary**: Auto-generated summary from first lines of each slide
- **Table of Contents**: Interactive navigation to each slide
- **Premium Design**: Beautiful typography, shadows, and spacing
- **Print-Friendly**: Proper page breaks for PDF export
- **Responsive**: Works on all screen sizes

## Example

```bash
# Generate report from current directory
python generate_report.py

# Generate report from specific directory
python generate_report.py ./my-slides/
```

## File Format

Each `.txt` file should contain the slide content. The filename will be used as the slide title (e.g., `slide1.txt` → "Slide 1").

Content can include:
- Multiple paragraphs (separated by blank lines)
- Lists
- Any plain text content

The tool automatically:
- Sorts slides naturally (slide1, slide2, ..., slide10, slide11)
- Escapes HTML characters
- Formats paragraphs
- Extracts summaries

No external dependencies required - uses only Python standard library!