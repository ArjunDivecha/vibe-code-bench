"""
Functional tests for Data Visualization Dashboard (case_25_dataviz).

Tests verify:
1. Has SVG charts (not external library)
2. Bar chart present
3. Pie/Donut chart present
4. Line chart present
5. Interactive tooltips
6. Legend present
7. Responsive layout
"""


def test_uses_svg_for_charts(page):
    """Charts should be drawn with SVG."""
    svg_elements = page.locator("svg")
    assert svg_elements.count() > 0, "No SVG elements found - charts should use SVG"


def test_has_bar_chart(page):
    """Should have a bar chart."""
    # Look for rect elements (bars) in SVG
    bars = page.locator("svg rect")
    
    content = page.locator("body").text_content().lower()
    has_bar_mention = 'bar' in content or 'sales' in content
    
    # Should have multiple rect elements for bars
    assert bars.count() >= 3 or has_bar_mention, "No bar chart found"


def test_has_pie_or_donut_chart(page):
    """Should have a pie or donut chart."""
    # Pie charts use path elements with arc commands
    paths = page.locator("svg path")
    
    content = page.locator("body").text_content().lower()
    has_pie_mention = any(term in content for term in [
        'pie', 'donut', 'category', 'breakdown', 'distribution'
    ])
    
    # Check for circular elements
    circles = page.locator("svg circle")
    
    assert paths.count() >= 2 or circles.count() > 0 or has_pie_mention, \
        "No pie/donut chart found"


def test_has_line_chart(page):
    """Should have a line chart."""
    # Line charts use path or polyline
    lines = page.locator("svg path, svg polyline, svg line")
    
    content = page.locator("body").text_content().lower()
    has_line_mention = any(term in content for term in [
        'line', 'trend', 'time', 'series', 'month'
    ])
    
    assert lines.count() >= 1 or has_line_mention, "No line chart found"


def test_has_chart_legend(page):
    """Charts should have legends."""
    legend = page.locator(
        "[class*='legend'], [class*='Legend']"
    )
    
    content = page.locator("body").text_content()
    # Should show category names
    has_categories = any(cat in content for cat in [
        'Electronics', 'Clothing', 'Home', 'Sports', 'Category'
    ])
    
    assert legend.count() > 0 or has_categories, "No legend found"


def test_has_axis_labels(page):
    """Charts should have axis labels."""
    content = page.locator("body").text_content()
    
    # Should have month names or numeric labels
    has_labels = any(label in content for label in [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        '100', '200', 'Sales', 'Value'
    ])
    
    # Look for text elements in SVG
    svg_text = page.locator("svg text")
    
    assert has_labels or svg_text.count() >= 3, "No axis labels found"


def test_has_dashboard_layout(page):
    """Should have a card-based dashboard layout."""
    cards = page.locator(
        "[class*='card'], [class*='panel'], [class*='chart'], "
        "[class*='widget']"
    )
    
    # Check for grid/flex layout
    content = page.content().lower()
    has_layout = any(term in content for term in [
        'grid', 'flex', 'display: grid', 'display: flex'
    ])
    
    assert cards.count() >= 2 or has_layout, "No dashboard layout found"


def test_has_interactive_elements(page):
    """Should have interactive hover or click features."""
    content = page.content().lower()
    
    has_interactivity = any(term in content for term in [
        'hover', 'mouseover', 'mouseenter', 'onclick', 'click',
        'tooltip', ':hover', 'cursor'
    ])
    
    assert has_interactivity, "No interactive features found"


def test_has_filters_or_controls(page):
    """Should have data filters or controls."""
    controls = page.locator(
        "select, input[type='checkbox'], input[type='date'], "
        "button, [class*='filter'], [class*='control']"
    )
    
    assert controls.count() >= 1, "No data filters or controls found"


def test_visual_styling(page):
    """Dashboard should have modern styling."""
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    has_custom_bg = body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", ""]
    
    content = page.content().lower()
    has_modern_style = any(term in content for term in [
        'box-shadow', 'border-radius', 'rgba', 'gradient', '#'
    ])
    
    assert has_custom_bg or has_modern_style, "Dashboard lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
