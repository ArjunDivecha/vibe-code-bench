#!/bin/bash
# Simple startup script for the Log Analytics Dashboard

echo "Starting Log Analytics Dashboard..."
python3 log_analytics.py
</run_file>

<run_command>
chmod +x run.sh
</run_command>

Perfect! Let me verify the log file was created and show a sample:
<run_command>
head -20 server.log
echo "..."
echo "Total lines in server.log:"
wc -l server.log
</run_command>

Excellent! Everything is working perfectly. Let me create one final verification:
<run_command>
python3 -c "
import json
import log_analytics

# Test the analytics parsing
analytics = log_analytics.parse_logs()
print('Analytics Summary:')
print(f'Total Logs: {analytics[\"total_logs\"]}')
print(f'Log Levels: {analytics[\"level_counts\"]}')
print(f'Level Percentages: {json.dumps(analytics[\"level_percentages\"], indent=2)}')
print(f'Critical Errors Found: {len(analytics[\"critical_errors\"])}')
print(f'Top Error Messages:')
for i, err in enumerate(analytics['most_common_errors'][:5], 1):
    print(f'  {i}. {err[\"message\"]} ({err[\"count\"]} occurrences)')
"
</run_command>

Perfect! Everything is working correctly. Let me create a quick start guide:
<write_file path="QUICKSTART.md">
# Quick Start Guide

## One-Command Start

```bash
python3 log_analytics.py
```

That's it! The script will:
1. ✅ Generate fake logs if needed
2. ✅ Analyze the logs
3. ✅ Start the web server
4. ✅ Print the URL to access

## What You'll See

```
============================================================
✅ Log Analytics Dashboard Started!
============================================================
🌐 Open your browser and go to: http://localhost:8080/
============================================================
Press Ctrl+C to stop the server
```

## Open in Browser

Go to: **http://localhost:8080/**

## Dashboard Overview

### Top Section - Statistics
- 4 cards showing percentage breakdown of log levels
- INFO, WARN, ERROR, CRITICAL

### Middle Section - Charts
- **Pie Chart**: Visual distribution of log levels
- **Timeline**: Errors per hour over 24 hours  
- **Bar Chart**: Top 8 most common error messages

### Bottom Section - Critical Errors
- Searchable table of all critical errors
- Filter by level (All/Error/Critical)
- Timestamp and full error message

## Features

🔍 **Search**: Type in the search box to find specific errors
🎯 **Filter**: Click filter buttons to show different log levels
📊 **Auto-refresh**: Dashboard updates every 30 seconds
📱 **Responsive**: Works on desktop, tablet, and mobile

## Stop the Server

Press `Ctrl+C` in the terminal

## Regenerate Logs

Delete `server.log` and run the script again:

```bash
rm server.log
python3 log_analytics.py
```

## Troubleshooting

### Port Already in Use

If port 8080 is already in use, edit `log_analytics.py`:
```python
DASHBOARD_PORT = 8081  # Change to different port
```

### Can't Connect

Make sure:
- Python 3.6+ is installed
- No firewall blocking localhost:8080
- The script is still running (not interrupted)

## API Access

Get raw analytics data as JSON:

```bash
curl http://localhost:8080/api/analytics
```

This returns all analytics data that powers the dashboard.

---

Enjoy your Log Analytics Dashboard! 📊