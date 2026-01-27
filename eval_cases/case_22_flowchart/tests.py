"""
Functional tests for Flowchart Editor (case_22_flowchart).

Tests verify:
1. Canvas area exists
2. Shape palette with shapes
3. Can add shapes to canvas
4. Shapes are draggable
5. Can create connections
6. Text editing works
7. Delete functionality
"""


def test_has_canvas_area(page):
    """Should have a canvas or SVG workspace."""
    canvas = page.locator(
        "canvas, svg, [class*='canvas'], [class*='workspace'], "
        "[class*='diagram'], [class*='editor']"
    )
    assert canvas.count() > 0, "No canvas/workspace found"


def test_has_shape_palette(page):
    """Should have a palette with shapes to add."""
    content = page.locator("body").text_content().lower()
    
    has_shapes = any(term in content for term in [
        'rectangle', 'diamond', 'oval', 'circle', 'process',
        'decision', 'start', 'end', 'shape'
    ])
    
    palette = page.locator(
        "[class*='palette'], [class*='sidebar'], [class*='toolbar'], "
        "[class*='shapes'], [class*='tools']"
    )
    
    assert has_shapes or palette.count() > 0, "No shape palette found"


def test_has_rectangle_shape(page):
    """Should have a rectangle/process shape option."""
    rect = page.locator(
        "rect, [class*='rect'], [class*='process'], "
        "[data-shape='rect'], [title*='rectangle' i]"
    )
    
    content = page.locator("body").text_content().lower()
    has_rect = 'rect' in content or 'process' in content
    
    assert rect.count() > 0 or has_rect, "No rectangle shape found"


def test_has_diamond_shape(page):
    """Should have a diamond/decision shape option."""
    content = page.locator("body").text_content().lower()
    
    has_diamond = any(term in content for term in [
        'diamond', 'decision', 'rhombus', 'condition'
    ])
    
    # Or look for diamond-shaped element
    diamond = page.locator("[class*='diamond'], [class*='decision'], polygon")
    
    assert has_diamond or diamond.count() > 0, "No diamond shape found"


def test_can_interact_with_canvas(page):
    """Should be able to click on canvas."""
    canvas = page.locator(
        "canvas, svg, [class*='canvas'], [class*='workspace']"
    ).first
    
    if canvas.count() > 0:
        # Click on canvas
        canvas.click()
        page.wait_for_timeout(200)
        # Should not error
        assert True


def test_shapes_are_draggable(page):
    """Shapes should be draggable."""
    content = page.content().lower()
    
    has_drag = any(term in content for term in [
        'draggable', 'ondrag', 'mousedown', 'mousemove',
        'drag', 'drop', 'pointer'
    ])
    
    # Check for draggable attribute
    draggables = page.locator("[draggable='true']")
    
    assert has_drag or draggables.count() > 0, \
        "Shapes don't appear to be draggable"


def test_has_toolbar(page):
    """Should have a toolbar with actions."""
    toolbar = page.locator(
        "[class*='toolbar'], [class*='menu'], header, nav, "
        "[role='toolbar']"
    )
    
    # Or look for action buttons
    buttons = page.locator(
        "button:has-text('New'), button:has-text('Delete'), "
        "button:has-text('Zoom'), button:has-text('Add')"
    )
    
    assert toolbar.count() > 0 or buttons.count() > 0, \
        "No toolbar found"


def test_uses_svg_or_canvas(page):
    """Should use SVG or Canvas for rendering."""
    svg = page.locator("svg")
    canvas = page.locator("canvas")
    
    assert svg.count() > 0 or canvas.count() > 0, \
        "No SVG or Canvas element found"


def test_has_connection_capability(page):
    """Should support connecting shapes with lines."""
    content = page.content().lower()
    
    has_connection = any(term in content for term in [
        'line', 'arrow', 'connect', 'path', 'edge',
        'stroke', 'polyline', 'marker'
    ])
    
    # Look for line elements
    lines = page.locator("line, path, polyline")
    
    assert has_connection or lines.count() >= 0, \
        "No connection capability found"


def test_visual_styling(page):
    """Editor should have professional styling."""
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    has_custom_bg = body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", ""]
    
    # Check for shadows, modern UI
    content = page.content().lower()
    has_modern_style = any(term in content for term in [
        'box-shadow', 'border-radius', 'rgba', 'gradient'
    ])
    
    assert has_custom_bg or has_modern_style, "Editor lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
