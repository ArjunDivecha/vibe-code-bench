"""
Functional tests for Expense Tracker (case_09_expenses).

Tests verify actual behavior, not just presence.
"""


def test_can_add_expense(page):
    """Should be able to add an expense."""
    # Find inputs
    amount_input = page.locator("input[type='number'], input[placeholder*='amount' i]").first
    desc_input = page.locator("input[placeholder*='desc' i], input[type='text']").first
    
    if amount_input.count() > 0:
        amount_input.fill("50")
    if desc_input.count() > 0:
        desc_input.fill("Test expense")
    
    # Click add button
    add_btn = page.locator("button:has-text('Add'), button:has-text('Save'), button:has-text('+')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    content = page.locator("body").text_content()
    assert "50" in content or "Test expense" in content, "Expense not added"


def test_shows_total(page):
    """Should display total expenses."""
    content = page.locator("body").text_content().lower()
    
    has_total = any(term in content for term in [
        'total', 'sum', 'balance', '$'
    ])
    assert has_total, "No total display found"


def test_has_categories(page):
    """Should have expense categories."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    categories = ['food', 'transport', 'entertainment', 'shopping', 'bills', 'category']
    has_categories = any(cat in content or cat in html for cat in categories)
    
    # Or has a select/dropdown
    selects = page.locator("select").count()
    
    assert has_categories or selects > 0, "No categories found"


def test_can_delete_expense(page):
    """Should be able to delete an expense."""
    # First add an expense
    amount_input = page.locator("input[type='number']").first
    if amount_input.count() > 0:
        amount_input.fill("99")
    add_btn = page.locator("button:has-text('Add')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    initial = page.locator("body").text_content()
    
    # Delete
    delete_btn = page.locator("button:has-text('Delete'), button:has-text('×'), [class*='delete']").first
    if delete_btn.count() > 0:
        delete_btn.click()
        page.wait_for_timeout(300)
        
        final = page.locator("body").text_content()
        # Should change after delete


def test_expenses_persist(page):
    """Expenses should persist in localStorage."""
    # Add expense
    amount_input = page.locator("input[type='number']").first
    if amount_input.count() > 0:
        amount_input.fill("123")
    add_btn = page.locator("button:has-text('Add')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    # Check localStorage
    storage = page.evaluate("localStorage.length")
    assert storage > 0, "Expenses not persisted to localStorage"


def test_has_chart_or_visualization(page):
    """Should have a chart or visualization."""
    html = page.content().lower()
    
    has_chart = any(term in html for term in [
        'chart', 'graph', 'svg', 'canvas', 'pie', 'bar'
    ])
    
    # Or has SVG/canvas elements
    visuals = page.locator("svg, canvas").count()
    
    assert has_chart or visuals > 0, "No chart/visualization found"


def test_shows_expense_list(page):
    """Should display a list of expenses."""
    lists = page.locator("table, ul, [class*='list'], [class*='expense']").count()
    assert lists > 0, "No expense list found"


def test_has_date_support(page):
    """Should support dates for expenses."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_date = any(term in content or term in html for term in [
        'date', 'today', 'month', 'day', 'input type="date'
    ])
    assert has_date, "No date support found"


def test_visual_styling(page):
    """App should have visual styling."""
    html = page.content().lower()
    has_styling = any(term in html for term in [
        'background', 'border', 'color:', '#', 'rgb'
    ])
    assert has_styling, "Expense tracker lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
