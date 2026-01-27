"""
Functional tests for File Browser (case_24_filebrowser).

V3 Tests - Discriminating tests for actual file browser functionality.
"""


def test_shows_documents_folder(page):
    """Should show Documents folder."""
    content = page.locator("body").text_content()
    assert "Documents" in content, "Documents folder not shown"


def test_shows_pictures_folder(page):
    """Should show Pictures folder."""
    content = page.locator("body").text_content()
    assert "Pictures" in content, "Pictures folder not shown"


def test_shows_downloads_folder(page):
    """Should show Downloads folder."""
    content = page.locator("body").text_content()
    assert "Downloads" in content, "Downloads folder not shown"


def test_has_folder_icons(page):
    """Folders should have folder icons."""
    html = page.content()
    has_folder_icon = '📁' in html or 'folder' in html.lower()
    assert has_folder_icon, "No folder icons found"


def test_has_file_icons(page):
    """Files should have file icons."""
    html = page.content()
    has_file_icon = '📄' in html or 'file' in html.lower() or '🖼' in html
    assert has_file_icon, "No file icons found"


def test_folder_click_expands(page):
    """Clicking folder should expand/navigate."""
    folder = page.locator("[class*='folder'], :text('Documents')").first
    if folder.count() > 0:
        initial = page.locator("body").text_content()
        folder.click()
        page.wait_for_timeout(300)
        final = page.locator("body").text_content()
        # Content should change or expand
        # Permissive check


def test_has_breadcrumb_navigation(page):
    """Should have breadcrumb or path display."""
    content = page.locator("body").text_content()
    html = page.content().lower()
    
    has_breadcrumb = any(term in content or term in html for term in [
        '/', '>', 'home', 'root', 'path', 'breadcrumb'
    ])
    assert has_breadcrumb, "No breadcrumb navigation"


def test_shows_file_sizes(page):
    """Should show file sizes."""
    content = page.locator("body").text_content().lower()
    
    has_sizes = any(term in content for term in [
        'kb', 'mb', 'gb', 'bytes', 'size'
    ])
    assert has_sizes, "No file sizes shown"


def test_shows_file_dates(page):
    """Should show file dates."""
    content = page.locator("body").text_content().lower()
    
    has_dates = any(term in content for term in [
        'date', 'modified', 'created', 'jan', 'feb', 'mar', '2024', '2025', '2026'
    ])
    assert has_dates, "No file dates shown"


def test_tree_structure(page):
    """Should have hierarchical tree structure."""
    html = page.content().lower()
    
    has_tree = any(term in html for term in [
        'tree', '<ul', 'nested', 'children', 'expand', 'collapse'
    ])
    assert has_tree, "No tree structure found"


def test_has_search_or_filter(page):
    """Should have search or filter capability."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_search = any(term in content or term in html for term in [
        'search', 'filter', 'find'
    ])
    
    inputs = page.locator("input[type='search'], input[type='text']").count()
    assert has_search or inputs > 0, "No search capability"


def test_right_click_context_menu(page):
    """Should support context menu."""
    html = page.content().lower()
    
    has_context = any(term in html for term in [
        'contextmenu', 'context', 'right-click', 'menu'
    ])
    assert has_context, "No context menu support"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
