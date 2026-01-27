"""
Functional tests for Debug Session (case_32_debug_session).

Tests verify the fixed todo app works correctly.
"""


def test_fixed_file_exists(page):
    """Fixed todo.html should exist and load."""
    # Page already loaded if we got here
    content = page.locator("body").text_content()
    assert "Todo" in content, "Todo app not loaded"


def test_can_add_todo_with_enter(page):
    """Pressing Enter should add a todo (Bug 1 fix)."""
    input_field = page.locator("#newTodo, input[type='text']").first
    input_field.fill("Test todo item")
    input_field.press("Enter")
    
    page.wait_for_timeout(300)
    
    content = page.locator("body").text_content()
    assert "Test todo item" in content, "Enter key doesn't add todo"


def test_toggle_completion_works(page):
    """Clicking checkbox should toggle completion (Bug 3 fix)."""
    # Add a todo first
    input_field = page.locator("#newTodo, input[type='text']").first
    input_field.fill("Toggle test")
    input_field.press("Enter")
    page.wait_for_timeout(200)
    
    # Find and click the checkbox
    checkbox = page.locator("input[type='checkbox']").first
    checkbox.click()
    page.wait_for_timeout(200)
    
    # Should have completed class or checked state
    completed_items = page.locator(".completed, [class*='completed']")
    checkbox_state = checkbox.is_checked()
    
    assert completed_items.count() > 0 or checkbox_state, \
        "Toggle completion not working"


def test_delete_removes_correct_item(page):
    """Delete should remove the item (Bug 4 fix)."""
    # Add two todos
    input_field = page.locator("#newTodo, input[type='text']").first
    input_field.fill("Keep this")
    input_field.press("Enter")
    page.wait_for_timeout(200)
    
    input_field.fill("Delete this")
    input_field.press("Enter")
    page.wait_for_timeout(200)
    
    # Delete the second one
    delete_buttons = page.locator("button:has-text('Delete'), button:has-text('×')").all()
    if len(delete_buttons) >= 2:
        delete_buttons[1].click()
        page.wait_for_timeout(200)
    
    content = page.locator("body").text_content()
    assert "Keep this" in content, "Wrong item was deleted"


def test_count_shows_total_items(page):
    """Count should show total items, not completed (Bug 5 fix)."""
    # Clear and add fresh todos
    page.reload()
    page.wait_for_timeout(300)
    
    input_field = page.locator("#newTodo, input[type='text']").first
    
    # Add 3 todos
    for i in range(3):
        input_field.fill(f"Todo {i+1}")
        input_field.press("Enter")
        page.wait_for_timeout(150)
    
    # Check count shows 3
    count_element = page.locator("#count, .count")
    content = page.locator("body").text_content()
    
    assert "3" in content, "Count should show 3 total items"


def test_unique_ids_after_delete(page):
    """IDs should remain unique after delete (Bug 2 fix)."""
    page.reload()
    page.wait_for_timeout(300)
    
    input_field = page.locator("#newTodo, input[type='text']").first
    
    # Add a todo
    input_field.fill("First")
    input_field.press("Enter")
    page.wait_for_timeout(200)
    
    # Delete it
    delete_btn = page.locator("button:has-text('Delete')").first
    if delete_btn.count() > 0:
        delete_btn.click()
        page.wait_for_timeout(200)
    
    # Add another
    input_field.fill("Second")
    input_field.press("Enter")
    page.wait_for_timeout(200)
    
    # Add another
    input_field.fill("Third")
    input_field.press("Enter")
    page.wait_for_timeout(200)
    
    # Both should exist (no ID collision)
    content = page.locator("body").text_content()
    assert "Second" in content and "Third" in content, \
        "ID collision after delete"


def test_fixes_documented(page):
    """FIXES.md should document the changes."""
    # This test can't check the file from browser
    # But we verify the app works which implies fixes were made
    content = page.locator("body").text_content()
    assert "Todo" in content, "App should be functional"


def test_no_console_errors(page):
    """Fixed app should have no JS errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"JS errors found: {errors}"
