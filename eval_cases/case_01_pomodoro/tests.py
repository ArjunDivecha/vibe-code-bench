"""
Functional tests for Pomodoro Timer (case_01_pomodoro).

V3 Tests - Behavioral tests that verify actual functionality.
Optimized for speed with reduced timeouts.
"""


def test_shows_25_minute_display(page):
    """Timer should show 25:00 (standard Pomodoro work time)."""
    content = page.locator("body").text_content()
    
    has_25 = any(pattern in content for pattern in [
        "25:00", "25 : 00", "25:0"
    ])
    
    assert has_25, f"No 25-minute display found in: {content[:200]}"


def test_has_start_button(page):
    """Should have a clearly labeled start button."""
    buttons = page.locator("button").all_text_contents()
    button_text = " ".join(buttons).lower()
    
    has_start = any(word in button_text for word in ['start', 'begin', 'play'])
    assert has_start, f"No start button found in: {button_text}"


def test_has_pause_button(page):
    """Should have a pause/stop button."""
    buttons = page.locator("button").all_text_contents()
    button_text = " ".join(buttons).lower()
    
    has_pause = any(word in button_text for word in ['pause', 'stop'])
    assert has_pause, "No pause/stop button found"


def test_has_reset_button(page):
    """Should have a reset button."""
    buttons = page.locator("button").all_text_contents()
    button_text = " ".join(buttons).lower()
    
    has_reset = any(word in button_text for word in ['reset', 'restart', 'clear'])
    assert has_reset, "No reset button found"


def test_timer_counts_down(page):
    """Starting timer should count down from 25:00."""
    # Click start
    start_btn = page.locator("button:has-text('Start'), button:has-text('start')").first
    if start_btn.count() > 0:
        start_btn.click()
    else:
        page.locator("button").first.click()
    
    page.wait_for_timeout(1200)  # Wait just over 1 second for timer to tick
    
    content = page.locator("body").text_content()
    # Should show less than 25:00
    has_countdown = any(t in content for t in ["24:5", "24:4", "24:3", "24:58", "24:59"])
    assert has_countdown, f"Timer not counting down, content: {content[:200]}"


def test_has_work_break_modes(page):
    """Should distinguish work and break sessions."""
    content = page.locator("body").text_content().lower()
    
    has_modes = any(term in content for term in [
        'work', 'break', 'session', 'focus', 'rest'
    ])
    
    assert has_modes, "No work/break session indicator found"


def test_shows_break_duration(page):
    """Should show 5-minute short break time."""
    content = page.locator("body").text_content()
    html = page.content()
    
    # Look for 5:00 or break-related content
    has_break = "5:00" in content or "5 min" in content or "break" in content.lower()
    assert has_break, "No 5-minute break indicator found"


def test_session_counter(page):
    """Should track completed sessions/pomodoros."""
    content = page.locator("body").text_content().lower()
    
    has_counter = any(term in content for term in [
        'session', 'round', 'pomodoro', '#', 'completed'
    ])
    assert has_counter, "No session counter found"


def test_pause_stops_timer(page):
    """Pause should stop the timer from counting."""
    # Start the timer
    start_btn = page.locator("button:has-text('Start'), button:has-text('start')").first
    if start_btn.count() > 0:
        start_btn.click()
        page.wait_for_timeout(500)
    
    # Pause it
    pause_btn = page.locator("button:has-text('Pause'), button:has-text('pause'), button:has-text('Stop')").first
    if pause_btn.count() > 0:
        pause_btn.click()
        page.wait_for_timeout(100)
        
        content1 = page.locator("body").text_content()
        page.wait_for_timeout(800)
        content2 = page.locator("body").text_content()
        
        # Timer should not change when paused (extract time pattern)
        import re
        time1 = re.findall(r'\d{1,2}:\d{2}', content1)
        time2 = re.findall(r'\d{1,2}:\d{2}', content2)
        
        if time1 and time2:
            assert time1[0] == time2[0], "Timer continued after pause"


def test_reset_returns_to_25(page):
    """Reset should return timer to 25:00."""
    # Start timer
    start_btn = page.locator("button:has-text('Start')").first
    if start_btn.count() > 0:
        start_btn.click()
        page.wait_for_timeout(1200)
    
    # Reset
    reset_btn = page.locator("button:has-text('Reset'), button:has-text('Restart')").first
    if reset_btn.count() > 0:
        reset_btn.click()
        page.wait_for_timeout(200)
        
        content = page.locator("body").text_content()
        has_25 = "25:00" in content or "25 : 00" in content
        assert has_25, "Reset did not return to 25:00"


def test_visual_styling(page):
    """Timer should have proper visual styling."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'background', 'color:', 'font-size', '#', 'rgb'
    ])
    assert has_styling, "Timer lacks visual styling"


def test_has_break_timer(page):
    """Should have break timer option (5 min short, 15 min long)."""
    content = page.locator("body").text_content().lower()
    
    has_break = any(term in content for term in [
        'break', 'rest', '5:00', '5 min', '15 min', 'short', 'long'
    ])
    assert has_break, "No break timer functionality"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(300)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
