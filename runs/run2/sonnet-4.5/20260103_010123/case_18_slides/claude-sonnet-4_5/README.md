# Slide Summary Reporter

A Python tool that converts text files into a beautiful HTML report.

## Usage

1. **Basic usage** (reads .txt files from current directory):
   ```bash
   python slide_reporter.py
   ```

2. **Specify a directory**:
   ```bash
   python slide_reporter.py /path/to/slides
   ```

3. **View the report**:
   - Open `report.html` in your browser
   - Click "Print to PDF" button to save as PDF

## Slide Format

Each `.txt` file should follow this format:
- **First line**: Slide title
- **Remaining lines**: Slide content

Example (`slide1.txt`):
```
Introduction to Machine Learning
Welcome to this comprehensive overview of Machine Learning fundamentals.
In this presentation, we'll explore key concepts and practical applications.
```

## Features

✨ **Beautiful Design**
- Premium typography and spacing
- Smooth shadows and transitions
- Gradient accents
- Responsive layout

📑 **Table of Contents**
- Auto-generated with links
- Numbered entries
- Quick navigation

✨ **Executive Summary**
- Combines first 3 lines from each slide
- Highlighted section
- Quick overview

🖨️ **Print-Friendly**
- One-click print to PDF
- Optimized page breaks
- Clean print layout

## Sample Output

Run the script in this directory to see the sample report generated from the 5 example slides included.