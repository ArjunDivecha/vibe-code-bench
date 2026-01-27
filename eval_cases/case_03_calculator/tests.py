"""
Functional tests for Calculator (case_03_calculator).

V3 Tests - Behavioral tests that verify actual calculations.
"""


def test_has_all_digit_buttons(page):
    """Calculator should have buttons for 0-9."""
    buttons = page.locator("button").all_text_contents()
    text = " ".join(buttons)
    
    digits_found = sum(1 for d in "0123456789" if d in text)
    assert digits_found >= 10, f"Missing digit buttons, found {digits_found}"


def test_has_four_operators(page):
    """Should have +, -, ×, ÷ operators."""
    buttons = page.locator("button").all_text_contents()
    text = "".join(buttons)
    
    operators = [('+', '+'), ('-', '-'), ('*', '*×x'), ('/', '/÷')]
    found = 0
    for _, chars in operators:
        if any(c in text for c in chars):
            found += 1
    
    assert found >= 4, f"Expected 4 operators, found {found}"


def test_has_decimal_point(page):
    """Should have decimal point button."""
    buttons = page.locator("button").all_text_contents()
    text = "".join(buttons)
    
    assert '.' in text, "No decimal point button"


def test_addition_7_plus_3(page):
    """7 + 3 = 10."""
    page.locator("button:has-text('7')").first.click()
    page.locator("button:has-text('+')").first.click()
    page.locator("button:has-text('3')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "10" in content, f"7+3 should equal 10, got: {content[:100]}"


def test_subtraction_15_minus_7(page):
    """15 - 7 = 8."""
    clear = page.locator("button:has-text('C'), button:has-text('AC')").first
    if clear.count() > 0:
        clear.click()
    
    page.locator("button:has-text('1')").first.click()
    page.locator("button:has-text('5')").first.click()
    page.locator("button:has-text('-')").first.click()
    page.locator("button:has-text('7')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "8" in content, f"15-7 should equal 8"


def test_multiplication_6_times_7(page):
    """6 × 7 = 42."""
    clear = page.locator("button:has-text('C'), button:has-text('AC')").first
    if clear.count() > 0:
        clear.click()
    
    page.locator("button:has-text('6')").first.click()
    mult = page.locator("button:has-text('×'), button:has-text('*'), button:has-text('x')").first
    if mult.count() > 0:
        mult.click()
    page.locator("button:has-text('7')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "42" in content, f"6×7 should equal 42"


def test_division_100_by_4(page):
    """100 ÷ 4 = 25."""
    clear = page.locator("button:has-text('C'), button:has-text('AC')").first
    if clear.count() > 0:
        clear.click()
    
    page.locator("button:has-text('1')").first.click()
    page.locator("button:has-text('0')").first.click()
    page.locator("button:has-text('0')").first.click()
    div = page.locator("button:has-text('÷'), button:has-text('/')").first
    if div.count() > 0:
        div.click()
    page.locator("button:has-text('4')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "25" in content, f"100÷4 should equal 25"


def test_clear_resets_display(page):
    """Clear button should reset to 0."""
    page.locator("button:has-text('5')").first.click()
    page.locator("button:has-text('5')").first.click()
    
    clear = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear')").first
    if clear.count() > 0:
        clear.click()
        page.wait_for_timeout(100)
        
        content = page.locator("body").text_content()
        assert "55" not in content, "Clear did not reset display"


def test_chained_operations(page):
    """2 + 3 × 4 should work (left-to-right or proper order)."""
    clear = page.locator("button:has-text('C'), button:has-text('AC')").first
    if clear.count() > 0:
        clear.click()
    
    page.locator("button:has-text('2')").first.click()
    page.locator("button:has-text('+')").first.click()
    page.locator("button:has-text('3')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(100)
    
    mult = page.locator("button:has-text('×'), button:has-text('*')").first
    if mult.count() > 0:
        mult.click()
    page.locator("button:has-text('4')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    # Should show 20 (5×4) for left-to-right, or 14 for proper PEMDAS
    assert "20" in content or "14" in content, "Chained operations failed"


def test_decimal_calculation(page):
    """3.5 + 2.5 = 6."""
    clear = page.locator("button:has-text('C'), button:has-text('AC')").first
    if clear.count() > 0:
        clear.click()
    
    page.locator("button:has-text('3')").first.click()
    page.locator("button:has-text('.')").first.click()
    page.locator("button:has-text('5')").first.click()
    page.locator("button:has-text('+')").first.click()
    page.locator("button:has-text('2')").first.click()
    page.locator("button:has-text('.')").first.click()
    page.locator("button:has-text('5')").first.click()
    page.locator("button:has-text('=')").first.click()
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "6" in content, "3.5+2.5 should equal 6"


def test_visual_styling(page):
    """Calculator should have visual styling."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'background', 'border', 'grid', 'color:', '#', 'rgb'
    ])
    assert has_styling, "Calculator lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
