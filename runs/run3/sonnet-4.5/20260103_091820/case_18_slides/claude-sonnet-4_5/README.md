# Slide Summary Reporter

A Python tool that generates beautiful HTML reports from text slide files.

## Usage

```bash
# Generate report from current directory
python slide_reporter.py

# Generate report from specific directory
python slide_reporter.py /path/to/slides
```

## Features

- ✨ Premium CSS styling with gradients and shadows
- 📑 Auto-generated Table of Contents
- 📝 Executive Summary section
- 🎴 Beautiful slide cards
- 🖨️ Print to PDF functionality
- 📱 Responsive design
- 🎨 Print-optimized CSS with page breaks

## Example

The repository includes 5 sample slides (slide1.txt - slide5.txt) demonstrating a Machine Learning presentation.

Run the script to generate `report.html`:

```bash
python slide_reporter.py
```

Then open `report.html` in your browser and click "Print to PDF" to save!

## Requirements

- Python 3.6+
- No external dependencies (uses only stdlib)

## Output

The script generates a single `report.html` file with:
- Elegant header with gradient background
- Table of Contents with clickable links
- Executive Summary showing first 2 lines of each slide
- Detailed slide cards with full content
- Print-friendly CSS for PDF generation