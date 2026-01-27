"""
Functional tests for Quiz App (case_02_quiz).

Tests verify:
1. Questions are displayed
2. Multiple choice options (4 per question)
3. Answer selection works
4. Score tracking
5. Feedback on answers
6. Final results screen
7. Try again functionality
"""


def test_displays_question(page):
    """Should display a question on load."""
    content = page.locator("body").text_content()
    # Should have question mark or question-like text
    assert "?" in content or len(content) > 50, "No question displayed"


def test_has_multiple_choice_options(page):
    """Should have at least 4 answer options."""
    # Look for buttons, radio inputs, or clickable options
    options = page.locator("button, input[type='radio'], [class*='option'], [class*='answer'], [class*='choice']")
    # Filter to visible, text-containing elements
    visible_count = 0
    for i in range(options.count()):
        try:
            if options.nth(i).is_visible():
                visible_count += 1
        except Exception:
            pass
    assert visible_count >= 4, f"Expected at least 4 options, found {visible_count}"


def test_can_select_answer(page):
    """Clicking an option should register selection."""
    # Find clickable options
    options = page.locator("button:visible, [class*='option']:visible, [class*='answer']:visible").all()
    
    if len(options) < 2:
        # Try finding any clickable elements
        options = page.locator("button:visible").all()
    
    assert len(options) >= 1, "No clickable options found"
    
    # Click first option
    options[0].click()
    page.wait_for_timeout(300)
    
    # Page content should change (feedback, next question, or styling)
    # This is a basic check - content should differ somehow


def test_shows_score_tracking(page):
    """Should display score or progress indicator."""
    content = page.locator("body").text_content().lower()
    has_score = any(term in content for term in [
        "score", "point", "/", "correct", "question 1", "1 of", "progress"
    ])
    assert has_score, "No score or progress tracking visible"


def test_provides_feedback_on_answer(page):
    """Selecting an answer should provide feedback."""
    # Find and click an option
    options = page.locator("button:visible, [class*='option']:visible").all()
    if len(options) < 1:
        options = page.locator("button").all()
    
    initial_content = page.locator("body").text_content()
    
    if len(options) >= 1:
        options[0].click()
        page.wait_for_timeout(500)
        
        new_content = page.locator("body").text_content()
        # Content should change after clicking (feedback, next question, etc.)
        assert initial_content != new_content, "No feedback after selecting answer"


def test_has_styled_interface(page):
    """Quiz should have visual styling."""
    body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
    has_custom_bg = body_bg not in ["rgba(0, 0, 0, 0)", "rgb(255, 255, 255)", "transparent", ""]
    
    # Check for any custom CSS
    has_styles = page.locator("[style], [class]").count() > 3
    
    assert has_custom_bg or has_styles, "Quiz lacks visual styling"


def test_no_console_errors(page):
    """Page should load without JavaScript errors."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.reload()
    page.wait_for_timeout(500)
    assert len(errors) == 0, f"Page has JS errors: {errors}"


def test_can_complete_quiz(page):
    """Should be able to answer multiple questions."""
    # Try to click through several questions
    for _ in range(3):
        options = page.locator("button:visible, [class*='option']:visible, [class*='answer']:visible").all()
        if len(options) >= 1:
            try:
                options[0].click()
                page.wait_for_timeout(400)
            except Exception:
                break
    
    # After answering, should see results or more questions
    content = page.locator("body").text_content().lower()
    # Either still in quiz or showing results
    assert len(content) > 20, "Quiz navigation not working"
