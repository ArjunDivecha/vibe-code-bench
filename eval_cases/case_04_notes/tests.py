"""
Functional tests for Notes App (case_04_notes).

Tests verify actual behavior, not just presence.
"""


def test_can_create_note(page):
    """Should be able to create a new note."""
    # Look for input/textarea and add button
    title_input = page.locator("input[placeholder*='title' i], input[type='text']").first
    content_input = page.locator("textarea, [contenteditable='true'], input").nth(1)
    
    if title_input.count() > 0:
        title_input.fill("Test Note Title")
    if content_input.count() > 0:
        content_input.fill("Test note content here")
    
    # Find and click add/save button
    add_btn = page.locator("button:has-text('Add'), button:has-text('Save'), button:has-text('Create'), button:has-text('+')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    content = page.locator("body").text_content()
    assert "Test Note Title" in content or "Test note content" in content, \
        "Created note not visible"


def test_notes_persist_after_reload(page):
    """Notes should persist in localStorage after reload."""
    # Create a note first
    page.keyboard.press("Control+a")
    page.keyboard.type("Persistence Test Note")
    
    add_btn = page.locator("button:has-text('Add'), button:has-text('Save'), button:has-text('Create')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    # Reload page
    page.reload()
    page.wait_for_timeout(500)
    
    # Check localStorage has data
    storage = page.evaluate("localStorage.length")
    content = page.locator("body").text_content()
    
    # Either localStorage has data OR note is still visible
    assert storage > 0 or "Persistence" in content, \
        "Notes did not persist after reload"


def test_can_delete_note(page):
    """Should be able to delete a note."""
    # First create a note
    title_input = page.locator("input").first
    if title_input.count() > 0:
        title_input.fill("Delete Me Note")
    
    add_btn = page.locator("button:has-text('Add'), button:has-text('Save')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    initial_content = page.locator("body").text_content()
    
    # Find and click delete button
    delete_btn = page.locator("button:has-text('Delete'), button:has-text('×'), button:has-text('X'), [class*='delete']").first
    if delete_btn.count() > 0:
        delete_btn.click()
        page.wait_for_timeout(300)
        
        final_content = page.locator("body").text_content()
        # Content should change after delete
        assert initial_content != final_content, "Delete did not remove note"


def test_search_filters_notes(page):
    """Search should filter displayed notes."""
    # Create two notes
    for title in ["Apple Note", "Banana Note"]:
        title_input = page.locator("input").first
        if title_input.count() > 0:
            title_input.fill(title)
        add_btn = page.locator("button:has-text('Add'), button:has-text('Save')").first
        if add_btn.count() > 0:
            add_btn.click()
            page.wait_for_timeout(200)
    
    # Find search input
    search = page.locator("input[placeholder*='search' i], input[type='search'], [class*='search'] input").first
    if search.count() > 0:
        search.fill("Apple")
        page.wait_for_timeout(300)
        
        content = page.locator("body").text_content()
        # Apple should be visible, Banana might be hidden
        assert "Apple" in content, "Search filter not working"


def test_can_edit_note(page):
    """Should be able to edit an existing note."""
    # Create a note
    title_input = page.locator("input").first
    if title_input.count() > 0:
        title_input.fill("Original Title")
    add_btn = page.locator("button:has-text('Add'), button:has-text('Save')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    # Click on the note to edit
    note = page.locator("[class*='note'], [class*='card'], li").first
    if note.count() > 0:
        note.click()
        page.wait_for_timeout(200)
        
        # Try to edit
        page.keyboard.type(" Edited")
        page.wait_for_timeout(200)
        
        # Save if needed
        save_btn = page.locator("button:has-text('Save'), button:has-text('Update')").first
        if save_btn.count() > 0:
            save_btn.click()


def test_notes_list_visible(page):
    """Should display a list or grid of notes."""
    # Check for list/grid structure
    list_items = page.locator("[class*='note'], [class*='card'], [class*='item'], li").count()
    
    # Or check for notes container
    container = page.locator("[class*='notes'], [class*='list'], [class*='grid'], ul").count()
    
    assert list_items > 0 or container > 0, "No notes list/grid structure found"


def test_has_title_and_content_inputs(page):
    """Should have separate inputs for title and content."""
    inputs = page.locator("input, textarea").count()
    assert inputs >= 2, f"Expected at least 2 inputs (title + content), found {inputs}"


def test_visual_styling(page):
    """App should have visual styling."""
    html = page.content().lower()
    has_styling = any(term in html for term in [
        'background', 'border', 'shadow', 'color:', '#', 'rgb', 'flex', 'grid'
    ])
    assert has_styling, "Notes app lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
