# Slide Summary Reporter 🎨

Transform your text-based slide files into a beautiful, professional HTML report with just one command!

## Features

✨ **Premium Design**: Beautiful typography, shadows, and spacing  
📚 **Auto Table of Contents**: Navigate your slides easily  
📝 **Executive Summary**: Auto-generated summary of key points  
📄 **Print to PDF**: Built-in print functionality  
📱 **Responsive**: Works perfectly on all devices  
🎯 **Zero Dependencies**: Python stdlib only  

## Quick Start

1. **Create demo slides** (optional):
   ```bash
   python demo_slides.py
   ```

2. **Generate the report**:
   ```bash
   python slide_reporter.py
   ```

3. **Open `report.html`** in your browser

## Usage

```bash
# Basic usage - scan current directory
python slide_reporter.py

# Specify custom directory
python slide_reporter.py --directory ./my-slides

# Custom output filename
python slide_reporter.py --output presentation.html
```

## Slide File Format

Create `.txt` files in your directory with content like:

```
# Slide Title

Main content here
- Bullet point 1
- Bullet point 2

Additional information
```

The tool automatically detects:
- Headers (lines starting with #)
- Bullet points (lines starting with - or *)
- Numbered lists (lines starting with numbers)
- Regular paragraphs

## Report Features

### 📋 Table of Contents
- Auto-generated from your slide titles
- Click to navigate to any slide
- Beautiful card-based design

### 📝 Executive Summary
- Combines first few lines from each slide
- Grid layout for easy scanning
- Highlighted with premium styling

### 🎨 Premium Styling
- Professional color scheme
- Smooth shadows and transitions
- Print-optimized CSS
- Mobile-responsive design

### 📄 Print Support
- Click "Print to PDF" button
- Optimized page breaks
- Clean print layout
- Professional formatting

## Customization

The CSS variables in the generated HTML make it easy to customize:
- `--primary-color`: Main theme color
- `--secondary-color`: Secondary elements
- `--accent-color`: Highlights and CTAs
- `--shadow-*`: Shadow depths

## Requirements

- Python 3.6+
- No external dependencies
- Works on Windows, macOS, Linux

## Example Output

The generated report includes:
1. Beautiful header with gradient background
2. Interactive Table of Contents
3. Executive Summary section
4. Individual slide cards with premium styling
5. Print functionality
6. Smooth scrolling navigation
7. Responsive design for all devices

Enjoy your beautiful slide reports! 🚀