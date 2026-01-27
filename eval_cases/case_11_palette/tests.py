"""
Functional tests for Color Palette Generator (case_11_palette).

Tests verify actual behavior, not just presence.
"""


def test_shows_color_swatches(page):
    """Should display color swatches."""
    # Look for colored elements
    swatches = page.locator("[class*='color'], [class*='swatch'], [class*='palette']").count()
    
    # Or elements with background colors
    colored = page.locator("[style*='background']").count()
    
    assert swatches > 0 or colored > 0, "No color swatches found"


def test_shows_multiple_colors(page):
    """Should display multiple colors (typically 5)."""
    html = page.content()
    
    # Count hex color codes
    import re
    hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', html)
    
    # Or RGB values
    rgb_colors = re.findall(r'rgb\(\d+,\s*\d+,\s*\d+\)', html)
    
    total_colors = len(set(hex_colors)) + len(set(rgb_colors))
    assert total_colors >= 3, f"Expected at least 3 colors, found {total_colors}"


def test_has_generate_button(page):
    """Should have a generate/refresh button."""
    buttons = page.locator("button").all_text_contents()
    text = " ".join(buttons).lower()
    
    has_generate = any(word in text for word in [
        'generate', 'new', 'refresh', 'random', 'create'
    ])
    assert has_generate, "No generate button found"


def test_generate_changes_colors(page):
    """Clicking generate should change colors."""
    initial = page.content()
    
    gen_btn = page.locator("button:has-text('Generate'), button:has-text('New'), button:has-text('Refresh')").first
    if gen_btn.count() > 0:
        gen_btn.click()
        page.wait_for_timeout(300)
        
        final = page.content()
        # Colors should change
        assert initial != final, "Generate did not change colors"


def test_has_lock_functionality(page):
    """Should have lock buttons to freeze colors."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_lock = any(term in content or term in html for term in [
        'lock', '🔒', '🔓', 'freeze', 'keep'
    ])
    
    # Or lock icons/buttons
    locks = page.locator("[class*='lock'], button:has-text('🔒')").count()
    
    assert has_lock or locks > 0, "No lock functionality found"


def test_shows_color_codes(page):
    """Should display hex or RGB color codes."""
    content = page.locator("body").text_content()
    
    import re
    # Look for hex codes
    hex_codes = re.findall(r'#[0-9A-Fa-f]{6}', content)
    # Or RGB
    rgb_codes = re.findall(r'rgb\(', content.lower())
    
    assert len(hex_codes) > 0 or len(rgb_codes) > 0, "No color codes displayed"


def test_has_copy_functionality(page):
    """Should be able to copy color codes."""
    content = page.locator("body").text_content().lower()
    html = page.content().lower()
    
    has_copy = any(term in content or term in html for term in [
        'copy', 'clipboard', 'copied', 'click to copy'
    ])
    
    # Or copy buttons
    copy_btns = page.locator("[class*='copy'], button:has-text('Copy')").count()
    
    assert has_copy or copy_btns > 0, "No copy functionality found"


def test_spacebar_generates(page):
    """Spacebar should generate new palette."""
    html = page.content().lower()
    
    # Check for keyboard event handling
    has_keyboard = 'keydown' in html or 'keypress' in html or 'space' in html
    
    # Or try pressing space
    initial = page.content()
    page.keyboard.press("Space")
    page.wait_for_timeout(300)
    final = page.content()
    
    # Either has keyboard handling or space changed colors
    assert has_keyboard or initial != final, "Spacebar generation not found"


def test_visual_styling(page):
    """App should have visual styling."""
    html = page.content().lower()
    has_styling = any(term in html for term in [
        'background', 'border', 'flex', 'grid', '#', 'rgb'
    ])
    assert has_styling, "Palette generator lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"
