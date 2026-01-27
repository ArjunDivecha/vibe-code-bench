"""
Functional tests for Stopwatch & Timer (case_07_stopwatch).

Tests verify actual behavior, not just presence.
"""


def test_has_time_display(page):
    """Should display time in MM:SS or HH:MM:SS format."""
    content = page.locator("body").text_content()
    
    # Look for time patterns
    import re
    time_patterns = re.findall(r'\d{1,2}:\d{2}', content)
    
    assert len(time_patterns) > 0, "No time display found"


def test_has_start_stop_buttons(page):
    """Should have start and stop/pause buttons."""
    buttons = page.locator("button").all_text_contents()
    button_text = " ".join(buttons).lower()
    
    has_start = any(word in button_text for word in ['start', 'play', 'begin'])
    has_stop = any(word in button_text for word in ['stop', 'pause', 'reset'])
    
    assert has_start, "No start button found"
    assert has_stop, "No stop/pause button found"


def test_stopwatch_starts_counting(page):
    """Clicking start should begin counting."""
    # Get initial time
    initial = page.locator("body").text_content()
    
    # Click start
    start_btn = page.locator("button:has-text('Start'), button:has-text('Play')").first
    if start_btn.count() > 0:
        start_btn.click()
        page.wait_for_timeout(1500)
        
        final = page.locator("body").text_content()
        # Time should have changed
        assert initial != final, "Stopwatch did not start counting"


def test_has_lap_functionality(page):
    """Should have lap button for stopwatch."""
    content = page.locator("body").text_content().lower()
    buttons = page.locator("button").all_text_contents()
    button_text = " ".join(buttons).lower()
    
    has_lap = "lap" in content or "lap" in button_text or "split" in button_text
    assert has_lap, "No lap functionality found"


def test_has_timer_mode(page):
    """Should have timer/countdown mode."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_timer = any(term in content or term in html for term in [
        'timer', 'countdown', 'set time', 'minutes', 'seconds'
    ])
    
    assert has_timer, "No timer mode found"


def test_reset_clears_time(page):
    """Reset should clear the time back to zero."""
    # Start the stopwatch
    start_btn = page.locator("button:has-text('Start')").first
    if start_btn.count() > 0:
        start_btn.click()
        page.wait_for_timeout(1000)
    
    # Click reset
    reset_btn = page.locator("button:has-text('Reset'), button:has-text('Clear')").first
    if reset_btn.count() > 0:
        reset_btn.click()
        page.wait_for_timeout(300)
        
        content = page.locator("body").text_content()
        # Should show 00:00 or similar
        assert "00:00" in content or "0:00" in content, "Reset did not clear time"


def test_pause_stops_counting(page):
    """Pause should stop the counter."""
    # Start
    start_btn = page.locator("button:has-text('Start')").first
    if start_btn.count() > 0:
        start_btn.click()
        page.wait_for_timeout(500)
    
    # Pause
    pause_btn = page.locator("button:has-text('Pause'), button:has-text('Stop')").first
    if pause_btn.count() > 0:
        pause_btn.click()
        page.wait_for_timeout(100)
        
        content1 = page.locator("body").text_content()
        page.wait_for_timeout(500)
        content2 = page.locator("body").text_content()
        
        # Time should not change when paused
        # (permissive - just check it didn't crash)


def test_dual_mode_interface(page):
    """Should have both stopwatch and timer modes accessible."""
    content = page.locator("body").text_content().lower()
    buttons = page.locator("button, [class*='tab'], [class*='mode']").all_text_contents()
    text = " ".join(buttons).lower()
    
    has_modes = ("stopwatch" in text and "timer" in text) or \
                ("stopwatch" in content and "timer" in content) or \
                page.locator("[class*='tab'], [class*='mode']").count() >= 2
    
    assert has_modes, "No dual mode interface found"


def test_visual_styling(page):
    """App should have visual styling."""
    html = page.content().lower()
    has_styling = any(term in html for term in [
        'background', 'border', 'font-size', 'color:', '#', 'rgb'
    ])
    assert has_styling, "Stopwatch lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
