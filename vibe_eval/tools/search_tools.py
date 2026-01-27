"""
Search tools for the agent.

Provides simulated web search for documentation lookup.
Note: This is a mock implementation for evaluation purposes.
"""

from typing import Optional


# Simulated documentation database
MOCK_DOCS = {
    "open-meteo": {
        "title": "Open-Meteo API Documentation",
        "url": "https://open-meteo.com/en/docs",
        "content": """
# Open-Meteo Weather API

Free weather API with no API key required.

## Endpoints

### Current Weather
GET https://api.open-meteo.com/v1/forecast

Parameters:
- latitude (required): Latitude in decimal degrees
- longitude (required): Longitude in decimal degrees
- current_weather=true: Get current conditions

Example:
https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true

Response:
{
  "current_weather": {
    "temperature": 15.2,
    "windspeed": 12.3,
    "winddirection": 180,
    "weathercode": 2,
    "time": "2024-01-15T12:00"
  }
}

### Geocoding API
GET https://geocoding-api.open-meteo.com/v1/search

Parameters:
- name (required): City name to search

Example:
https://geocoding-api.open-meteo.com/v1/search?name=London

Response:
{
  "results": [
    {
      "name": "London",
      "latitude": 51.5074,
      "longitude": -0.1278,
      "country": "United Kingdom",
      "country_code": "GB"
    }
  ]
}

Weather Codes:
0: Clear sky
1-3: Partly cloudy
45-48: Fog
51-55: Drizzle
61-65: Rain
71-75: Snow
95-99: Thunderstorm
"""
    },
    
    "python argparse": {
        "title": "Python argparse Documentation",
        "url": "https://docs.python.org/3/library/argparse.html",
        "content": """
# argparse — Parser for command-line options

## Basic Usage

```python
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('integers', metavar='N', type=int, nargs='+',
                    help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=sum, default=max,
                    help='sum the integers (default: find the max)')

args = parser.parse_args()
```

## Subcommands

```python
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

# Create subcommand
parser_a = subparsers.add_parser('command_a', help='Command A help')
parser_a.add_argument('foo', type=int, help='foo help')

args = parser.parse_args()
if args.command == 'command_a':
    print(args.foo)
```
"""
    },
    
    "python urllib": {
        "title": "Python urllib Documentation",
        "url": "https://docs.python.org/3/library/urllib.html",
        "content": """
# urllib — URL handling modules

## urllib.request — Extensible library for opening URLs

```python
import urllib.request
import json

# Simple GET request
url = 'https://api.example.com/data'
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())

# With timeout
with urllib.request.urlopen(url, timeout=10) as response:
    html = response.read()

# With headers
req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')
with urllib.request.urlopen(req) as response:
    data = response.read()
```

## urllib.parse — Parse URLs

```python
from urllib.parse import urlencode, quote

# Build query string
params = {'name': 'London', 'count': 5}
query = urlencode(params)  # 'name=London&count=5'

# URL encode
safe_string = quote('hello world')  # 'hello%20world'
```
"""
    },
    
    "python unittest": {
        "title": "Python unittest Documentation", 
        "url": "https://docs.python.org/3/library/unittest.html",
        "content": """
# unittest — Unit testing framework

## Basic Test Case

```python
import unittest

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
```

## Assertions

- assertEqual(a, b)
- assertNotEqual(a, b)
- assertTrue(x)
- assertFalse(x)
- assertIs(a, b)
- assertIsNot(a, b)
- assertIsNone(x)
- assertIsNotNone(x)
- assertIn(a, b)
- assertRaises(exc, fun, *args, **kwds)
"""
    }
}


def web_search_tool(query: str) -> dict:
    """
    Simulate web search for documentation.
    
    This is a mock implementation that returns predefined documentation
    for common queries. In a real implementation, this would make actual
    web requests.
    
    Args:
        query: Search query string
        
    Returns:
        Dict with search results
    """
    query_lower = query.lower()
    
    results = []
    
    # Search through mock docs
    for key, doc in MOCK_DOCS.items():
        if any(term in query_lower for term in key.split()):
            results.append({
                "title": doc["title"],
                "url": doc["url"],
                "snippet": doc["content"][:500] + "..."
            })
    
    if not results:
        # Return generic "no results" response
        return {
            "success": True,
            "query": query,
            "results": [],
            "message": f"No documentation found for '{query}'. Try a different search term."
        }
    
    return {
        "success": True,
        "query": query,
        "results": results,
        "message": f"Found {len(results)} result(s)"
    }


def get_documentation(topic: str) -> Optional[str]:
    """
    Get full documentation for a known topic.
    
    Args:
        topic: Topic key (e.g., "open-meteo", "python argparse")
        
    Returns:
        Full documentation content or None if not found
    """
    topic_lower = topic.lower()
    
    for key, doc in MOCK_DOCS.items():
        if topic_lower in key or key in topic_lower:
            return doc["content"]
    
    return None
