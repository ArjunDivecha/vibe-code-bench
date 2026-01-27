# Build me a Flowchart Editor

I want a visual flowchart/diagram editor in a single HTML file. Think simple Lucidchart or draw.io.

## Core Features

1. **Canvas area** - Large workspace where diagrams are drawn
2. **Shape palette** - Sidebar with shapes to add:
   - Rectangle (process)
   - Diamond (decision)
   - Oval (start/end)
   - Parallelogram (input/output)
3. **Drag shapes from palette** onto canvas
4. **Move shapes** by dragging on canvas
5. **Connect shapes** - Click and drag from one shape to another to create arrows
6. **Edit text** - Double-click shape to edit its label
7. **Delete** - Select and press Delete, or right-click menu

## Connection Lines

- Arrows should connect from edge of source to edge of target
- Lines should update when shapes are moved
- Straight lines are fine (curved optional)
- Arrowhead at target end

## UI Requirements

- **Toolbar** at top or side with: New, Delete, Zoom In/Out
- **Shape palette** on left side
- **Canvas** in center, should be scrollable/pannable
- **Selected shape** shows resize handles or highlight
- Grid background (optional but nice)

## Behavior

- Shapes snap to grid (optional)
- Undo/Redo with Ctrl+Z / Ctrl+Y (optional but nice)
- Export as SVG or PNG (optional)

## Technical

- Use SVG or Canvas for rendering
- Vanilla JavaScript, no libraries
- Single HTML file with embedded CSS/JS

Make it look professional - modern UI with shadows, clean colors.
