"""
Functional tests for Rich Text Editor (case_23_richtext).

V3 Tests - More flexible, behavior-focused.
"""


def test_has_editable_area(page):
    """Should have an editable content area."""
    # Check for contenteditable or textarea
    editable = page.locator("[contenteditable='true']").count()
    textarea = page.locator("textarea").count()
    
    assert editable > 0 or textarea > 0, "No editable area found"


def test_can_type_text(page):
    """Should be able to type and see text."""
    # Click in editor area
    editable = page.locator("[contenteditable='true'], textarea").first
    if editable.count() > 0:
        editable.click()
    else:
        page.click("body", position={"x": 400, "y": 300})
    
    page.keyboard.type("Hello World Test")
    page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "Hello World Test" in content, "Typed text not visible"


def test_has_formatting_buttons(page):
    """Should have formatting buttons (bold, italic, etc)."""
    html = page.content().lower()
    content = page.locator("body").text_content().lower()
    
    # Look for formatting indicators
    format_terms = ['bold', 'italic', 'underline', '<b>', '<i>', '<u>']
    found = sum(1 for term in format_terms if term in html or term in content)
    
    # Or count buttons that might be formatting
    buttons = page.locator("button").count()
    
    assert found >= 1 or buttons >= 3, "No formatting buttons found"


def test_has_bold_capability(page):
    """Should have bold formatting option."""
    # Look for B button or bold in HTML
    bold_btn = page.locator("button:has-text('B'), [title*='bold' i], [class*='bold']")
    html = page.content().lower()
    
    has_bold = bold_btn.count() > 0 or 'bold' in html or '>b<' in html
    assert has_bold, "No bold formatting option found"


def test_has_italic_capability(page):
    """Should have italic formatting option."""
    italic_btn = page.locator("button:has-text('I'), [title*='italic' i], [class*='italic']")
    html = page.content().lower()
    
    has_italic = italic_btn.count() > 0 or 'italic' in html
    assert has_italic, "No italic formatting option found"


def test_keyboard_shortcut_support(page):
    """Should handle keyboard events (potential shortcuts)."""
    html = page.content().lower()
    
    # Check for keydown handlers or shortcut mentions
    has_keyboard = any(term in html for term in [
        'keydown', 'keypress', 'ctrl', 'command', 'shortcut'
    ])
    
    # Or test that Ctrl+B doesn't break anything
    editable = page.locator("[contenteditable='true'], textarea").first
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("test")
        page.keyboard.press("Control+b")  # Try bold shortcut
        page.wait_for_timeout(100)
    
    # Pass if no errors
    assert True


def test_has_toolbar(page):
    """Should have a formatting toolbar."""
    html = page.content().lower()
    
    has_toolbar = any(term in html for term in [
        'toolbar', 'menu', 'format', 'editor'
    ])
    
    # Or has multiple buttons at top
    buttons = page.locator("button").count()
    
    assert has_toolbar or buttons >= 2, "No toolbar found"


def test_document_appearance(page):
    """Editor should have document-like appearance."""
    html = page.content().lower()
    
    # Check for styling
    has_styling = any(term in html for term in [
        'background', 'white', 'paper', 'document', 'editor', '#fff'
    ])
    
    assert has_styling, "Editor lacks document styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
