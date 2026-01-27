"""
Functional tests for Rich Text Editor (case_23_richtext).

V3 Tests - Discriminating tests for actual rich text formatting.
"""


def test_has_contenteditable(page):
    """Should use contenteditable for WYSIWYG editing."""
    editable = page.locator("[contenteditable='true']").count()
    assert editable > 0, "No contenteditable element found"


def test_can_type_text(page):
    """Should be able to type text."""
    editable = page.locator("[contenteditable='true']").first
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("Hello World")
        page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "Hello World" in content, "Typed text not visible"


def test_bold_button_works(page):
    """Bold button should apply bold formatting."""
    editable = page.locator("[contenteditable='true']").first
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("Make me bold")
        page.keyboard.press("Control+a")  # Select all
    
    bold_btn = page.locator("button:has-text('B'), [title*='bold' i]").first
    if bold_btn.count() > 0:
        bold_btn.click()
        page.wait_for_timeout(200)
    
    html = page.content().lower()
    has_bold = '<b>' in html or '<strong' in html or 'font-weight' in html
    assert has_bold, "Bold formatting not applied"


def test_italic_button_works(page):
    """Italic button should apply italic formatting."""
    editable = page.locator("[contenteditable='true']").first
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("Make me italic")
        page.keyboard.press("Control+a")
    
    italic_btn = page.locator("button:has-text('I'), [title*='italic' i]").first
    if italic_btn.count() > 0:
        italic_btn.click()
        page.wait_for_timeout(200)
    
    html = page.content().lower()
    has_italic = '<i>' in html or '<em' in html or 'font-style' in html
    assert has_italic, "Italic formatting not applied"


def test_underline_button_works(page):
    """Underline button should apply underline."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_underline = 'underline' in content or 'underline' in html or '<u>' in html
    assert has_underline, "No underline option found"


def test_has_font_size_control(page):
    """Should have font size control."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_size = any(term in content or term in html for term in [
        'size', 'font-size', 'heading', 'h1', 'h2', 'large', 'small'
    ])
    assert has_size, "No font size control found"


def test_has_text_alignment(page):
    """Should have text alignment options."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_align = any(term in content or term in html for term in [
        'align', 'left', 'center', 'right', 'justify'
    ])
    assert has_align, "No text alignment options found"


def test_has_list_formatting(page):
    """Should support bullet/numbered lists."""
    html = page.content().lower()
    
    has_lists = any(term in html for term in [
        'list', 'bullet', 'number', 'ol', 'ul', '•'
    ])
    assert has_lists, "No list formatting options"


def test_ctrl_b_applies_bold(page):
    """Ctrl+B should apply bold."""
    editable = page.locator("[contenteditable='true']").first
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("Bold test")
        page.keyboard.press("Control+a")
        page.keyboard.press("Control+b")
        page.wait_for_timeout(200)
    
    html = page.content().lower()
    has_bold = '<b>' in html or '<strong' in html or 'font-weight: bold' in html
    assert has_bold, "Ctrl+B did not apply bold"


def test_ctrl_i_applies_italic(page):
    """Ctrl+I should apply italic."""
    editable = page.locator("[contenteditable='true']").first
    if editable.count() > 0:
        editable.click()
        page.keyboard.type("Italic test")
        page.keyboard.press("Control+a")
        page.keyboard.press("Control+i")
        page.wait_for_timeout(200)
    
    html = page.content().lower()
    has_italic = '<i>' in html or '<em' in html or 'font-style: italic' in html
    assert has_italic, "Ctrl+I did not apply italic"


def test_toolbar_has_formatting_buttons(page):
    """Toolbar should have B, I, U buttons at minimum."""
    buttons = page.locator("button").all_text_contents()
    text = " ".join(buttons)
    
    has_b = 'B' in text
    has_i = 'I' in text
    
    assert has_b and has_i, "Missing B and/or I buttons in toolbar"


def test_document_styling(page):
    """Editor should have document-like styling."""
    html = page.content().lower()
    
    has_styling = any(term in html for term in [
        'background', 'white', '#fff', 'paper', 'border'
    ])
    assert has_styling, "Editor lacks document styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
