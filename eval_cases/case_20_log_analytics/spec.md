# Build me a Log Analytics Dashboard

Create a Python script that:

1. Checks for a `server.log` file. If missing, it generates 1000 lines of fake log data (INFO, WARN, ERROR, CRITICAL) with timestamps.
2. Parses the log file to extract:
   - Percentage of each log level
   - Errors per hour (timeline)
   - Most common error messages
3. Launches a **local HTTP server** (using `http.server`) that serves an interactive dashboard:
   - Use HTML/CSS/JS (vanilla)
   - Graphs for the trends (using SVG)
   - A searchable table of all CRITICAL errors
   - Filter by level (All, Error, Alert)

**Rules:**
- Python 3 Stdlib only (notably `http.server`, `json`, `collections`)
- The script should keep running until interrupted, providing the URL to the user.
