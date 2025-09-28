# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PCI (Physical Cell Identity) planning tool for LTE/NR networks, enhanced to fix critical issues and optimize performance. The tool supports both PCI planning and network parameter updates from existing network data.

## Common Development Commands

### Running the Application
```bash
# Main application entry point
python pci_planning_lte_nr_enhanced.py

# Alternative using batch file (Windows)
run.bat
```

### Testing
```bash
# Run location-based same site conflict test
python test_location_based_same_site.py
```

### Dependencies
The project requires these Python packages:
- pandas
- openpyxl
- numpy

## Code Architecture

### Main Components

1. **pci_planning_lte_nr_enhanced.py** - Main application file containing:
   - `PCIPlanningTool` class: Main application logic and menu system
   - `LTENRPCIPlanner` class: PCI planning algorithms for LTE/NR
   - `NetworkParameterUpdater` class: Updates network parameters from existing data

2. **Data Processing Flow**:
   - Reads input from Excel files in `全量工参/`, `待规划小区/`, `现网工参/` directories
   - Processes LTE and NR data separately with different logic
   - Outputs results to `输出文件/` directory with timestamps

### Key Technical Details

1. **NR PCI Planning**: Uses mod30 logic instead of mod3 for 5G networks
2. **Data Protection**: Only processes data rows (index ≥3), protecting header rows
3. **Matching Logic**:
   - LTE: Uses eNodeB ID + Cell ID for matching
   - NR: Uses MCC + MNC + gNodeB ID + Cell ID for global matching
4. **Performance Optimizations**: Removed unnecessary color formatting to improve speed

### Critical Functions

- `_fill_mnc_from_plmn()`: Extracts MNC from PLMN field, only processes data rows
- `_fill_gnodeb_length()`: Sets gNodeB length based on SSB frequency, only processes data rows
- `_update_lte_parameters()`: Updates LTE parameters with existing network data
- `_update_nr_parameters()`: Updates NR parameters with enhanced matching logic

### File Structure
```
PCI规划/
├── pci_planning_lte_nr_enhanced.py    # Main application
├── 全量工参/                           # Full network parameter files
├── 待规划小区/                         # Cells to be planned
├── 现网工参/                           # Existing network parameter files
└── 输出文件/                           # Output files with timestamps
```

## Important Implementation Notes

1. **Excel File Handling**: Uses openpyxl for Excel operations, pandas for data processing
2. **Error Handling**: Comprehensive error handling with detailed logging
3. **Data Validation**: Validates input files and provides clear error messages
4. **Timestamp Format**: All output files include timestamp in format YYYYMMDD_HHMMSS
5. **Header Protection**: Critical - always use `df.loc[3:, ...]` to protect header rows (indices 0-2)

## Testing Approach

- Unit tests focus on specific functionality (matching logic, data protection)
- Integration tests verify complete workflow with sample data
- Test files are created to validate specific scenarios like location-based conflicts