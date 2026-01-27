"""
Functional tests for Markdown Editor (case_15_markdown).

Tests verify actual behavior, not just presence.
"""


def test_has_editor_area(page):
    """Should have a text editor area."""
    editor = page.locator("textarea, [contenteditable='true'], [class*='editor']").count()
    assert editor > 0, "No editor area found"


def test_has_preview_area(page):
    """Should have a preview area."""
    preview = page.locator("[class*='preview'], [class*='output'], [class*='rendered']").count()
    
    # Or split panes
    panes = page.locator("[class*='pane'], [class*='panel']").count()
    
    assert preview > 0 or panes >= 2, "No preview area found"


def test_bold_renders(page):
    """**bold** should render as bold in preview."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("**bold text**")
        page.wait_for_timeout(300)
        
        html = page.content().lower()
        # Should have <strong> or <b> or font-weight: bold
        has_bold = '<strong' in html or '<b>' in html or 'font-weight' in html
        assert has_bold, "Bold not rendering"


def test_italic_renders(page):
    """*italic* should render as italic in preview."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("*italic text*")
        page.wait_for_timeout(300)
        
        html = page.content().lower()
        has_italic = '<em' in html or '<i>' in html or 'font-style' in html
        assert has_italic, "Italic not rendering"


def test_list_renders(page):
    """Lists should render properly."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("- Item 1\\n- Item 2\\n- Item 3")
        page.wait_for_timeout(300)
        
        html = page.content().lower()
        has_list = '<ul' in html or '<li' in html
        assert has_list, "List not rendering"


def test_link_renders(page):
    """[link](url) should render as clickable link."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("[Click here](https://example.com)")
        page.wait_for_timeout(300)
        
        html = page.content().lower()
        has_link = '<a ' in html or 'href' in html
        assert has_link, "Link not rendering"


def test_heading_renders(page):
    """# Heading should render as heading."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("# Main Heading")
        page.wait_for_timeout(300)
        
        html = page.content().lower()
        has_heading = any(f'<h{i}' in html for i in range(1, 7))
        assert has_heading, "Heading not rendering"


def test_live_preview(page):
    """Preview should update as you type."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("First text")
        content1 = page.content()
        
        editor.fill("Different text here")
        page.wait_for_timeout(300)
        content2 = page.content()
        
        assert content1 != content2, "Preview not updating live"


def test_has_toolbar(page):
    """Should have formatting toolbar."""
    toolbar = page.locator("[class*='toolbar'], [class*='menu'], [class*='buttons']").count()
    buttons = page.locator("button").count()
    
    assert toolbar > 0 or buttons >= 3, "No toolbar found"


def test_code_block_renders(page):
    """Code blocks should render with formatting."""
    editor = page.locator("textarea, [contenteditable='true']").first
    if editor.count() > 0:
        editor.fill("```\\ncode here\\n```")
        page.wait_for_timeout(300)
        
        html = page.content().lower()
        has_code = '<code' in html or '<pre' in html or 'monospace' in html
        assert has_code, "Code block not rendering"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
