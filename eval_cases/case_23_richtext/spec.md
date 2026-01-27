# Build me a Rich Text Editor

I want a WYSIWYG rich text editor in a single HTML file. Think simple Google Docs or Medium editor.

## Core Features

1. **Editable content area** - Large text editing area
2. **Formatting toolbar** with buttons for:
   - **Bold** (Ctrl+B)
   - **Italic** (Ctrl+I)
   - **Underline** (Ctrl+U)
   - **Strikethrough**
   - **Headings** (H1, H2, H3)
   - **Lists** (bullet and numbered)
   - **Links** (add/edit hyperlinks)
   - **Text alignment** (left, center, right, justify)

3. **Undo/Redo** - Ctrl+Z and Ctrl+Y should work
4. **Character/word count** - Show at bottom

## Advanced Features (bonus)

- **Text color** picker
- **Highlight/background color**
- **Font size** selector
- **Block quotes**
- **Code blocks** (monospace)
- **Insert horizontal rule**

## UI Requirements

- **Toolbar** at top with formatting buttons (icons preferred)
- **Content area** below, like a document page
- **Clean, minimal design** - focus on content
- Buttons should show active state when format is applied

## Behavior

- Formatting applies to selected text
- If no selection, toggle format for next typed text
- Keyboard shortcuts should work
- Content should persist in localStorage (optional)

## Technical

- Use `contenteditable` or build from scratch
- Vanilla JavaScript, no libraries
- Single HTML file with embedded CSS/JS
- Use `document.execCommand` or Selection API

Make it look like a professional document editor - white page, subtle shadows.
