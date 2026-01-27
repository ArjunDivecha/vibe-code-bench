# Build me an Interactive Data Visualization Dashboard

I want a data visualization dashboard in a single HTML file. Think a mini Tableau or simple analytics dashboard.

## Core Features

1. **Multiple chart types** (all drawn with SVG, no libraries):
   - **Bar chart** - Horizontal or vertical bars
   - **Line chart** - Time series data with points and lines
   - **Pie/Donut chart** - Category breakdown
   - **Area chart** (optional)

2. **Interactive features**:
   - **Hover tooltips** - Show values on hover
   - **Click to filter** - Click legend items to show/hide data
   - **Responsive** - Charts resize with window

3. **Data controls**:
   - **Date range selector** - Filter data by time period
   - **Category filters** - Checkboxes or dropdown
   - **Data set switcher** - Toggle between sample datasets

## Sample Data

Use mock sales data:
```javascript
const data = {
  months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  sales: [120, 150, 180, 140, 200, 190],
  categories: [
    { name: 'Electronics', value: 450, color: '#3498db' },
    { name: 'Clothing', value: 280, color: '#e74c3c' },
    { name: 'Home', value: 320, color: '#2ecc71' },
    { name: 'Sports', value: 150, color: '#f39c12' }
  ]
};
```

## Layout

- **Header** with title and global filters
- **Grid of cards** containing charts
- **Each card** has: title, chart, maybe summary stat
- **Responsive grid** - 2x2 on desktop, 1 column on mobile

## Chart Requirements

- **Axes** - Labeled X and Y axes where appropriate
- **Legends** - Show what colors mean
- **Animations** - Smooth transitions when data changes (optional)
- **Grid lines** - Subtle reference lines

## Styling

- Modern dashboard aesthetic (dark or light theme)
- Cards with shadows
- Consistent color palette
- Clean typography

Single HTML file with embedded CSS/JS. Draw charts with SVG (no Chart.js, D3, etc).
