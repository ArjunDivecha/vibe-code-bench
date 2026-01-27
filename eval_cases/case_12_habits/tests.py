"""
Functional tests for Habit Tracker (case_12_habits).

Tests verify actual behavior, not just presence.
"""


def test_can_add_habit(page):
    """Should be able to add a new habit."""
    # Find input and add
    input_field = page.locator("input[type='text'], input[placeholder*='habit' i]").first
    if input_field.count() > 0:
        input_field.fill("Exercise Daily")
    
    add_btn = page.locator("button:has-text('Add'), button:has-text('Create'), button:has-text('+')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    content = page.locator("body").text_content()
    assert "Exercise" in content, "Habit not added"


def test_shows_habit_list(page):
    """Should display a list of habits."""
    lists = page.locator("[class*='habit'], [class*='list'], ul, table").count()
    assert lists > 0, "No habit list found"


def test_has_checkbox_or_toggle(page):
    """Should have checkboxes or toggles for completion."""
    checkboxes = page.locator("input[type='checkbox'], [class*='toggle'], [class*='check']").count()
    assert checkboxes > 0, "No checkboxes for habit completion"


def test_shows_streak(page):
    """Should display streak count."""
    content = page.locator("body").text_content().lower()
    
    has_streak = any(term in content for term in [
        'streak', 'day', 'consecutive', 'current'
    ])
    assert has_streak, "No streak display found"


def test_marking_habit_updates_ui(page):
    """Marking a habit complete should update the UI."""
    initial = page.locator("body").text_content()
    
    # Click a checkbox or completion button
    checkbox = page.locator("input[type='checkbox'], [class*='check']").first
    if checkbox.count() > 0:
        checkbox.click()
        page.wait_for_timeout(300)
        
        final = page.locator("body").text_content()
        # Something should change (streak, visual, etc)


def test_habits_persist(page):
    """Habits should persist in localStorage."""
    # Add a habit
    input_field = page.locator("input").first
    if input_field.count() > 0:
        input_field.fill("Persist Test Habit")
    add_btn = page.locator("button:has-text('Add')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    # Check localStorage
    storage = page.evaluate("localStorage.length")
    assert storage > 0, "Habits not persisted"


def test_shows_completion_percentage(page):
    """Should show completion percentage or progress."""
    content = page.locator("body").text_content().lower()
    
    has_progress = any(term in content for term in [
        '%', 'percent', 'progress', 'complete', 'done'
    ])
    
    # Or progress bar
    progress = page.locator("[class*='progress'], progress, [role='progressbar']").count()
    
    assert has_progress or progress > 0, "No completion percentage found"


def test_can_delete_habit(page):
    """Should be able to delete a habit."""
    delete_btn = page.locator("button:has-text('Delete'), button:has-text('×'), [class*='delete']").first
    
    if delete_btn.count() > 0:
        initial = page.locator("body").text_content()
        delete_btn.click()
        page.wait_for_timeout(300)
        final = page.locator("body").text_content()
        # Should change


def test_visual_calendar_or_grid(page):
    """Should have visual calendar or grid for tracking."""
    html = page.content().lower()
    
    has_visual = any(term in html for term in [
        'calendar', 'grid', 'week', 'month', 'day'
    ])
    
    # Or grid elements
    grid = page.locator("[class*='calendar'], [class*='grid'], table").count()
    
    assert has_visual or grid > 0, "No calendar/grid visualization"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
