# Detailed Project Contributions

## Nikoloz Topuridze (@nikatopu)

### Core Architecture
- Designed the entire project structure and workflow
- Implemented the main scraping pipeline in `collector.py`
- Created all data models in `data_models.py` (StateData, YearData, ElectionResult)
- Built the complete file handling system in `file_handler.py` with:
  - CSV export functionality
  - JSON export functionality
  - Automatic directory creation
  - Comprehensive error handling

### Scraping Engine
- Developed the request handling system with:
  - Rate limiting (1s delay between requests)
  - Session persistence
  - Custom user agents
  - Timeout handling
- Implemented the state link parser in `parser.py`
- Created the state details parser (electoral votes, population attempts)
- Optimized performance with ThreadPoolExecutor (5x faster scraping)

### Data Processing
- Designed the data validation system:
  - Type checking for all fields
  - Vote percentage validation (0-100%)
  - Vote count validation (positive integers)
- Built the data cleaning pipeline:
  - Handling missing values
  - Text normalization
  - Error recovery mechanisms

### Documentation & Maintenance
- Created comprehensive README.md
- Set up requirements.txt with all dependencies
- Configured .gitignore properly
- Wrote the main.py entry point script
- Added detailed docstrings throughout the codebase

## Nino Bendianishvili (@NinoBendianishvili)

### Visualization System
- Developed the complete visualization engine in `analyzer.py`:
  - National vote trend charts
  - State-level vote percentage charts
  - Choropleth election maps
- Created both HTML report templates:
  - `map_report_template.html` (interactive maps)
  - `report_template.html` (vote percentage analysis)

### Data Analysis
- Implemented Plotly visualization features:
  - Color-coded by party (red/blue)
  - Hover tooltips with candidate info
  - Percentage formatting
  - Responsive design
- Built the Jinja2 template rendering system
- Added comprehensive logging throughout analyzer

### Data Processing
- Developed the data cleaning pipeline for visualization:
  - Handling missing percentages
  - Winner determination logic
  - Year filtering
  - State grouping
- Created the national vote calculation system

### Core Infrastructure
- Set up initial project structure
- Implemented first data models prototype
- Created early version of main.py
- Established initial scraping framework

## Joint Contributions

### System Integration
- Combined scraping and visualization pipelines
- Unified data models between components
- Standardized error handling approaches
- Synchronized CSV/JSON data formats

### Testing & Debugging
- Tested all components end-to-end
- Fixed cross-browser visualization issues
- Resolved data consistency problems
- Optimized memory usage

### Documentation
- Collaborated on README.md
- Maintained consistent code comments
- Created example output files
- Documented all edge cases

## Timeline of Major Milestones
1. **Project Setup** (Apr 6)
   - Initial repository creation
   - Basic scaffolding

2. **Core Development** (Apr 12-13)
   - Completed scraping engine
   - Implemented data models
   - Built file export system

3. **Visualization Phase** (Apr 13)
   - Developed analysis tools
   - Created interactive maps
   - Built HTML reports

4. **Final Polish** (Apr 13)
   - Performance optimization
   - Comprehensive documentation
   - Error handling improvements