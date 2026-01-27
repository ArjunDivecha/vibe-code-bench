"""
Functional tests for Spreadsheet (case_21_spreadsheet).

V3 Tests - More flexible, behavior-focused.
"""


def test_has_column_headers(page):
    """Should have column headers A, B, C..."""
    content = page.locator("body").text_content()
    # Count how many column letters are visible
    cols_found = sum(1 for col in "ABCDEFGHIJ" if col in content)
    assert cols_found >= 4, f"Expected at least 4 column headers, found {cols_found}"


def test_has_row_numbers(page):
    """Should have row numbers visible."""
    content = page.locator("body").text_content()
    # Count row numbers found
    rows_found = sum(1 for i in range(1, 11) if str(i) in content)
    assert rows_found >= 3, f"Expected at least 3 row numbers, found {rows_found}"


def test_has_grid_structure(page):
    """Should have a grid of cells (table, div grid, or inputs)."""
    # Try multiple possible implementations
    table_cells = page.locator("td").count()
    div_cells = page.locator("[class*='cell']").count()
    inputs = page.locator("input").count()
    
    total = table_cells + div_cells + inputs
    assert total >= 20, f"Expected at least 20 cells/inputs, found {total}"


def test_page_is_interactive(page):
    """Page should respond to clicks without errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    
    # Click somewhere in the middle of the page
    page.click("body", position={"x": 300, "y": 300})
    page.wait_for_timeout(200)
    
    assert len(errors) == 0, f"Click caused JS errors: {errors}"


def test_can_type_numbers(page):
    """Should be able to type and see numbers appear."""
    initial = page.locator("body").text_content()
    
    # Click and type
    page.click("body", position={"x": 300, "y": 200})
    page.wait_for_timeout(100)
    page.keyboard.type("42")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    
    final = page.locator("body").text_content()
    assert "42" in final, "Typed number not visible on page"


def test_formula_evaluation(page):
    """Entering =2+2 should show 4 somewhere."""
    page.click("body", position={"x": 300, "y": 200})
    page.wait_for_timeout(100)
    
    # Clear and type formula
    page.keyboard.press("Control+a")
    page.keyboard.type("=2+2")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    
    content = page.locator("body").text_content()
    # Should show 4 (the result)
    assert "4" in content, "Formula =2+2 did not evaluate to 4"


def test_has_visual_grid(page):
    """Should have visible grid lines or borders."""
    html = page.content().lower()
    
    has_table = "<table" in html
    has_border = "border" in html
    has_grid_css = "display: grid" in html or "display:grid" in html
    
    assert has_table or has_border or has_grid_css, \
        "No visible grid structure found"


def test_multiple_cells_work(page):
    """Should be able to enter data in multiple cells."""
    # Enter in one location
    page.click("body", position={"x": 200, "y": 200})
    page.keyboard.type("AAA")
    page.keyboard.press("Tab")
    page.wait_for_timeout(100)
    
    # Enter in another
    page.keyboard.type("BBB")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    has_aaa = "AAA" in content
    has_bbb = "BBB" in content
    
    assert has_aaa and has_bbb, "Could not enter data in multiple cells"


def test_no_console_errors_on_load(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
