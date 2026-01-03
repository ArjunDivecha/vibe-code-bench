# Log Analytics Dashboard

A Python-based log analytics dashboard that processes log files and serves an interactive web interface.

## Features

- **Auto-generates log data** if `server.log` doesn't exist (1000 lines of fake log data)
- **Parses and analyzes** log files to extract:
  - Percentage distribution of log levels (INFO, WARN, ERROR, CRITICAL)
  - Errors per hour timeline
  - Most common error messages
  - Critical error details
- **Interactive web dashboard** with:
  - Visual charts using SVG
  - Searchable critical error table
  - Filter by log level
  - Responsive design

## Usage

Run the script:
```bash
python log_analytics.py
```

The dashboard will be available at `http://localhost:8080`

## Requirements

- Python 3.x
- No external dependencies (uses only Python standard library)

## Dashboard Features

1. **Overview Statistics**: Shows total log entries and level distribution
2. **Timeline Chart**: Visual representation of errors per hour
3. **Top Errors**: Most frequently occurring error messages
4. **Critical Errors Table**: Searchable and filterable table of critical errors
5. **Interactive Elements**: 
   - Search functionality for critical errors
   - Filter buttons for different log levels

## Data Generation

If `server.log` doesn't exist, the script automatically generates 1000 lines of realistic log data with:
- Timestamps spread over the last 7 days
- Realistic log messages for each level
- Weighted distribution (more INFO, fewer CRITICAL)

## Technical Details

- Uses Python's `http.server` for the web server
- Pure HTML/CSS/JavaScript frontend (no external libraries)
- SVG-based charts
- JSON API endpoint at `/api/data`