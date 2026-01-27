"""
Functional tests for Calculator (case_03_calculator).

Tests verify:
1. Number buttons work
2. Basic operations (+, -, ×, ÷)
3. Equals button computes result
4. Clear functionality
5. Decimal support
6. Display shows input/output
7. Keyboard input (optional)
"""


def test_has_number_buttons(page):
    """Calculator should have buttons for digits 0-9."""
    for digit in range(10):
        btn = page.locator(f"button:has-text('{digit}'), [class*='btn']:has-text('{digit}')")
        assert btn.count() > 0, f"No button for digit {digit}"


def test_has_operation_buttons(page):
    """Should have +, -, *, / buttons."""
    operations = ["+", "-", "×", "÷", "*", "/"]
    found = 0
    for op in operations:
        btn = page.locator(f"button:has-text('{op}')")
        if btn.count() > 0:
            found += 1
    assert found >= 4, f"Missing operation buttons, found {found}"


def test_has_equals_button(page):
    """Should have an equals button."""
    equals_btn = page.locator("button:has-text('='), button:has-text('Enter')")
    assert equals_btn.count() > 0, "No equals button found"


def test_has_clear_button(page):
    """Should have a clear button."""
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear'), button:has-text('CLR')")
    assert clear_btn.count() > 0, "No clear button found"


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
    
    # Check display shows 10
    content = page.locator("body").text_content()
    assert "10" in content, f"Expected 10 in display, got: {content[:100]}"


def test_basic_subtraction(page):
    """9 - 4 should equal 5."""
    # Clear first
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear')").first
    if clear_btn.count() > 0:
        clear_btn.click()
        page.wait_for_timeout(100)
    
    page.locator("button:has-text('9')").first.click()
    page.locator("button:has-text('-')").first.click()
    page.locator("button:has-text('4')").first.click()
    page.locator("button:has-text('=')").first.click()
    
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "5" in content, f"Expected 5 in display, got: {content[:100]}"


def test_basic_multiplication(page):
    """6 × 7 should equal 42."""
    # Clear first
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear')").first
    if clear_btn.count() > 0:
        clear_btn.click()
        page.wait_for_timeout(100)
    
    page.locator("button:has-text('6')").first.click()
    # Try both × and *
    mult_btn = page.locator("button:has-text('×'), button:has-text('*')").first
    mult_btn.click()
    page.locator("button:has-text('7')").first.click()
    page.locator("button:has-text('=')").first.click()
    
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "42" in content, f"Expected 42 in display, got: {content[:100]}"


def test_basic_division(page):
    """8 ÷ 2 should equal 4."""
    # Clear first
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear')").first
    if clear_btn.count() > 0:
        clear_btn.click()
        page.wait_for_timeout(100)
    
    page.locator("button:has-text('8')").first.click()
    # Try both ÷ and /
    div_btn = page.locator("button:has-text('÷'), button:has-text('/')").first
    div_btn.click()
    page.locator("button:has-text('2')").first.click()
    page.locator("button:has-text('=')").first.click()
    
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "4" in content, f"Expected 4 in display, got: {content[:100]}"


def test_has_decimal_button(page):
    """Should have a decimal point button."""
    decimal_btn = page.locator("button:has-text('.'), button:has-text(',')")
    assert decimal_btn.count() > 0, "No decimal button found"


def test_clear_resets_display(page):
    """Clear button should reset calculator."""
    # Enter some numbers
    page.locator("button:has-text('5')").first.click()
    page.locator("button:has-text('5')").first.click()
    
    # Click clear
    clear_btn = page.locator("button:has-text('C'), button:has-text('AC'), button:has-text('Clear')").first
    clear_btn.click()
    
    page.wait_for_timeout(200)
    
    # Display should be cleared (show 0 or empty)
    content = page.locator("body").text_content()
    # Shouldn't have 55 anymore
    assert "55" not in content, "Clear did not reset display"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
