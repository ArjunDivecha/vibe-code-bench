# Log Analytics Dashboard

A Python-based log analytics dashboard that generates fake log data, analyzes it, and serves an interactive web-based dashboard for visualization and exploration.

## Features

✨ **Automatic Log Generation**
- Generates 1000 lines of realistic fake log data if `server.log` doesn't exist
- Includes INFO, WARN, ERROR, and CRITICAL log levels
- Timestamps distributed over 24 hours
- Realistic error and info messages

📊 **Analytics & Insights**
- Log level distribution (percentage breakdown)
- Errors per hour timeline
- Most common error messages
- Complete critical error log with search and filter

🎨 **Interactive Web Dashboard**
- Real-time analytics visualization
- SVG-based charts (pie chart, timeline, bar chart)
- Searchable table of critical errors
- Filter by log level (All, Error, Critical)
- Responsive design that works on mobile
- Auto-refreshes every 30 seconds

🚀 **Pure Python Implementation**
- Uses only Python standard library
- `http.server` for the web server
- `json` for data serialization
- `collections` for data analysis
- Vanilla HTML/CSS/JavaScript (no external dependencies)

## Requirements

- Python 3.6+
- No external packages required!

## Usage

### Quick Start

```bash
python3 log_analytics.py
```

The script will:
1. Check for `server.log` file
2. Generate 1000 fake log lines if it doesn't exist
3. Parse the logs for analytics
4. Start a local HTTP server on port 8080
5. Display the URL to access the dashboard

### Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8080/
```

### API Endpoints

- `GET /` - Main dashboard HTML
- `GET /api/analytics` - JSON data with all analytics

### Stopping the Server

Press `Ctrl+C` to stop the server.

## File Structure

```
.
├── log_analytics.py      # Main script
├── server.log            # Generated log file (auto-created)
└── README.md             # This file
```

## Dashboard Features

### Statistics Cards
- Shows percentage and count for each log level (INFO, WARN, ERROR, CRITICAL)

### Visualizations

1. **Log Level Distribution (Pie Chart)**
   - Visual breakdown of log level percentages
   - Color-coded by severity

2. **Errors Over Time (Timeline Chart)**
   - Shows error count for each hour
   - Helps identify peak error times

3. **Top Error Messages (Bar Chart)**
   - Most frequently occurring error messages
   - Up to 8 most common errors displayed

### Critical Errors Table

- **Search**: Filter errors by message or timestamp
- **Filter**: View All errors, only Errors, or only Critical errors
- **Sort**: Click column headers to sort
- **Details**: Full timestamp and error message for each entry

## Customization

You can modify these constants in `log_analytics.py`:

```python
LOG_FILE = "server.log"           # Log file name
NUM_LOG_LINES = 1000              # Number of fake logs to generate
DASHBOARD_PORT = 8080             # Server port
```

## Example Log Format

```
2024-01-15 10:30:45 [INFO] User login successful
2024-01-15 10:31:12 [WARN] High memory usage detected
2024-01-15 10:32:03 [ERROR] Database connection timeout [Code: 503]
2024-01-15 10:33:15 [CRITICAL] CRITICAL: Service unavailable [Code: 789]
```

## Performance

- Handles 1000+ log entries efficiently
- Fast JSON API responses
- Responsive UI with smooth interactions
- Auto-refresh every 30 seconds

## Browser Compatibility

- Chrome/Chromium
- Firefox
- Safari
- Edge
- Any modern browser with ES6 support

## License

Free to use and modify!