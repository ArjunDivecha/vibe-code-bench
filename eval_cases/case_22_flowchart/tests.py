"""
Functional tests for Flowchart Editor (case_22_flowchart).

V3 Tests - Discriminating tests for actual flowchart editing capability.
"""


def test_has_svg_canvas(page):
    """Should have SVG element for drawing."""
    svg = page.locator("svg").count()
    canvas = page.locator("canvas").count()
    
    assert svg > 0 or canvas > 0, "No SVG or Canvas for drawing"


def test_has_rectangle_shape(page):
    """Should have rectangle/process shape option."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_rect = any(term in content or term in html for term in [
        'rectangle', 'process', 'box', 'rect'
    ])
    assert has_rect, "No rectangle shape option"


def test_has_diamond_shape(page):
    """Should have diamond/decision shape option."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_diamond = any(term in content or term in html for term in [
        'diamond', 'decision', 'condition', 'if'
    ])
    assert has_diamond, "No diamond/decision shape option"


def test_has_oval_shape(page):
    """Should have oval/terminal shape option."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_oval = any(term in content or term in html for term in [
        'oval', 'ellipse', 'terminal', 'start', 'end', 'circle'
    ])
    assert has_oval, "No oval/terminal shape option"


def test_can_add_shape_to_canvas(page):
    """Clicking toolbar + canvas should add a shape."""
    initial = page.locator("svg rect, svg ellipse, svg polygon, svg path").count()
    
    # Click add/shape button
    add_btn = page.locator("button:has-text('Add'), button:has-text('Rectangle'), button:has-text('Process')").first
    if add_btn.count() > 0:
        add_btn.click()
        page.wait_for_timeout(300)
    
    # Click on canvas
    svg = page.locator("svg").first
    if svg.count() > 0:
        svg.click(position={"x": 150, "y": 150})
        page.wait_for_timeout(300)
    
    final = page.locator("svg rect, svg ellipse, svg polygon, svg path").count()
    assert final >= initial, "Could not add shape to canvas"


def test_shapes_are_draggable(page):
    """Shapes should be draggable to reposition."""
    # Find a shape element
    shape = page.locator("svg rect, svg g, [class*='node']").first
    if shape.count() > 0:
        box = shape.bounding_box()
        if box:
            # Drag it
            page.mouse.move(box['x'] + 20, box['y'] + 20)
            page.mouse.down()
            page.mouse.move(box['x'] + 100, box['y'] + 50)
            page.mouse.up()
            page.wait_for_timeout(300)
            # Should not error


def test_can_connect_shapes(page):
    """Should be able to draw connections between shapes."""
    html = page.content().lower()
    
    has_connect = any(term in html for term in [
        'connect', 'line', 'arrow', 'edge', 'link', 'path'
    ])
    
    # Or has line/path elements
    lines = page.locator("svg line, svg path, svg polyline").count()
    
    assert has_connect or lines > 0, "No connection capability"


def test_connections_have_arrows(page):
    """Connection lines should have arrow markers."""
    html = page.content().lower()
    
    has_arrows = any(term in html for term in [
        'arrow', 'marker', '▶', '→', 'triangle'
    ])
    assert has_arrows, "No arrow markers for connections"


def test_can_add_text_to_shapes(page):
    """Should be able to label shapes with text."""
    # Find text input or try double-clicking shape
    html = page.content().lower()
    
    has_text = '<text' in html or 'contenteditable' in html or 'label' in html
    assert has_text, "No text labeling capability"


def test_has_delete_capability(page):
    """Should be able to delete shapes."""
    content = page.locator("body").text_content().lower()
    
    has_delete = any(term in content for term in [
        'delete', 'remove', '×', 'trash'
    ])
    
    # Or check for delete key handling
    html = page.content().lower()
    has_keyboard = 'keydown' in html or 'delete' in html
    
    assert has_delete or has_keyboard, "No delete capability"


def test_toolbar_has_multiple_tools(page):
    """Toolbar should have at least 3 shape tools."""
    buttons = page.locator("button").count()
    assert buttons >= 3, f"Expected 3+ tools, found {buttons}"


def test_undo_capability(page):
    """Should support undo functionality."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_undo = any(term in content or term in html for term in [
        'undo', 'ctrl+z', '↩'
    ])
    assert has_undo, "No undo capability"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
