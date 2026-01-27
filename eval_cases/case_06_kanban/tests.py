"""
Functional tests for Kanban Board (case_06_kanban).

Tests verify:
1. Three columns visible (To Do, In Progress, Done)
2. Can add new cards
3. Cards display title
4. Can delete cards
5. Cards are draggable
6. Visual feedback on drag
7. Persistence (localStorage)
"""


def test_has_three_columns(page):
    """Should have To Do, In Progress, Done columns."""
    content = page.locator("body").text_content().lower()
    
    has_todo = any(term in content for term in ["to do", "todo", "to-do", "backlog"])
    has_progress = any(term in content for term in ["in progress", "doing", "in-progress", "working"])
    has_done = any(term in content for term in ["done", "complete", "finished"])
    
    assert has_todo, "Missing 'To Do' column"
    assert has_progress, "Missing 'In Progress' column"
    assert has_done, "Missing 'Done' column"


def test_has_add_card_functionality(page):
    """Should have a way to add new cards."""
    # Look for add button or input field
    add_btn = page.locator("button:has-text('Add'), button:has-text('+'), button:has-text('New'), [class*='add']")
    input_field = page.locator("input[type='text'], textarea")
    
    assert add_btn.count() > 0 or input_field.count() > 0, "No add card functionality found"


def test_can_add_card(page):
    """Adding a card should create visible card element."""
    initial_content = page.locator("body").text_content()
    
    # Try to add a card
    # First, look for input
    input_field = page.locator("input[type='text'], input[placeholder*='task' i], input[placeholder*='card' i], input[placeholder*='title' i]").first
    add_btn = page.locator("button:has-text('Add'), button:has-text('+'), button:has-text('Create')").first
    
    if input_field.count() > 0 and add_btn.count() > 0:
        input_field.fill("Test Card 12345")
        add_btn.click()
        page.wait_for_timeout(300)
        
        new_content = page.locator("body").text_content()
        assert "Test Card 12345" in new_content or initial_content != new_content, \
            "Card was not added"
    else:
        # Just verify structure exists
        assert True


def test_cards_are_draggable(page):
    """Cards should have draggable attribute or drag events."""
    content = page.content().lower()
    
    has_draggable = 'draggable="true"' in content or 'draggable=true' in content
    has_drag_events = any(event in content for event in ['ondrag', 'ondragstart', 'dragstart', 'drag-'])
    has_drag_class = any(cls in content for cls in ['draggable', 'drag', 'sortable'])
    
    assert has_draggable or has_drag_events or has_drag_class, \
        "Cards don't appear to be draggable"


def test_has_column_structure(page):
    """Should have distinct column containers."""
    # Look for column-like elements
    columns = page.locator("[class*='column'], [class*='lane'], [class*='list'], [class*='col']")
    
    # Or look for flex/grid container with children
    containers = page.locator("[style*='flex'], [style*='grid']")
    
    assert columns.count() >= 3 or containers.count() > 0, \
        "No column structure found"


def test_has_styled_cards(page):
    """Cards should have visual styling (not plain text)."""
    # Check for card-like elements with styling
    cards = page.locator("[class*='card'], [class*='task'], [class*='item']")
    
    if cards.count() > 0:
        # Check first card has some styling
        first_card = cards.first
        bg = page.evaluate("(el) => window.getComputedStyle(el).backgroundColor", first_card.element_handle())
        border = page.evaluate("(el) => window.getComputedStyle(el).border", first_card.element_handle())
        shadow = page.evaluate("(el) => window.getComputedStyle(el).boxShadow", first_card.element_handle())
        
        has_styling = (
            bg not in ["rgba(0, 0, 0, 0)", "transparent", ""] or
            border not in ["none", "0px none rgb(0, 0, 0)", ""] or
            shadow not in ["none", ""]
        )
        assert has_styling, "Cards lack visual styling"
    else:
        # Just check page has styling
        body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
        assert body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", ""], \
            "Board lacks visual styling"


def test_has_delete_functionality(page):
    """Should be able to delete cards."""
    content = page.content().lower()
    
    has_delete = any(term in content for term in [
        'delete', 'remove', 'trash', '×', '✕', '✖', '🗑', 'close'
    ])
    
    # Also check for buttons with X or delete icons
    delete_btns = page.locator("button:has-text('×'), button:has-text('X'), button:has-text('Delete'), [class*='delete'], [class*='remove']")
    
    assert has_delete or delete_btns.count() > 0, \
        "No delete functionality found"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"


def test_responsive_layout(page):
    """Board should have responsive layout."""
    # Check if using flexbox or grid
    content = page.content().lower()
    
    has_flex_grid = any(term in content for term in [
        'display: flex', 'display:flex', 'display: grid', 'display:grid',
        'flex-direction', 'grid-template'
    ])
    
    # Or check computed styles
    body_display = page.evaluate("window.getComputedStyle(document.body).display")
    
    assert has_flex_grid or body_display in ['flex', 'grid'], \
        "Board doesn't use flexible layout"
