"""
Functional tests for Pomodoro Timer (case_01_pomodoro).

V3 Tests - More flexible, behavior-focused.
"""


def test_shows_time_display(page):
    """Timer should show a time display (MM:SS or similar)."""
    content = page.locator("body").text_content()
    
    # Look for time patterns: 25:00, 25 : 00, 25min, etc
    has_time = any(pattern in content for pattern in [
        "25:00", "25 : 00", "25:0", "25 min", "1500"
    ])
    
    assert has_time, f"No 25-minute time display found in: {content[:200]}"


def test_has_start_button(page):
    """Should have a start button."""
    buttons = page.locator("button").all_text_contents()
    button_text = " ".join(buttons).lower()
    
    has_start = any(word in button_text for word in ['start', 'begin', 'play'])
    
    # Or check for clickable elements
    clickables = page.locator("button, [onclick], [class*='start']").count()
    
    assert has_start or clickables > 0, "No start button found"


def test_has_control_buttons(page):
    """Should have control buttons (start, pause, reset)."""
    buttons = page.locator("button").count()
    assert buttons >= 2, f"Expected at least 2 control buttons, found {buttons}"


def test_timer_can_start(page):
    """Clicking start should change the display."""
    initial = page.locator("body").text_content()
    
    # Find and click start button
    start_btn = page.locator("button:has-text('Start'), button:has-text('start'), button:has-text('Play')").first
    if start_btn.count() > 0:
        start_btn.click()
    else:
        # Click first button
        page.locator("button").first.click()
    
    page.wait_for_timeout(1500)  # Wait for timer to tick
    
    final = page.locator("body").text_content()
    # Something should change (time or state)
    assert initial != final or "24:5" in final or "running" in final.lower(), \
        "Timer did not start"


def test_has_session_indicator(page):
    """Should indicate work/break session."""
    content = page.locator("body").text_content().lower()
    
    has_indicator = any(term in content for term in [
        'work', 'break', 'session', 'pomodoro', 'focus', 'rest', 'round'
    ])
    
    assert has_indicator, "No session indicator found"


def test_has_visual_styling(page):
    """Timer should have visual styling (not plain HTML)."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'background', 'color:', 'font-', 'border', '#', 'rgb', 'tomato', 'red'
    ])
    
    assert has_styling, "Timer lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
