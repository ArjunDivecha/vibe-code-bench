"""
Functional tests for Data Visualization Dashboard (case_25_dataviz).

V3 Tests - Discriminating tests for actual data visualization.
"""


def test_uses_svg_not_libraries(page):
    """Should use native SVG, not external charting libraries."""
    html = page.content().lower()
    
    # Check no external libraries
    forbidden = ['chart.js', 'd3.', 'plotly', 'highcharts', 'echarts']
    uses_library = any(lib in html for lib in forbidden)
    
    svg_count = page.locator("svg").count()
    assert svg_count > 0 and not uses_library, "Should use native SVG"


def test_has_bar_chart(page):
    """Should have a bar chart with rect elements."""
    rects = page.locator("svg rect").count()
    assert rects >= 5, f"Expected 5+ bar rects, found {rects}"


def test_bar_chart_has_varied_heights(page):
    """Bar chart should have bars of different heights."""
    rects = page.locator("svg rect").all()
    if len(rects) >= 3:
        heights = set()
        for rect in rects[:5]:
            try:
                h = rect.get_attribute("height")
                if h:
                    heights.add(h)
            except:
                pass
        assert len(heights) >= 2, "All bars same height - no data variance"


def test_has_line_chart(page):
    """Should have a line chart (path or polyline)."""
    paths = page.locator("svg path, svg polyline").count()
    assert paths >= 1, "No line chart path found"


def test_has_pie_chart(page):
    """Should have a pie chart."""
    html = page.content().lower()
    
    # Pie charts use paths with arc commands or circles
    has_pie = 'pie' in html or 'arc' in html or page.locator("svg circle").count() > 3
    assert has_pie, "No pie chart found"


def test_shows_month_labels(page):
    """Should show month labels for time data."""
    content = page.locator("body").text_content()
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    found = sum(1 for m in months if m in content)
    assert found >= 3, f"Expected month labels, found {found}"


def test_shows_category_labels(page):
    """Should show category labels."""
    content = page.locator("body").text_content()
    
    categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Sales']
    found = sum(1 for c in categories if c in content)
    assert found >= 2, f"Expected category labels, found {found}"


def test_has_legend(page):
    """Should have a chart legend."""
    html = page.content().lower()
    content = page.locator("body").text_content().lower()
    
    has_legend = any(term in content or term in html for term in [
        'legend', 'key', '●', '■', '◆'
    ])
    assert has_legend, "No legend found"


def test_charts_have_colors(page):
    """Charts should use distinct colors."""
    html = page.content().lower()
    
    # Count unique colors
    import re
    colors = re.findall(r'#[0-9a-f]{6}', html)
    unique_colors = len(set(colors))
    
    assert unique_colors >= 3, f"Expected 3+ colors, found {unique_colors}"


def test_hover_tooltips(page):
    """Should have hover tooltips."""
    html = page.content().lower()
    
    has_tooltips = any(term in html for term in [
        'tooltip', 'mouseover', 'onmouse', ':hover', 'title'
    ])
    assert has_tooltips, "No hover tooltips"


def test_dashboard_layout(page):
    """Should have dashboard layout with multiple panels."""
    cards = page.locator("[class*='card'], [class*='panel'], [class*='chart']").count()
    assert cards >= 2, "Not enough dashboard panels"


def test_responsive_design(page):
    """Dashboard should be responsive."""
    html = page.content().lower()
    
    has_responsive = any(term in html for term in [
        'flex', 'grid', '@media', 'viewbox', '100%'
    ])
    assert has_responsive, "Dashboard not responsive"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
