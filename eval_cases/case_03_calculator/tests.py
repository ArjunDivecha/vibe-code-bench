"""
Functional tests for Calculator (case_03_calculator).

V3 Tests - More flexible, behavior-focused.
"""


def test_has_number_buttons(page):
    """Calculator should have number buttons 0-9."""
    content = page.locator("body").text_content()
    
    # Count digits found
    digits_found = sum(1 for d in "0123456789" if d in content)
    assert digits_found >= 10, f"Expected all digits 0-9, found {digits_found}"


def test_has_operator_buttons(page):
    """Should have +, -, *, / operators."""
    content = page.locator("body").text_content()
    
    # Check for operators (various representations)
    operators = ['+', '-', '×', '÷', '*', '/']
    found = sum(1 for op in operators if op in content)
    
    assert found >= 4, f"Expected 4 operators, found {found}"


def test_has_equals_button(page):
    """Should have equals button."""
    content = page.locator("body").text_content()
    
    has_equals = '=' in content or 'Enter' in content
    assert has_equals, "No equals button found"


def test_has_display_area(page):
    """Should have a display area for results."""
    # Look for display-like elements
    display = page.locator("input, [class*='display'], [class*='screen'], [class*='result']")
    
    assert display.count() > 0, "No display area found"


def test_basic_addition(page):
    """7 + 3 should equal 10."""
    # Click 7
    page.locator("button:has-text('7')").first.click()
    # Click +
    page.locator("button:has-text('+')").first.click()
    # Click 3
    page.locator("button:has-text('3')").first.click()
    # Click =
    page.locator("button:has-text('=')").first.click()
    
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "10" in content, f"7+3 should equal 10, got: {content[:100]}"


def test_basic_multiplication(page):
    """Clear and test 6 * 7 = 42."""
    # Try to clear first
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear')").first
    if clear_btn.count() > 0:
        clear_btn.click()
        page.wait_for_timeout(100)
    
    page.locator("button:has-text('6')").first.click()
    mult_btn = page.locator("button:has-text('×'), button:has-text('*'), button:has-text('x')").first
    if mult_btn.count() > 0:
        mult_btn.click()
    page.locator("button:has-text('7')").first.click()
    page.locator("button:has-text('=')").first.click()
    
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "42" in content, f"6*7 should equal 42, got: {content[:100]}"


def test_has_clear_button(page):
    """Should have a clear button."""
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear'), button:has-text('CE')")
    assert clear_btn.count() > 0, "No clear button found"


def test_visual_styling(page):
    """Calculator should have visual styling."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'background', 'border', 'grid', 'button', 'color:', '#', 'rgb'
    ])
    
    assert has_styling, "Calculator lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
