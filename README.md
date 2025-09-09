# Student Analytics MVP (Excel → Insights)

## Overview
This project analyzes student performance data from Excel files. It normalizes incoming columns to a canonical schema and computes weighted scores, semester trends, and configurable flags. The interface is built with [Streamlit](https://streamlit.io/), while core logic lives in standalone Python modules for data loading, schema management, and analytics.

## Features
- Upload Excel files with student grades
- Normalize columns to a canonical schema
- Compute weighted scores and semester trends
- Flag students based on configurable criteria
- Export filtered results to CSV
- Streamlit UI for browsing, filtering, and visualization

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/OmerMichael/student-analytics-mvp.git
   cd student-analytics-mvp
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the application:
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage
1. Upload an Excel file containing student grades.
2. Select a student to view their normalized data and computed metrics.
3. Export filtered results to CSV for further analysis.
4. *(Optional)* View basic charts or add comments within the UI.

## Development
- Core modules live under `src/`:
  - `data_loader.py`
  - `schema.py`
  - `analytics.py`
- `streamlit_app.py` handles the UI only and imports these modules.
- Recommended: add unit tests for data transformation logic using `pytest`.

## Known Limitations
- Single-file Streamlit session (no persistence)
- Manual schema mapping for some fields
- Basic visualization (charts are minimal)

## Roadmap
- Add persistent storage
- Add user authentication and roles
- Improve data visualization
- Expand test coverage

## License
This project is licensed under the [MIT License](LICENSE).
