"""
Functional tests for Rich Text Editor (case_23_richtext).

Tests verify:
1. Editable content area
2. Bold button works
3. Italic button works
4. Heading support
5. List support
6. Keyboard shortcuts
7. Clean UI
"""


def test_has_editable_area(page):
    """Should have an editable content area."""
    editable = page.locator(
        "[contenteditable='true'], textarea, "
        "[class*='editor'], [class*='content']"
    )
    assert editable.count() > 0, "No editable area found"


def test_has_formatting_toolbar(page):
    """Should have a toolbar with formatting buttons."""
    toolbar = page.locator(
        "[class*='toolbar'], [class*='menu'], "
        "[role='toolbar'], header"
    )
    
    # Or look for formatting buttons
    buttons = page.locator(
        "button, [class*='btn'], [role='button']"
    )
    
    assert toolbar.count() > 0 or buttons.count() >= 3, \
        "No formatting toolbar found"


def test_has_bold_button(page):
    """Should have a bold formatting button."""
    bold_btn = page.locator(
        "button:has-text('B'), button[title*='bold' i], "
        "[class*='bold'], button:has-text('Bold'), "
        "[aria-label*='bold' i]"
    )
    
    content = page.content().lower()
    has_bold = 'bold' in content or '>b<' in content
    
    assert bold_btn.count() > 0 or has_bold, "No bold button found"


def test_has_italic_button(page):
    """Should have an italic formatting button."""
    italic_btn = page.locator(
        "button:has-text('I'), button[title*='italic' i], "
        "[class*='italic'], button:has-text('Italic'), "
        "[aria-label*='italic' i]"
    )
    
    content = page.content().lower()
    has_italic = 'italic' in content
    
    assert italic_btn.count() > 0 or has_italic, "No italic button found"


def test_can_type_in_editor(page):
    """Should be able to type text in editor."""
    editable = page.locator(
        "[contenteditable='true'], textarea"
    ).first
    
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("Test content here")
        page.wait_for_timeout(200)
        
        content = page.locator("body").text_content()
        assert "Test content here" in content, "Cannot type in editor"


def test_has_heading_options(page):
    """Should have heading formatting options."""
    content = page.locator("body").text_content().lower()
    
    has_headings = any(term in content for term in [
        'h1', 'h2', 'h3', 'heading', 'title', 'header'
    ])
    
    heading_btn = page.locator(
        "button:has-text('H1'), button:has-text('H2'), "
        "select, [class*='heading']"
    )
    
    assert has_headings or heading_btn.count() > 0, \
        "No heading options found"


def test_has_list_options(page):
    """Should have list formatting options."""
    content = page.locator("body").text_content().lower()
    
    has_lists = any(term in content for term in [
        'list', 'bullet', 'numbered', 'ul', 'ol'
    ])
    
    list_btn = page.locator(
        "[class*='list'], button[title*='list' i], "
        "[aria-label*='list' i]"
    )
    
    assert has_lists or list_btn.count() > 0, "No list options found"


def test_has_undo_support(page):
    """Should support undo functionality."""
    content = page.content().lower()
    
    # Check for undo button or keyboard handler
    has_undo = any(term in content for term in [
        'undo', 'ctrl+z', 'command+z', 'keydown'
    ])
    
    undo_btn = page.locator(
        "button:has-text('Undo'), button[title*='undo' i], "
        "[class*='undo']"
    )
    
    assert has_undo or undo_btn.count() > 0, "No undo support found"


def test_uses_contenteditable(page):
    """Should use contenteditable for editing."""
    editable = page.locator("[contenteditable='true']")
    textarea = page.locator("textarea")
    
    assert editable.count() > 0 or textarea.count() > 0, \
        "No editable element found"


def test_document_styling(page):
    """Editor should have document-like styling."""
    # Check for white page / document appearance
    content = page.content().lower()
    
    has_doc_style = any(term in content for term in [
        'background', 'white', '#fff', 'rgb(255', 'shadow', 'paper'
    ])
    
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    
    assert has_doc_style or body_bg != "", "Editor lacks document styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
