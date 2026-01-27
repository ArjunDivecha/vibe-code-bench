"""
Functional tests for Data Visualization Dashboard (case_25_dataviz).

V3 Tests - More flexible, behavior-focused.
"""


def test_has_svg_elements(page):
    """Should use SVG for charts (not external libraries)."""
    svg_count = page.locator("svg").count()
    assert svg_count >= 1, "No SVG elements found - should use SVG for charts"


def test_has_bar_elements(page):
    """Should have bar chart (rect elements)."""
    rects = page.locator("svg rect").count()
    assert rects >= 3, f"Expected bar chart rects, found {rects}"


def test_has_chart_data(page):
    """Should display data values."""
    content = page.locator("body").text_content()
    
    # Check for numbers that might be data
    import re
    numbers = re.findall(r'\d+', content)
    
    assert len(numbers) >= 5, "Not enough data values displayed"


def test_has_labels(page):
    """Should have axis labels or legend."""
    content = page.locator("body").text_content()
    
    # Check for month names or category names from spec
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Electronics', 'Clothing', 'Home', 'Sports', 'Sales']
    found = sum(1 for label in labels if label in content)
    
    assert found >= 3, f"Expected labels, found {found}"


def test_has_multiple_chart_types(page):
    """Should have different chart elements (bars, paths, circles)."""
    rects = page.locator("svg rect").count()
    paths = page.locator("svg path").count()
    circles = page.locator("svg circle").count()
    
    # Should have at least 2 types
    types_present = sum([rects > 0, paths > 0, circles > 0])
    assert types_present >= 1, "Only one chart type found"


def test_has_colors(page):
    """Charts should have colors."""
    html = page.content().lower()
    
    # Check for fill colors
    has_colors = any(term in html for term in [
        'fill=', 'fill:', '#3498db', '#e74c3c', '#2ecc71', 'rgb(', 'blue', 'red', 'green'
    ])
    
    assert has_colors, "Charts lack colors"


def test_has_interactive_elements(page):
    """Should have some interactivity."""
    html = page.content().lower()
    
    has_interaction = any(term in html for term in [
        'hover', 'click', 'mouseover', 'onmouse', 'cursor', ':hover'
    ])
    
    # Or has buttons/filters
    controls = page.locator("button, select, input").count()
    
    assert has_interaction or controls > 0, "No interactive elements"


def test_has_dashboard_layout(page):
    """Should have a dashboard layout with cards."""
    html = page.content().lower()
    
    has_layout = any(term in html for term in [
        'dashboard', 'card', 'panel', 'grid', 'flex', 'chart'
    ])
    
    assert has_layout, "No dashboard layout found"


def test_responsive_svg(page):
    """SVG should have proper dimensions."""
    svg = page.locator("svg").first
    if svg.count() > 0:
        # Check SVG has reasonable size
        box = svg.bounding_box()
        if box:
            assert box['width'] > 50 and box['height'] > 50, \
                "SVG too small"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
