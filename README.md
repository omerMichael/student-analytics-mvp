# Student Analytics MVP (Excel → Insights)

This is a quick MVP to upload an Excel file with class results and show dashboards
for **student / teacher / coordinator** roles with Hebrew fields mapping.

## Quick start
1. Create a virtual env (optional) and install:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```
3. In the app:
   - Upload your class Excel file (see `data/sample_class.xlsx` as example).
   - Map your column names to the canonical fields (Hebrew-friendly).
   - Explore **Class Dashboard** and **Student Profile**.
   - Use **Criteria** to filter flagged students (e.g., low percentile).
   - Export filtered results to CSV.

## Files
- `streamlit_app.py` — the Streamlit web app.
- `schema.json` — canonical fields list + Hebrew hints.
- `data/sample_class.xlsx` — sample Excel schema (Hebrew headers).

## Notes
- This MVP assumes **one row per student** (aggregated per semester columns).
- If you have multiple rows per student per event/date, that's supported too:
  map your columns accordingly and the app will pivot when possible.
- You can customize weights in the sidebar (for the "Overall Score" metric).

## Privacy
- This runs locally. No cloud, no uploads elsewhere.
- Secure sensitive data according to your org policy.