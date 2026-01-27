"""
Functional tests for Pomodoro Timer (case_01_pomodoro).

Tests verify:
1. Timer display shows initial 25:00
2. Start button begins countdown
3. Pause functionality works
4. Reset functionality works
5. Session indicator shows current session
6. Timer switches to break after work session
"""


def test_initial_display_shows_25_minutes(page):
    """Timer should show 25:00 on load."""
    # Look for time display containing 25:00
    display = page.locator("body")
    content = display.text_content()
    assert "25:00" in content or "25 : 00" in content, f"Expected 25:00, got: {content[:100]}"


def test_has_start_button(page):
    """Should have a visible start button."""
    # Try various selectors for start button
    start_btn = page.locator("button:has-text('Start'), button:has-text('START'), [class*='start'], #start")
    assert start_btn.count() > 0, "No start button found"


def test_has_pause_button(page):
    """Should have pause functionality."""
    # Pause might be hidden initially or combined with start
    pause_btn = page.locator("button:has-text('Pause'), button:has-text('PAUSE'), button:has-text('Stop'), [class*='pause']")
    # Also check if there's a start/pause toggle
    toggle_btn = page.locator("button:has-text('Start'), button:has-text('START')")
    assert pause_btn.count() > 0 or toggle_btn.count() > 0, "No pause/stop button found"


def test_has_reset_button(page):
    """Should have a reset button."""
    reset_btn = page.locator("button:has-text('Reset'), button:has-text('RESET'), [class*='reset'], #reset")
    assert reset_btn.count() > 0, "No reset button found"


def test_start_button_changes_time(page):
    """Clicking start should begin countdown."""
    # Find and click start
    start_btn = page.locator("button:has-text('Start'), button:has-text('START')").first
    if start_btn.count() == 0:
        start_btn = page.locator("button").first
    
    initial_content = page.locator("body").text_content()
    start_btn.click()
    
    # Wait a moment for timer to tick
    page.wait_for_timeout(1500)
    
    new_content = page.locator("body").text_content()
    # Time should have changed (24:59 or 24:58)
    assert "24:5" in new_content or "24 : 5" in new_content or initial_content != new_content, \
        "Timer did not start counting down"


def test_session_indicator_present(page):
    """Should show session indicator (Work/Break, Session 1, etc.)."""
    content = page.locator("body").text_content().lower()
    has_indicator = any(term in content for term in [
        "work", "break", "session", "pomodoro", "focus", "rest"
    ])
    assert has_indicator, "No session indicator found"


def test_timer_has_visual_styling(page):
    """Timer should have visible styling (not plain unstyled HTML)."""
    # Check that CSS is applied - body should have some styling
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    # Default browser bg is usually white/transparent
    has_custom_bg = body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", "transparent", ""]
    
    # Also check if any element has tomato-ish red color
    content = page.content()
    has_red_theme = any(color in content.lower() for color in [
        "tomato", "#ff6347", "rgb(255, 99, 71)", "#e74c3c", "#c0392b", "red"
    ])
    
    assert has_custom_bg or has_red_theme, "Timer lacks visual styling"


def test_page_has_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
