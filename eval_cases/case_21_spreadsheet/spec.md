# Build me a Simple Spreadsheet

I want a basic spreadsheet application in a single HTML file. Here's what it needs:

## Core Features

1. **Grid of cells** - At least 10 columns (A-J) and 20 rows
2. **Cell selection** - Click to select, show which cell is active
3. **Cell editing** - Type to enter data, Enter to confirm
4. **Formula support** - Cells starting with `=` are formulas:
   - Basic math: `=5+3`, `=10*2`, `=100/4`
   - Cell references: `=A1+B1`, `=A1*C3`
   - SUM function: `=SUM(A1:A5)`
   - Simple functions: `=MIN(A1:A5)`, `=MAX(A1:A5)`, `=AVG(A1:A5)`

## UI Requirements

- **Column headers** (A, B, C...) at top
- **Row numbers** (1, 2, 3...) on left
- **Formula bar** showing the formula when a formula cell is selected
- **Active cell highlight** - border or background color
- **Resize columns** by dragging header borders (optional but nice)

## Behavior

- When a referenced cell changes, formulas should recalculate
- Show formula result in cell, actual formula in formula bar
- Handle circular references gracefully (show error, don't crash)
- Tab key moves to next cell, Enter moves down

## Styling

- Clean, spreadsheet-like appearance
- Alternating row colors or grid lines
- Fixed header row/column that doesn't scroll away

Make it a single HTML file with embedded CSS and JavaScript. No external libraries.
