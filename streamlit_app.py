import pandas as pd
import streamlit as st

from src.schema import load_schema, canonical_map
from src.data_loader import load_excel, normalize_dataframe
from src.analytics import compute_overall_score, compute_trends, apply_flags, normalize_weights
from src.db import init_db, insert_dataframe, load_records

st.set_page_config(page_title="Student Analytics MVP", layout="wide")
st.title("📊 Student Analytics — Excel → Insights (MVP)")

# Load schema and canonical field map
SCHEMA = load_schema()
CANON = canonical_map(SCHEMA)

# Initialize database connection
conn = init_db()

# Simple authentication data
USERS = {
    "teacher": {"password": "teach", "role": "מורה"},
    "coordinator": {"password": "coord", "role": "רכז"},
    "student": {"password": "stud", "role": "תלמיד", "student_name": "Student Name"},
}


def login() -> None:
    st.sidebar.subheader("כניסה")
    username = st.sidebar.text_input("שם משתמש")
    password = st.sidebar.text_input("סיסמה", type="password")
    if st.sidebar.button("התחבר"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state["user"] = {"username": username, **user}
        else:
            st.sidebar.error("פרטי התחברות שגויים")


if "user" not in st.session_state:
    login()
    st.stop()

user = st.session_state["user"]
role = user["role"]
st.sidebar.success(f"מחובר כ{role}")

st.sidebar.header("העדפות")

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
    weights = normalize_weights(weights)

# Thresholds
st.sidebar.subheader("קריטריונים (סינון)")
low_pct_default = int(SCHEMA["thresholds_default"]["low_percentile"])
significant_drop_default = int(SCHEMA["thresholds_default"]["significant_drop_points"])
low_percentile_thr = st.sidebar.number_input("אחוזון ארצי נמוך מ־", 0, 100, low_pct_default, 1)
drop_thr = st.sidebar.number_input("ירידה משמעותית (נק') בין סמסטרים", 0, 100, significant_drop_default, 1)

if role != "תלמיד":
    st.markdown("### 1) העלאת קובץ Excel (או שימוש בדוגמה)")
    uploaded = st.file_uploader("בחר קובץ Excel (xlsx/xls)", type=["xlsx", "xls"])
    if uploaded is None:
        st.info("לא הועלה קובץ. לנסות דוגמה?")
        if st.button("השתמש בדוגמה המצורפת"):
            uploaded = open("data/sample_class.xlsx", "rb")

    if uploaded:
        try:
            df_raw = load_excel(uploaded)
        except Exception as e:
            st.error(f"שגיאה בקריאת הקובץ: {e}")
            st.stop()

        st.write("תצוגה ראשונית של הנתונים (5 רשומות ראשונות):")
        st.dataframe(df_raw.head())

        st.markdown("---")
        st.markdown("### 2) מיפוי עמודות (חד פעמי לכל קובץ)")
        st.write("התאם בין שמות העמודות בקובץ לבין שדות סטנדרטיים במערכת.")

        mappings: dict[str, str] = {}
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
                st.markdown(f"**{label_he}**  \n*חובה*") if required else st.markdown(label_he)
            with d3:
                default_index = 0
                for i, col in enumerate(columns[1:], start=1):
                    if any(hint in str(col) for hint in c.get("examples", [])):
                        default_index = i
                        break
                mappings[key] = st.selectbox("", columns, index=default_index, key=f"map_{key}")

        missing_required = [
            c["label_he"]
            for c in SCHEMA["canonical_fields"]
            if c["required"] and mappings[c["key"]] == "(ללא)"
        ]
        if missing_required:
            st.error("חסרות עמודות חובה: " + ", ".join(missing_required))
            st.stop()

        df_norm = normalize_dataframe(df_raw, mappings)
        insert_dataframe(df_norm, conn)
        st.success("הנתונים נשמרו בבסיס הנתונים.")
        st.markdown("---")

# Load data for viewing
student_filter = user.get("student_name") if role == "תלמיד" else None
df_db = load_records(conn, student_filter)

if df_db.empty:
    st.info("אין נתונים להצגה.")
    st.stop()

df = compute_overall_score(df_db, weights)
df, trend_fields = compute_trends(df, list(weights.keys()))
df = apply_flags(df, low_percentile_thr, drop_thr, trend_fields)

st.markdown("### דשבורד כיתתי")
view_df = df.copy()
show_cols = [
    c
    for c in [
        "student_name",
        "class_name",
        "semester",
        "overall_score",
        "quiz_avg",
        "quarter_exam",
        "midterm_mock",
        "half_semester_final",
        "national_percentile",
        "flagged",
    ]
    if c in view_df.columns
]
st.dataframe(
    view_df[show_cols].sort_values(
        by=[c for c in ["flagged", "overall_score"] if c in show_cols],
        ascending=[False, False],
    )
)

filtered = view_df[view_df["flagged"]] if "flagged" in view_df.columns else view_df
csv = filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ הורד CSV מסונן (קריטריונים)",
    data=csv,
    file_name="filtered_students.csv",
    mime="text/csv",
)

st.markdown("---")
st.markdown("### פרופיל תלמיד")
if "student_name" in df.columns:
    if role == "תלמיד":
        student = user.get("student_name")
        st.write(f"תלמיד/ה: {student}")
    else:
        student = st.selectbox("בחר תלמיד/ה", sorted(df["student_name"].dropna().unique().tolist()))
    sdf = df[df["student_name"] == student].copy()
    st.write("רשומות תלמיד (לפי סמסטר/אירוע):")
    st.dataframe(sdf)

    if "semester" in sdf.columns:
        for metric in ["quiz_avg", "quarter_exam", "midterm_mock", "half_semester_final"]:
            if metric in sdf.columns:
                st.write(f"מדד: {CANON[metric]['label_he']}")
                try:
                    pivot_m = (
                        sdf.pivot_table(index="semester", values=metric, aggfunc="mean").reset_index()
                    )
                    pivot_m = pivot_m.sort_values("semester")
                    st.line_chart(pivot_m.set_index("semester"))
                except Exception as e:
                    st.info(f"לא ניתן להציג גרף ל-{metric}: {e}")

    if "teacher_comment" in sdf.columns:
        st.subheader("הערכת המור")
        st.write(" \n".join([str(x) for x in sdf["teacher_comment"].dropna().unique().tolist()]))
    if "coordinator_comment" in sdf.columns:
        st.subheader("הערכת הרכז")
        st.write(" \n".join([str(x) for x in sdf["coordinator_comment"].dropna().unique().tolist()]))
