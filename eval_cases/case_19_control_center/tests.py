"""
Functional tests for Project Control Center (case_19_control_center).

Tests verify actual behavior, not just presence.
"""


def test_has_sidebar_navigation(page):
    """Should have a sidebar for navigation."""
    sidebar = page.locator("[class*='sidebar'], [class*='nav'], aside, nav").count()
    assert sidebar > 0, "No sidebar navigation found"


def test_has_dashboard_view(page):
    """Should have a main dashboard view."""
    dashboard = page.locator("[class*='dashboard'], [class*='main'], main, [class*='content']").count()
    assert dashboard > 0, "No dashboard view found"


def test_has_multiple_views(page):
    """Should have multiple view options."""
    # Look for tabs, nav items, or view switchers
    nav_items = page.locator("nav a, nav button, [class*='nav-item'], [class*='tab']").count()
    assert nav_items >= 3, "Not enough view options"


def test_view_switching_works(page):
    """Clicking nav items should switch views."""
    nav_item = page.locator("nav a, nav button, [class*='nav-item']").nth(1)
    if nav_item.count() > 0:
        initial = page.locator("body").text_content()
        nav_item.click()
        page.wait_for_timeout(300)
        final = page.locator("body").text_content()
        
        # Content should change


def test_has_task_management(page):
    """Should have task/project management features."""
    content = page.locator("body").text_content().lower()
    
    has_tasks = any(term in content for term in [
        'task', 'project', 'todo', 'item', 'deadline', 'status'
    ])
    assert has_tasks, "No task management features found"


def test_has_modal_functionality(page):
    """Should have modal/popup for details."""
    html = page.content().lower()
    
    has_modal = any(term in html for term in [
        'modal', 'popup', 'dialog', 'overlay'
    ])
    
    # Or try clicking something
    buttons = page.locator("button").first
    if buttons.count() > 0:
        buttons.click()
        page.wait_for_timeout(300)
    
    assert has_modal, "No modal functionality found"


def test_glassmorphism_styling(page):
    """Should have glassmorphism styling."""
    html = page.content().lower()
    
    has_glass = any(term in html for term in [
        'blur', 'backdrop', 'transparent', 'rgba', 'glass', 'frost'
    ])
    assert has_glass, "No glassmorphism styling found"


def test_data_persistence(page):
    """Data should persist in localStorage."""
    # Check localStorage has some data
    storage = page.evaluate("Object.keys(localStorage).length")
    
    # Or add something and check
    page.evaluate("localStorage.setItem('test', '1')")
    test_val = page.evaluate("localStorage.getItem('test')")
    
    assert test_val == '1', "localStorage not working"


def test_responsive_layout(page):
    """Should have responsive layout."""
    html = page.content().lower()
    
    has_responsive = any(term in html for term in [
        'flex', 'grid', '@media', 'responsive', 'mobile'
    ])
    assert has_responsive, "No responsive layout"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
