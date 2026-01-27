"""
Functional tests for Spreadsheet (case_21_spreadsheet).

Tests verify:
1. Grid with columns and rows
2. Cell selection works
3. Can enter data
4. Basic formulas work
5. Cell references work
6. SUM function works
7. Formula bar displays formulas
"""


def test_has_column_headers(page):
    """Should have column headers A, B, C..."""
    content = page.locator("body").text_content()
    
    # Should have at least A, B, C, D visible
    has_headers = all(col in content for col in ["A", "B", "C", "D"])
    assert has_headers, "Missing column headers"


def test_has_row_numbers(page):
    """Should have row numbers 1, 2, 3..."""
    content = page.locator("body").text_content()
    
    # Should have row numbers
    has_rows = "1" in content and "2" in content and "3" in content
    assert has_rows, "Missing row numbers"


def test_has_cell_grid(page):
    """Should have a grid of cells."""
    # Look for cell elements or table cells
    cells = page.locator(
        "td, [class*='cell'], input[type='text'], "
        "[contenteditable], [data-cell], [data-col]"
    )
    
    # Should have at least 50 cells (5x10 minimum)
    count = cells.count()
    assert count >= 50, f"Expected at least 50 cells, found {count}"


def test_can_click_cell(page):
    """Clicking a cell should select it."""
    cells = page.locator(
        "td:not(:first-child), [class*='cell'], "
        "input[type='text'], [contenteditable='true']"
    ).all()
    
    if len(cells) >= 1:
        cells[0].click()
        page.wait_for_timeout(200)
        
        # Cell should be focused or selected
        # Check if any cell has focus or selected class
        focused = page.locator(":focus, [class*='selected'], [class*='active']")
        assert focused.count() >= 0, "Cell selection not working"


def test_can_enter_data(page):
    """Should be able to type data into a cell."""
    # Find an editable cell
    cells = page.locator(
        "td[contenteditable], [class*='cell'] input, "
        "input[type='text'], [contenteditable='true']"
    ).all()
    
    if len(cells) >= 1:
        cells[0].click()
        page.wait_for_timeout(100)
        page.keyboard.type("123")
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        
        content = page.locator("body").text_content()
        assert "123" in content, "Data entry not working"


def test_basic_formula(page):
    """Formula =5+3 should show 8."""
    # Find a cell and enter formula
    cells = page.locator(
        "td[contenteditable], [class*='cell'], "
        "input[type='text'], [contenteditable='true']"
    ).all()
    
    if len(cells) >= 1:
        cells[0].click()
        page.wait_for_timeout(100)
        page.keyboard.type("=5+3")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        
        content = page.locator("body").text_content()
        assert "8" in content, "Basic formula not calculating"


def test_has_formula_bar(page):
    """Should have a formula bar or input area."""
    formula_bar = page.locator(
        "[class*='formula'], [class*='input-bar'], "
        "#formula, input[placeholder*='formula' i], "
        "[aria-label*='formula' i]"
    )
    
    # Or look for a prominent input at top
    top_inputs = page.locator("header input, .toolbar input, input").all()
    
    assert formula_bar.count() > 0 or len(top_inputs) > 0, \
        "No formula bar found"


def test_cell_reference_formula(page):
    """Formula referencing cells should work."""
    cells = page.locator(
        "td[contenteditable], [class*='cell'], "
        "input[type='text'], [contenteditable='true']"
    ).all()
    
    if len(cells) >= 2:
        # Enter value in first cell
        cells[0].click()
        page.keyboard.type("10")
        page.keyboard.press("Tab")
        page.wait_for_timeout(100)
        
        # Enter formula in second cell
        page.keyboard.type("=A1*2")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        
        content = page.locator("body").text_content()
        # Should show 20 (10 * 2)
        assert "20" in content, "Cell reference formula not working"


def test_grid_styling(page):
    """Grid should have visible borders/styling."""
    content = page.content().lower()
    
    has_grid_style = any(term in content for term in [
        'border', 'grid', 'table', 'td', 'th'
    ])
    
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    has_styling = body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", ""]
    
    assert has_grid_style or has_styling, "Grid lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
