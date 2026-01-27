# Build me a Virtual File Browser

I want a file browser/explorer interface in a single HTML file. Think Windows Explorer or macOS Finder, but running entirely in the browser with mock data.

## Core Features

1. **Folder tree** on left sidebar - expandable/collapsible folders
2. **File listing** in main area - shows files in current folder
3. **Breadcrumb navigation** at top - click to navigate up
4. **Different views** - List view and Grid/Icon view toggle
5. **File icons** - Different icons for folders, files, and file types

## Mock File System

Create a mock file system with:
```
/
├── Documents/
│   ├── Reports/
│   │   ├── Q1_Report.pdf
│   │   └── Q2_Report.pdf
│   ├── Notes.txt
│   └── Budget.xlsx
├── Pictures/
│   ├── Vacation/
│   │   ├── beach.jpg
│   │   └── sunset.jpg
│   └── profile.png
├── Downloads/
│   ├── installer.exe
│   └── archive.zip
└── readme.txt
```

## Interactions

- **Click folder** - Opens it, shows contents
- **Double-click file** - Shows file info modal (name, size, type)
- **Right-click** - Context menu with: Open, Rename, Delete, Properties
- **Drag & drop** - Move files between folders (optional)

## UI Requirements

- **Toolbar** with: Back, Forward, Up, New Folder, Delete
- **Search bar** - Filter files by name
- **Status bar** at bottom - Shows item count, selection info
- **Sort options** - By name, size, date, type

## Styling

- Modern file browser aesthetic
- File type icons (use emoji or CSS icons)
- Selected item highlight
- Hover effects

Single HTML file with embedded CSS/JS. No external libraries.
