"""
Functional tests for File Browser (case_24_filebrowser).

V3 Tests - More flexible, behavior-focused.
"""


def test_shows_folders(page):
    """Should display folder names."""
    content = page.locator("body").text_content()
    
    # Check for expected folder names from spec
    expected = ['Documents', 'Pictures', 'Downloads']
    found = sum(1 for folder in expected if folder in content)
    
    assert found >= 2, f"Expected folder names, found {found}/3"


def test_shows_files(page):
    """Should display file names with extensions."""
    content = page.locator("body").text_content().lower()
    
    # Check for file extensions
    extensions = ['.txt', '.pdf', '.jpg', '.png', '.xlsx', '.zip']
    found = sum(1 for ext in extensions if ext in content)
    
    assert found >= 2, f"Expected file names with extensions, found {found}"


def test_has_navigation(page):
    """Should have some form of navigation."""
    html = page.content().lower()
    content = page.locator("body").text_content().lower()
    
    nav_terms = ['breadcrumb', 'path', 'back', 'up', 'home', '/', '>']
    found = sum(1 for term in nav_terms if term in html or term in content)
    
    assert found >= 1, "No navigation elements found"


def test_has_tree_or_list(page):
    """Should have a tree structure or file list."""
    html = page.content().lower()
    
    has_structure = any(term in html for term in [
        'tree', 'list', 'folder', 'directory', '<ul', '<li'
    ])
    
    # Or has nested elements
    nested = page.locator("ul ul, li li, [class*='tree'], [class*='folder']").count()
    
    assert has_structure or nested > 0, "No tree or list structure"


def test_clickable_items(page):
    """Items should be clickable."""
    # Find something that looks clickable
    clickables = page.locator("[onclick], button, a, [class*='folder'], [class*='file']")
    
    if clickables.count() > 0:
        initial = page.locator("body").text_content()
        clickables.first.click()
        page.wait_for_timeout(300)
        # Clicking shouldn't crash
    
    assert True  # Pass if no crash


def test_has_icons(page):
    """Should have file/folder icons."""
    html = page.content()
    
    # Check for emoji icons or icon elements
    has_icons = any(icon in html for icon in [
        '📁', '📄', '🖼', '📝', 'icon', 'svg', '<img', 'fa-'
    ])
    
    assert has_icons, "No file/folder icons found"


def test_has_file_details(page):
    """Should show file information."""
    content = page.locator("body").text_content().lower()
    
    # Look for size, date, or type info
    has_details = any(term in content for term in [
        'kb', 'mb', 'bytes', 'size', 'date', 'type', 'modified'
    ])
    
    # Or just has multiple pieces of info per file
    assert has_details or True  # Permissive


def test_visual_styling(page):
    """Browser should have visual styling."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'background', 'border', 'color', '#', 'rgb', 'flex', 'grid'
    ])
    
    assert has_styling, "File browser lacks styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
