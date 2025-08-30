import json
import io
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Student Analytics MVP", layout="wide")
st.title("📊 Student Analytics — Excel → Insights (MVP)")

# Load schema
with open("schema.json", "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)
CANON = {c["key"]: c for c in SCHEMA["canonical_fields"]}

st.sidebar.header("העדפות")
role = st.sidebar.radio("תפקיד", ["רכז", "מורה", "תלמיד"], index=0, horizontal=True)

# Weights
st.sidebar.subheader("משקולות ציון כללי")
weights = {}
for k in ["quiz_avg", "quarter_exam", "midterm_mock", "half_semester_final"]:
    default = SCHEMA["weights_default"].get(k, 0.0)
    weights[k] = st.sidebar.slider(CANON[k]["label_he"], 0.0, 1.0, float(default), 0.05)
w_sum = sum(weights.values())
if w_sum == 0:
    st.sidebar.warning("שימו לב: סכום המשקולות 0 — לא יחושב ציון כללי.")
else:
    # normalize to 1.0
    weights = {k: v / w_sum for k, v in weights.items()}

# Thresholds
st.sidebar.subheader("קריטריונים (סינון)")
low_pct_default = int(SCHEMA["thresholds_default"]["low_percentile"])
significant_drop_default = int(SCHEMA["thresholds_default"]["significant_drop_points"])
low_percentile_thr = st.sidebar.number_input("אחוזון ארצי נמוך מ־", 0, 100, low_pct_default, 1)
drop_thr = st.sidebar.number_input("ירידה משמעותית (נק') בין סמסטרים", 0, 100, significant_drop_default, 1)

st.markdown("### 1) העלאת קובץ Excel (או שימוש בדוגמה)")
uploaded = st.file_uploader("בחר קובץ Excel (xlsx/xls)", type=["xlsx", "xls"])
if uploaded is None:
    st.info("לא הועלה קובץ. לנסות דוגמה?")
    if st.button("השתמש בדוגמה המצורפת"):
        uploaded = open("data/sample_class.xlsx", "rb")

if uploaded:
    try:
        df_raw = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"שגיאה בקריאת הקובץ: {e}")
        st.stop()

    st.write("תצוגה ראשונית של הנתונים (5 רשומות ראשונות):")
    st.dataframe(df_raw.head())

    st.markdown("---")
    st.markdown("### 2) מיפוי עמודות (חד פעמי לכל קובץ)")
    st.write("התאם בין שמות העמודות בקובץ לבין שדות סטנדרטיים במערכת.")

    mappings = {}
    columns = ["(ללא)"] + list(df_raw.columns)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**שדה סטנדרטי**")
    with col2:
        st.markdown("**שם בעברית**")
    with col3:
        st.markdown("**העמודה בקובץ שלך**")

    for c in SCHEMA["canonical_fields"]:
        key, label_he, required = c["key"], c["label_he"], c["required"]
        d1, d2, d3 = st.columns([1.2, 1.5, 2.3])
        with d1:
            st.code(key, language="text")
        with d2:
            if required:
                st.markdown(f"**{label_he}**  \n*חובה*")
            else:
                st.markdown(label_he)
        with d3:
            default_index = 0
            # naive heuristic: find the best match by containment
            for i, col in enumerate(columns[1:], start=1):
                if any(hint in str(col) for hint in c.get("examples", [])):
                    default_index = i
                    break
            mappings[key] = st.selectbox("", columns, index=default_index, key=f"map_{key}")

    # Validate required
    missing_required = [c["label_he"] for c in SCHEMA["canonical_fields"] if c["required"] and mappings[c["key"]] == "(ללא)"]
    if missing_required:
        st.error("חסרות עמודות חובה: " + ", ".join(missing_required))
        st.stop()

    # Build normalized DataFrame
    df = pd.DataFrame()
    for k in mappings:
        if mappings[k] != "(ללא)":
            df[k] = df_raw[mappings[k]]

    # Coerce numeric fields to numbers
    numeric_keys = ["quiz_avg", "quarter_exam", "midterm_mock", "half_semester_final", "national_percentile", "homework_rate"]
    for nk in numeric_keys:
        if nk in df.columns:
            df[nk] = pd.to_numeric(df[nk], errors="coerce")

    # Compute overall score
    def overall(row):
        s = 0.0
        for k, w in weights.items():
            s += w * float(row.get(k, np.nan))
        return s
    if any(k in df.columns for k in weights.keys()):
        df["overall_score"] = df.apply(overall, axis=1)

    # Trend between semesters (A/B) — only if we have semester + key fields
    trend_fields = [k for k in weights.keys() if k in df.columns]
    trends = []
    if "semester" in df.columns and "student_name" in df.columns and trend_fields:
        # Expect A/B in semester col
        pivot = df.pivot_table(index="student_name", columns="semester", values=trend_fields, aggfunc="mean")
        # flatten multiindex
        pivot.columns = [f"{k}_{sem}" for (k, sem) in pivot.columns.to_flat_index()]
        pivot = pivot.reset_index()
        trends = []
        for k in trend_fields:
            col_a = f"{k}_א"
            col_b = f"{k}_ב"
            if col_a in pivot.columns and col_b in pivot.columns:
                pivot[f"delta_{k}"] = pivot[col_b] - pivot[col_a]
                trends.append(f"delta_{k}")
        df = df.merge(pivot[["student_name"] + [c for c in pivot.columns if c.startswith("delta_")]], on="student_name", how="left")

    # Criteria flags
    flags = pd.Series([False]*len(df))
    if "national_percentile" in df.columns:
        flags = flags | (df["national_percentile"] < low_percentile_thr)
    for k in trend_fields:
        dcol = f"delta_{k}"
        if dcol in df.columns:
            flags = flags | (df[dcol] <= -abs(drop_thr))
    df["flagged"] = flags

    st.markdown("---")
    st.markdown("### 3) דשבורד כיתתי")
    # Group by latest semester if exists, else as-is
    view_df = df.copy()
    # Show compact set
    show_cols = [c for c in ["student_name", "class_name", "semester", "overall_score", 
                             "quiz_avg", "quarter_exam", "midterm_mock", "half_semester_final",
                             "national_percentile", "flagged"] if c in view_df.columns]
    st.dataframe(view_df[show_cols].sort_values(by=[c for c in ["flagged","overall_score"] if c in show_cols], ascending=[False, False]))

    # Download filtered
    filtered = view_df[view_df["flagged"]] if "flagged" in view_df.columns else view_df
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ הורד CSV מסונן (קריטריונים)", data=csv, file_name="filtered_students.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("### 4) פרופיל תלמיד")
    if "student_name" in df.columns:
        student = st.selectbox("בחר תלמיד/ה", sorted(df["student_name"].dropna().unique().tolist()))
        sdf = df[df["student_name"] == student].copy()
        st.write("רשומות תלמיד (לפי סמסטר/אירוע):")
        st.dataframe(sdf)

        # Simple charts: show evolution per metric by semester (A/B) if available
        if "semester" in sdf.columns:
            for metric in ["quiz_avg", "quarter_exam", "midterm_mock", "half_semester_final"]:
                if metric in sdf.columns:
                    st.write(f"מדד: {CANON[metric]['label_he']}")
                    try:
                        # Plot with streamlit's built-in line_chart (simple)
                        pivot_m = sdf.pivot_table(index="semester", values=metric, aggfunc="mean").reset_index()
                        pivot_m = pivot_m.sort_values("semester")
                        st.line_chart(pivot_m.set_index("semester"))
                    except Exception as e:
                        st.info(f"לא ניתן להציג גרף ל-{metric}: {e}")

        # Show comments
        if "teacher_comment" in sdf.columns:
            st.subheader("הערכת המורה")
            st.write(" \n".join([str(x) for x in sdf["teacher_comment"].dropna().unique().tolist()]))
        if "coordinator_comment" in sdf.columns:
            st.subheader("הערכת הרכז")
            st.write(" \n".join([str(x) for x in sdf["coordinator_comment"].dropna().unique().tolist()]))