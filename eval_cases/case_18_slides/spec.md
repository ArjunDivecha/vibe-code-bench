# Build me a Slide Summary Reporter

Create a Python tool that processes presentation slides and generates an HTML report.

Create a Python tool that:
1. **If no `.txt` files exist in current directory**, auto-generate 5 sample slide files (`slide1.txt` through `slide5.txt`) with realistic presentation content (e.g., quarterly report data)
2. Reads all `.txt` files in the current directory
3. Formats them into a **single, beautiful HTML report**
   - Each slide should be a "card" in the report
   - Auto-generate a "Table of Contents" at the top
   - Add a "Summary" section at the top that combines the first few lines of every slide
4. Visuals:
   - Use extremely premium CSS (Typography, Shadows, Spacing)
   - Add a "Print to PDF" button (which just triggers `window.print()`)
   - Page-break CSS so it prints nicely

**Rules:**
- Python 3 Stdlib only
- The Python script should create a `report.html`
- No external libraries
- Script must work standalone (generate sample data if needed)
