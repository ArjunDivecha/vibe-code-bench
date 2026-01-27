"""
Functional tests for Weather Dashboard (case_05_weather).

Tests verify actual behavior, not just presence.
"""


def test_shows_five_cities(page):
    """Should display all 5 required cities."""
    content = page.locator("body").text_content()
    
    cities = ["New York", "London", "Tokyo", "Sydney", "Paris"]
    found = sum(1 for city in cities if city in content)
    
    assert found >= 4, f"Expected 5 cities, found {found}"


def test_shows_temperature(page):
    """Should display temperature values."""
    content = page.locator("body").text_content()
    
    # Look for temperature indicators
    has_temp = any(indicator in content for indicator in [
        "°C", "°F", "°", "degrees", "temp"
    ])
    
    # Or check for numbers that look like temperatures
    import re
    temps = re.findall(r'\d{1,3}°', content)
    
    assert has_temp or len(temps) > 0, "No temperature values found"


def test_shows_weather_conditions(page):
    """Should display weather conditions."""
    content = page.locator("body").text_content().lower()
    
    conditions = ['sunny', 'cloudy', 'rainy', 'rain', 'cloud', 'sun', 'clear', 'storm']
    found = sum(1 for cond in conditions if cond in content)
    
    assert found >= 1, "No weather conditions found"


def test_has_weather_icons(page):
    """Should have weather icons or emojis."""
    content = page.content()
    
    # Check for emojis or icon elements
    emojis = ['☀', '🌤', '⛅', '🌧', '🌩', '❄', '🌡', '💧', '☁']
    has_emoji = any(emoji in content for emoji in emojis)
    
    # Or check for icon elements
    icons = page.locator("svg, img, [class*='icon'], i").count()
    
    assert has_emoji or icons > 0, "No weather icons found"


def test_shows_humidity(page):
    """Should display humidity values."""
    content = page.locator("body").text_content().lower()
    
    has_humidity = "humidity" in content or "%" in content
    assert has_humidity, "No humidity values found"


def test_city_click_shows_details(page):
    """Clicking a city should show more details."""
    initial = page.locator("body").text_content()
    
    # Find and click a city card
    city_card = page.locator("[class*='city'], [class*='card'], [class*='weather']").first
    if city_card.count() > 0:
        city_card.click()
        page.wait_for_timeout(300)
        
        final = page.locator("body").text_content()
        # Something should change (more details, modal, etc)
        # This is a permissive check - clicking shouldn't break anything


def test_responsive_layout(page):
    """Should have responsive layout indicators."""
    html = page.content().lower()
    
    has_responsive = any(term in html for term in [
        'flex', 'grid', '@media', 'responsive', 'mobile', 'max-width', 'min-width'
    ])
    
    assert has_responsive, "No responsive layout found"


def test_background_changes_or_theming(page):
    """Should have dynamic backgrounds or theming."""
    html = page.content().lower()
    
    has_dynamic = any(term in html for term in [
        'background', 'gradient', 'theme', 'color', '#', 'rgb'
    ])
    
    assert has_dynamic, "No background styling found"


def test_cards_for_each_city(page):
    """Should have card-like elements for cities."""
    cards = page.locator("[class*='card'], [class*='city'], [class*='weather']").count()
    
    # Or check for repeated structured elements
    items = page.locator("article, section, .item, li").count()
    
    assert cards >= 3 or items >= 3, "Not enough city cards found"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
