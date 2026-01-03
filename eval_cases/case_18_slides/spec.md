# Build me a Slide Summary Reporter

I have a directory of text files representing PowerPoint slides (e.g., `slide1.txt`, `slide2.txt`).

Create a Python tool that:
1. Reads all `.txt` files in the directory
2. Formats them into a **single, beautiful HTML report**
   - Each slide should be a "card" in the report
   - Auto-generate a "Table of Contents" at the top
   - Add a "Summary" section at the top that combines the first few lines of every slide
3. Visuals:
   - Use extremely premium CSS (Typography, Shadows, Spacing)
   - Add a "Print to PDF" button (which just triggers `window.print()`)
   - Page-break CSS so it prints nicely

**Rules:**
- Python 3 Stdlib only
- The Python script should create a `report.html`
- No external libraries
