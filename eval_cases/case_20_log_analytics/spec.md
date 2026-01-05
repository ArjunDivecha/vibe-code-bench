# Build me a Log Analytics Dashboard

Create a Python script that:

1. Checks for a `server.log` file. If missing, it generates 1000 lines of fake log data (INFO, WARN, ERROR, CRITICAL) with timestamps.
2. Parses the log file to extract:
   - Percentage of each log level
   - Errors per hour (timeline)
   - Most common error messages
3. Generates a **standalone HTML dashboard file** (`dashboard.html`):
   - Use HTML/CSS/JS (vanilla)
   - Graphs for the trends (using SVG)
   - A searchable table of all CRITICAL errors
   - Filter by level (All, Error, Alert)
   - All data should be embedded in the HTML file as JavaScript variables

**Rules:**
- Python 3 Stdlib only (`json`, `collections`, `pathlib`, etc.)
- Script should exit after generating the dashboard file
- Output a message telling the user to open `dashboard.html` in their browser
