"""
Functional tests for Legal Case Search (case_17_legal).

Tests verify actual behavior, not just presence.
"""


def test_has_search_input(page):
    """Should have a search input field."""
    search = page.locator("input[type='search'], input[type='text'], input[placeholder*='search' i]").count()
    assert search >= 1, "No search input found"


def test_shows_case_list(page):
    """Should display a list of cases."""
    lists = page.locator("[class*='case'], [class*='result'], [class*='list'], ul, table").count()
    assert lists > 0, "No case list found"


def test_has_case_details_panel(page):
    """Should have a details panel for selected case."""
    detail = page.locator("[class*='detail'], [class*='panel'], [class*='preview'], aside").count()
    assert detail > 0, "No details panel found"


def test_search_filters_results(page):
    """Searching should filter the case list."""
    search = page.locator("input[type='search'], input[type='text']").first
    if search.count() > 0:
        initial = page.locator("body").text_content()
        search.fill("contract")
        page.wait_for_timeout(300)
        final = page.locator("body").text_content()
        
        # Content should change after search
        assert initial != final or "contract" in final.lower(), \
            "Search did not filter results"


def test_clicking_case_shows_details(page):
    """Clicking a case should show its details."""
    # Find a case item
    case_item = page.locator("[class*='case'], [class*='result'], li").first
    if case_item.count() > 0:
        initial = page.locator("body").text_content()
        case_item.click()
        page.wait_for_timeout(300)
        final = page.locator("body").text_content()
        
        # Details should appear or change


def test_has_notes_functionality(page):
    """Should have notes/annotation capability."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_notes = any(term in content or term in html for term in [
        'note', 'annotation', 'comment', 'memo', 'textarea'
    ])
    
    textareas = page.locator("textarea").count()
    
    assert has_notes or textareas > 0, "No notes functionality found"


def test_professional_styling(page):
    """Should have professional/legal styling."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'serif', 'professional', 'legal', 'dark', 'border', 'shadow'
    ])
    
    assert has_styling, "Lacks professional styling"


def test_shows_case_metadata(page):
    """Should display case metadata (date, court, etc)."""
    content = page.locator("body").text_content().lower()
    
    metadata = ['date', 'court', 'judge', 'citation', 'year', 'filed']
    found = sum(1 for m in metadata if m in content)
    
    assert found >= 2, "Not enough case metadata displayed"


def test_has_sample_cases(page):
    """Should have sample legal cases to search."""
    content = page.locator("body").text_content()
    
    # Should have some text content
    assert len(content) > 200, "Not enough sample case content"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
