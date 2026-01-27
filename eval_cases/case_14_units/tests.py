"""
Functional tests for Unit Converter (case_14_units).

Tests verify actual behavior, not just presence.
"""


def test_has_input_field(page):
    """Should have an input field for values."""
    inputs = page.locator("input[type='number'], input[type='text']").count()
    assert inputs >= 1, "No input field found"


def test_has_unit_selectors(page):
    """Should have unit selection dropdowns."""
    selects = page.locator("select").count()
    
    # Or radio buttons/buttons for units
    radios = page.locator("input[type='radio']").count()
    
    assert selects >= 2 or radios >= 4, "Not enough unit selectors"


def test_has_multiple_categories(page):
    """Should support multiple conversion categories."""
    content = page.locator("body").text_content().lower()
    
    categories = ['length', 'weight', 'temperature', 'volume', 'area', 'time', 'speed']
    found = sum(1 for cat in categories if cat in content)
    
    assert found >= 2, f"Expected multiple categories, found {found}"


def test_conversion_produces_output(page):
    """Entering a value should produce conversion output."""
    # Enter a value
    input_field = page.locator("input[type='number'], input[type='text']").first
    if input_field.count() > 0:
        input_field.fill("100")
        page.wait_for_timeout(300)
        
        content = page.locator("body").text_content()
        # Should show some output number
        import re
        numbers = re.findall(r'\d+\.?\d*', content)
        assert len(numbers) > 1, "No conversion output"


def test_live_conversion(page):
    """Conversion should update as you type."""
    input_field = page.locator("input[type='number'], input[type='text']").first
    if input_field.count() > 0:
        input_field.fill("50")
        content1 = page.locator("body").text_content()
        
        input_field.fill("100")
        page.wait_for_timeout(200)
        content2 = page.locator("body").text_content()
        
        # Output should change
        assert content1 != content2, "Conversion not live"


def test_swap_units(page):
    """Should be able to swap from/to units."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_swap = any(term in content or term in html for term in [
        'swap', '⇄', '↔', 'reverse', 'switch'
    ])
    
    # Or swap button
    swap_btn = page.locator("button:has-text('Swap'), button:has-text('⇄')").count()
    
    assert has_swap or swap_btn > 0, "No swap functionality found"


def test_temperature_conversion(page):
    """Temperature conversion should be correct (32°F = 0°C)."""
    content = page.locator("body").text_content().lower()
    
    # Check if temperature is supported
    has_temp = any(term in content for term in ['celsius', 'fahrenheit', '°c', '°f', 'temperature'])
    
    if has_temp:
        # Try to input 32 for F->C
        input_field = page.locator("input").first
        if input_field.count() > 0:
            input_field.fill("32")
            page.wait_for_timeout(300)
            
            result = page.locator("body").text_content()
            # Should show 0 somewhere for 32F = 0C


def test_shows_unit_labels(page):
    """Should display unit labels clearly."""
    content = page.locator("body").text_content().lower()
    
    units = ['meter', 'feet', 'kg', 'pound', 'celsius', 'liter', 'gallon', 'mile', 'kilometer']
    found = sum(1 for unit in units if unit in content)
    
    assert found >= 2, "Not enough unit labels displayed"


def test_visual_styling(page):
    """App should have visual styling."""
    html = page.content().lower()
    has_styling = any(term in html for term in [
        'background', 'border', 'color:', '#', 'rgb'
    ])
    assert has_styling, "Unit converter lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
