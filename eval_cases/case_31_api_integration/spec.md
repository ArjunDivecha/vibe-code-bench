# Build a Weather CLI Tool

Build a Python command-line tool that fetches and displays weather information. This task tests your ability to work with APIs, handle errors, and create a polished CLI interface.

## Requirements

### Core Functionality

1. **Weather data provider**: Use the Open-Meteo API (free, no key required)
   - Base URL: `https://api.open-meteo.com/v1/forecast`
   - Example: `?latitude=52.52&longitude=13.41&current_weather=true`

2. **Geocoding**: Convert city names to coordinates
   - Use Open-Meteo Geocoding: `https://geocoding-api.open-meteo.com/v1/search?name={city}`

3. **CLI interface** with these commands:
   ```
   python weather.py current "London"     # Current weather
   python weather.py forecast "Paris" 3   # 3-day forecast
   python weather.py --help               # Show help
   ```

### Output Format

Current weather should display:
```
Weather for London, GB
━━━━━━━━━━━━━━━━━━━━━━
🌡️  Temperature: 15°C
💨 Wind: 12 km/h NW
☁️  Conditions: Partly cloudy
📅 Updated: 2024-01-15 14:30
```

Forecast should show each day:
```
3-Day Forecast for Paris, FR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mon Jan 15: 🌤️  High 12°C / Low 5°C
Tue Jan 16: 🌧️  High 8°C / Low 3°C  
Wed Jan 17: ☀️  High 14°C / Low 6°C
```

### Error Handling

- Invalid city name: "City 'xyz' not found. Did you mean...?"
- Network errors: "Unable to connect. Check your internet connection."
- API errors: Display meaningful error message

### Technical Requirements

- Python 3 standard library only (`urllib`, `json`, `argparse`, `sys`)
- No external packages (no `requests`, no `rich`)
- Single Python file: `weather.py`
- Proper exit codes (0 for success, 1 for errors)

### Bonus Features (optional)

- Cache results to avoid repeated API calls
- Support for units (Celsius/Fahrenheit)
- Multiple cities in one command
- ASCII art weather icons

## Evaluation

You will be tested on:
1. Correct API integration
2. Clean CLI interface with help text
3. Proper error handling
4. Code organization and readability
