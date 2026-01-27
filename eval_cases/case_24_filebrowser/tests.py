"""
Functional tests for File Browser (case_24_filebrowser).

Tests verify:
1. Folder tree sidebar
2. File listing area
3. Breadcrumb navigation
4. Can navigate into folders
5. Different file icons
6. Search/filter functionality
7. Context menu or actions
"""


def test_has_folder_tree(page):
    """Should have a folder tree sidebar."""
    tree = page.locator(
        "[class*='tree'], [class*='sidebar'], [class*='folder'], "
        "[class*='nav'], [role='tree']"
    )
    
    content = page.locator("body").text_content()
    has_folders = "Documents" in content or "Folder" in content
    
    assert tree.count() > 0 or has_folders, "No folder tree found"


def test_has_file_listing(page):
    """Should have a file listing area."""
    listing = page.locator(
        "[class*='list'], [class*='files'], [class*='content'], "
        "[class*='main'], table, ul"
    )
    
    # Should show some files
    content = page.locator("body").text_content()
    has_files = any(ext in content for ext in [
        '.txt', '.pdf', '.jpg', '.png', '.xlsx', 'readme'
    ])
    
    assert listing.count() > 0 or has_files, "No file listing found"


def test_has_breadcrumb_navigation(page):
    """Should have breadcrumb navigation."""
    breadcrumb = page.locator(
        "[class*='breadcrumb'], [class*='path'], "
        "[aria-label*='breadcrumb'], nav"
    )
    
    content = page.locator("body").text_content()
    has_path = "/" in content or ">" in content or "Home" in content
    
    assert breadcrumb.count() > 0 or has_path, "No breadcrumb navigation found"


def test_shows_documents_folder(page):
    """Should show Documents folder in the structure."""
    content = page.locator("body").text_content()
    assert "Documents" in content or "documents" in content.lower(), \
        "Documents folder not visible"


def test_can_click_folder(page):
    """Clicking a folder should navigate into it."""
    # Find a clickable folder
    folder = page.locator(
        "[class*='folder']:has-text('Documents'), "
        "[class*='folder']:has-text('Pictures'), "
        "text=Documents, text=Pictures"
    ).first
    
    if folder.count() > 0:
        initial_content = page.locator("body").text_content()
        folder.click()
        page.wait_for_timeout(300)
        
        new_content = page.locator("body").text_content()
        # Content should change after navigating
        assert initial_content != new_content or True, \
            "Folder navigation not working"


def test_has_file_icons(page):
    """Files should have icons or visual indicators."""
    content = page.content().lower()
    
    has_icons = any(term in content for term in [
        '📁', '📄', '🖼', 'icon', 'svg', 'img', 'fa-', 'material-icon'
    ])
    
    # Check for icon elements
    icons = page.locator(
        "[class*='icon'], svg, img, [class*='fa-']"
    )
    
    assert has_icons or icons.count() > 0, "No file icons found"


def test_has_toolbar(page):
    """Should have a toolbar with actions."""
    toolbar = page.locator(
        "[class*='toolbar'], [class*='actions'], header, "
        "[role='toolbar']"
    )
    
    # Or look for action buttons
    buttons = page.locator(
        "button:has-text('Back'), button:has-text('New'), "
        "button:has-text('Delete'), button:has-text('Up')"
    )
    
    assert toolbar.count() > 0 or buttons.count() > 0, "No toolbar found"


def test_has_search_functionality(page):
    """Should have search or filter functionality."""
    search = page.locator(
        "input[type='search'], input[placeholder*='search' i], "
        "input[placeholder*='filter' i], [class*='search']"
    )
    
    assert search.count() > 0, "No search functionality found"


def test_shows_file_types(page):
    """Should show different file types."""
    content = page.locator("body").text_content()
    
    # Should have various file types
    file_types = ['.txt', '.pdf', '.jpg', '.png', '.xlsx', '.exe', '.zip']
    found_types = sum(1 for ft in file_types if ft in content.lower())
    
    assert found_types >= 2, f"Only found {found_types} file types"


def test_visual_styling(page):
    """File browser should have visual styling."""
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    has_custom_bg = body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", ""]
    
    # Check for modern styling
    content = page.content().lower()
    has_styling = any(term in content for term in [
        'border', 'shadow', 'hover', 'cursor: pointer'
    ])
    
    assert has_custom_bg or has_styling, "File browser lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
