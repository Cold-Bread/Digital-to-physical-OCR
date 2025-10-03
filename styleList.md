App.tsx - Main container with two key areas:

~~.main-container - Root container~~

ControlPanel.tsx - Bottom control panel with:

.control-panel and .control-panel-bottom classes
Input field (.box-input) for box numbers
Multiple buttons (.button, .button.primary, .button.secondary)
Dividers (.divider)
File input handling
Integration with ImagePopup component

OCROutputs.tsx - Main data display area with:
.outputs-container - Main wrapper
.main-table-container - Box records table (left/main table)
.side-table-container - OCR results table (right/side table)
.table-content - Table content wrappers
Uses Material-UI DataGrid with custom row classes:
.row-match - Strong fuzzy match
.row-partial-match - Partial fuzzy match
.row-no-match - No match found
