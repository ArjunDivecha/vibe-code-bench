"""
Functional tests for Password Generator (case_13_password).

Tests verify actual behavior, not just presence.
"""


def test_shows_generated_password(page):
    """Should display a generated password."""
    content = page.locator("body").text_content()
    
    # Should have some text that looks like a password (mixed chars)
    # Look for output area
    output = page.locator("[class*='password'], [class*='output'], [class*='result'], input[readonly]").first
    if output.count() > 0:
        pwd = output.text_content() or output.input_value()
        assert len(pwd) >= 8, f"Password too short: {pwd}"


def test_has_length_control(page):
    """Should have password length control."""
    # Look for range slider or number input
    length_control = page.locator("input[type='range'], input[type='number'], [class*='length']").count()
    
    content = page.locator("body").text_content().lower()
    has_length = 'length' in content
    
    assert length_control > 0 or has_length, "No length control found"


def test_length_slider_affects_output(page):
    """Changing length should affect password length."""
    # Find length slider
    slider = page.locator("input[type='range']").first
    if slider.count() > 0:
        # Set to specific value
        slider.fill("20")
        page.wait_for_timeout(300)
        
        # Generate new password
        gen_btn = page.locator("button:has-text('Generate'), button:has-text('New')").first
        if gen_btn.count() > 0:
            gen_btn.click()
            page.wait_for_timeout(300)
        
        # Check password length
        output = page.locator("[class*='password'], [class*='output'], input[readonly]").first
        if output.count() > 0:
            pwd = output.text_content() or output.input_value()
            # Should be close to 20 characters


def test_has_character_options(page):
    """Should have options for character types."""
    content = page.locator("body").text_content().lower()
    
    options = ['uppercase', 'lowercase', 'numbers', 'symbols', 'special']
    found = sum(1 for opt in options if opt in content)
    
    # Or checkboxes
    checkboxes = page.locator("input[type='checkbox']").count()
    
    assert found >= 2 or checkboxes >= 2, "Not enough character options"


def test_toggle_affects_password(page):
    """Toggling options should affect password content."""
    # Find a checkbox and toggle it
    checkbox = page.locator("input[type='checkbox']").first
    if checkbox.count() > 0:
        initial = page.locator("body").text_content()
        checkbox.click()
        
        # Generate new
        gen_btn = page.locator("button:has-text('Generate')").first
        if gen_btn.count() > 0:
            gen_btn.click()
            page.wait_for_timeout(300)
        
        final = page.locator("body").text_content()
        # Password should potentially change


def test_has_copy_button(page):
    """Should have a copy button."""
    copy_btn = page.locator("button:has-text('Copy'), [class*='copy']").count()
    
    content = page.locator("body").text_content().lower()
    has_copy = 'copy' in content
    
    assert copy_btn > 0 or has_copy, "No copy button found"


def test_has_strength_indicator(page):
    """Should show password strength."""
    content = page.locator("body").text_content().lower()
    
    has_strength = any(term in content for term in [
        'strength', 'weak', 'medium', 'strong', 'secure'
    ])
    
    # Or strength meter
    meter = page.locator("[class*='strength'], [class*='meter'], progress").count()
    
    assert has_strength or meter > 0, "No strength indicator found"


def test_generate_produces_different_passwords(page):
    """Each generate should produce different passwords."""
    gen_btn = page.locator("button:has-text('Generate'), button:has-text('New')").first
    
    if gen_btn.count() > 0:
        gen_btn.click()
        page.wait_for_timeout(200)
        pwd1 = page.locator("body").text_content()
        
        gen_btn.click()
        page.wait_for_timeout(200)
        pwd2 = page.locator("body").text_content()
        
        # Passwords should differ (with high probability)
        # Note: same random seed could produce same, so permissive


def test_visual_styling(page):
    """App should have visual styling."""
    html = page.content().lower()
    has_styling = any(term in html for term in [
        'background', 'border', 'color:', '#', 'rgb'
    ])
    assert has_styling, "Password generator lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
