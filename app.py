import streamlit as st
import pymysql
import pymysql.cursors
import random
import string
import base64
import time
from datetime import date, datetime
from io import BytesIO

# --- ReportLab Imports for PDF Generation ---
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Multi-Tenant Examination Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= DARK THEME & HIGH CONTRAST CUSTOM CSS =================
st.markdown("""
    <style>
    /* Global App Background */
    .stApp, .main {
        background-color: #0b0f19 !important;
        color: #f3f4f6 !important;
    }
    
    /* High Contrast Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #60a5fa !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700 !important;
    }

    /* Labels - High Contrast White */
    label, div[data-testid="stMarkdownContainer"] p {
        color: #f9fafb !important;
        font-weight: 600 !important;
    }
    
    /* Inputs, Selectboxes, Date Inputs - High Contrast Borders & BG */
    .stTextInput input, 
    .stSelectbox div[data-baseweb="select"] > div, 
    .stDateInput input {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 2px solid #4b5563 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }

    .stTextInput input:focus, 
    .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    
    /* Textarea Styling */
    div[data-baseweb="textarea"],
    div[data-baseweb="textarea"] > textarea,
    .stTextArea textarea {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 2px solid #4b5563 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 700;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        transition: all 0.3s ease;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    
    /* Containers & Banners */
    .banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #2563eb;
    }
    .cred-box {
        background-color: #1f2937;
        border-left: 6px solid #38bdf8;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
        color: #f9fafb;
    }
    .timer-box {
        background-color: #7f1d1d;
        color: #fef2f2;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        border: 1px solid #ef4444;
        margin-bottom: 15px;
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #030712;
        color: #9ca3af;
        text-align: center;
        padding: 8px 0;
        font-size: 0.9rem;
        border-top: 1px solid #1f2937;
        z-index: 9999;
    }
    .footer a {
        color: #38bdf8 !important;
        text-decoration: none;
        font-weight: bold;
    }
    .main .block-container {
        padding-bottom: 60px;
    }
    </style>
""", unsafe_allow_html=True)

# ================= DB CONFIGURATION =================
DB_CONFIG = {
    'host': 'sql12.freesqldatabase.com',
    'user': 'sql12835523',
    'password': 'iWsuYeRXjL',
    'database': 'sql12835523',
    'port': 3306
}

CLASSES = ['Class V', 'Class VI', 'Class VII', 'Class VIII', 'Class IX', 'Class X', 'Class XI', 'Class XII']
SUPER_ADMIN_PASSWORD = "M@m0ni4thjune"

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

# ================= PDF GENERATOR (WITH TOTAL MARKS) =================
def generate_pdf_report(data_rows, title="Exam Result Sheet"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PDFTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=18, textColor=colors.HexColor("#1e3a8a"), spaceAfter=15, alignment=1
    )
    
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    
    if data_rows:
        headers = list(data_rows[0].keys())
        table_data = [[str(h).replace('_', ' ').title() for h in headers]]
        
        total_obtained_marks = 0
        total_max_marks = 0

        for row in data_rows:
            table_data.append([str(row[h]) if row[h] is not None else "" for h in headers])
            if 'score' in row and row['score'] is not None:
                total_obtained_marks += int(row['score'])
            if 'total_questions' in row and row['total_questions'] is not None:
                total_max_marks += int(row['total_questions'])
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t)
        
        # Summary Total Section
        elements.append(Spacer(1, 15))
        summary_style = ParagraphStyle(
            'PDFSummary', parent=styles['Normal'], fontName='Helvetica-Bold',
            fontSize=11, textColor=colors.HexColor("#0f172a"), spaceAfter=5
        )
        elements.append(Paragraph(f"<b>Total Score Obtained:</b> {total_obtained_marks} / {total_max_marks}", summary_style))
        if total_max_marks > 0:
            percentage = (total_obtained_marks / total_max_marks) * 100
            elements.append(Paragraph(f"<b>Overall Percentage:</b> {percentage:.2f}%", summary_style))
    else:
        elements.append(Paragraph("No records found.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ================= DB MIGRATION & SETUP =================
def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_name VARCHAR(100) NOT NULL,
                institute_name VARCHAR(150),
                teacher_code VARCHAR(30) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                approved_at DATETIME NULL
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NULL,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                school_name VARCHAR(150),
                class_name VARCHAR(20) NOT NULL,
                dob DATE,
                userid VARCHAR(50) UNIQUE,
                password VARCHAR(50),
                seat_for_exam VARCHAR(10) DEFAULT 'yes',
                status VARCHAR(20) DEFAULT 'pending',
                approved_at DATETIME NULL
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                class_name VARCHAR(20) NOT NULL,
                subject_name VARCHAR(100) NOT NULL
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                class_name VARCHAR(20) NOT NULL,
                subject_name VARCHAR(100) NOT NULL,
                chapter_name VARCHAR(100) NOT NULL
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                class_name VARCHAR(20),
                subject_name VARCHAR(100),
                chapter_name VARCHAR(100),
                question_text TEXT,
                image_path LONGTEXT,
                option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT,
                correct_option INT
            )""")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                student_id INT NOT NULL,
                class_name VARCHAR(20),
                roll_no VARCHAR(50),
                student_name VARCHAR(100),
                subject_name VARCHAR(100),
                chapter_name VARCHAR(100),
                score INT,
                total_questions INT,
                exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

        # Add approved_at columns if missing
        for tbl in ['teachers', 'students']:
            cursor.execute(f"SHOW COLUMNS FROM {tbl}")
            cols = [r['Field'] for r in cursor.fetchall()]
            if 'approved_at' not in cols:
                cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN approved_at DATETIME NULL")

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database Migration Error: {e}")

# 60-Day Validity Expiry Check
def check_60_days_validity():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Change status to pending if approved > 60 days ago
            cursor.execute("""
                UPDATE students 
                SET status = 'pending' 
                WHERE status = 'approved' AND approved_at IS NOT NULL 
                AND DATEDIFF(NOW(), approved_at) > 60
            """)
            cursor.execute("""
                UPDATE teachers 
                SET status = 'pending' 
                WHERE status = 'approved' AND approved_at IS NOT NULL 
                AND DATEDIFF(NOW(), approved_at) > 60
            """)
            conn.commit()
        conn.close()
    except Exception:
        pass

setup_database()
check_60_days_validity()

# Helpers
def generate_credentials(name):
    clean_name = "".join(e for e in name if e.isalnum()).lower()[:4]
    rand_num = random.randint(1000, 9999)
    userid = f"stu_{clean_name}{rand_num}"
    chars = string.ascii_letters + string.digits
    password = "".join(random.choice(chars) for _ in range(6))
    return userid, password

# Helper function to submit exam results
def submit_student_exam(q_list, info):
    score = sum(1 for idx, q in enumerate(q_list) if st.session_state.user_answers.get(idx) == q['correct'])
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = """INSERT INTO exam_results 
                 (teacher_id, student_id, class_name, roll_no, student_name, subject_name, chapter_name, score, total_questions)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (
            info['teacher_id'], info['id'], info['class'], info['roll'], info['name'], 
            info['sub'], info['chap'], score, len(q_list)
        ))
        conn.commit()
    conn.close()
    return score

# ================= SIDEBAR NAVIGATION =================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=90)
st.sidebar.title("Portal Navigation")
menu = st.sidebar.radio("Select Interface", [
    "📝 Student Portal", 
    "👨‍🏫 Teacher Portal", 
    "📊 View Student Results", 
    "👑 Super Admin Panel"
])

# ================= 1. STUDENT PORTAL =================
if menu == "📝 Student Portal":
    st.markdown("<div class='banner'><h2>📝 Student Examination Portal</h2></div>", unsafe_allow_html=True)
    student_tab = st.radio("Select Action", ["📋 New Student Registration", "🔑 Login & Start Exam"], horizontal=True)
    st.divider()

    if student_tab == "📋 New Student Registration":
        st.subheader("👤 Registration for Online Exams")
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, teacher_name, institute_name, teacher_code FROM teachers WHERE status='approved'")
            approved_teachers = cursor.fetchall()
        conn.close()

        teacher_map = {"🏛️ System Administrator (Assign Teacher Later)": None}
        for t in approved_teachers:
            label = f"{t['teacher_name']} ({t['institute_name'] or 'Private Batch'}) - Code: {t['teacher_code']}"
            teacher_map[label] = t['id']

        with st.form("stu_reg_form"):
            selected_t_str = st.selectbox(
                "Select Administrator / Teacher *", 
                list(teacher_map.keys()), 
                help="আপনি যদি আপনার শিক্ষককে তালিকায় না পান, 'System Administrator' বেছে নিন।"
            )
            col1, col2 = st.columns(2)
            with col1:
                reg_name = st.text_input("Full Name *")
                reg_school = st.text_input("School Name *")
                reg_class = st.selectbox("Class *", CLASSES)
            with col2:
                reg_dob = st.date_input("Date of Birth *", min_value=date(1990, 1, 1), max_value=date.today())
                reg_address = st.text_area("Address *")
                
            submit_reg = st.form_submit_button("Submit Application", type="primary", use_container_width=True)

        if submit_reg:
            if not (reg_name and reg_school and reg_address):
                st.warning("⚠️ সমস্ত প্রয়োজনীয় বিবরণ পূরণ করুন! / PLEASE FILL ALL INFORMATION")
            else:
                teacher_id = teacher_map[selected_t_str]
                userid, password = generate_credentials(reg_name)
                
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        sql = """INSERT INTO students 
                                 (teacher_id, name, address, school_name, class_name, dob, userid, password, seat_for_exam, status)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'yes', 'pending')"""
                        cursor.execute(sql, (teacher_id, reg_name, reg_address, reg_school, reg_class, reg_dob, userid, password))
                        conn.commit()
                    conn.close()
                    
                    st.success("🎉 রেজিস্ট্রেশন আবেদন জমা হয়েছে!")
                    st.markdown(f"""
                        <div class='cred-box'>
                            <h4>📌 আপনার পরীক্ষার লগইন ক্রিডেনশিয়াল:</h4>
                            <p><b>User ID:</b> <code>{userid}</code></p>
                            <p><b>Password:</b> <code>{password}</code></p>
                            <p><b>Assigned Teacher ID:</b> <code>{teacher_id if teacher_id else 'Pending Administrator Assignment'}</code></p>
                            <small>⚠️ বিবরণটি লিখে রাখুন। অ্যাকাউন্ট 60 দিনের জন্য অনুমোদিত হবে। Approval পেতে মেইল করুন: bhattacharyap72@gmail.com</small>
                        </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    elif student_tab == "🔑 Login & Start Exam":
        if "exam_started" not in st.session_state:
            st.session_state.exam_started = False

        if not st.session_state.exam_started:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔑 Candidate Authentication")
                login_uid = st.text_input("User ID")
                login_pwd = st.text_input("Password", type="password")

            if st.button("Verify & Login", type="primary"):
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM students WHERE userid=%s AND password=%s", (login_uid, login_pwd))
                    student = cursor.fetchone()
                conn.close()

                if not student:
                    st.error("❌ ভুল User ID বা Password!")
                elif student['status'] != 'approved':
                    st.warning("⏳ আপনার অ্যাকাউন্টটি অনুমোদিত (Approve) নেই অথবা 60 দিন অতিক্রান্ত হওয়ার পর মেয়ার উত্তীর্ণ হয়েছে। অনুগ্রহ করে অ্যাডমিনের সাথে যোগাযোগ করুন।")
                elif not student['teacher_id']:
                    st.warning("⚠️ আপনাকে এখনো কোনো শিক্ষক বরাদ্দ করা হয়নি!")
                elif student['seat_for_exam'].lower() == 'no':
                    st.error("🚫 আপনার পরীক্ষা দেওয়ার অনুমতি স্থগিত (Disabled) রয়েছে।")
                else:
                    st.session_state.logged_student = student
                    st.session_state.exam_ready = True
                    st.success(f"স্বাগতম, {student['name']}!")

            if st.session_state.get("exam_ready", False):
                st.divider()
                st.subheader("📚 Select Exam Options")
                stu = st.session_state.logged_student
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"**Candidate:** {stu['name']} | **Class:** {stu['class_name']} | **Teacher ID:** {stu['teacher_id']}")
                    
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s AND teacher_id=%s", (stu['class_name'], stu['teacher_id']))
                        subjects = [r['subject_name'] for r in cursor.fetchall()]
                    conn.close()

                    stu_sub = st.selectbox("Select Subject", subjects if subjects else ["No Subjects Found"])

                with col_b:
                    chapters = []
                    if subjects:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s AND teacher_id=%s", (stu['class_name'], stu_sub, stu['teacher_id']))
                            chapters = [r['chapter_name'] for r in cursor.fetchall()]
                        conn.close()
                    
                    stu_chap = st.selectbox("Select Chapter", ["All Chapters (Combined)"] + chapters)

                if st.button("🚀 Start Exam Now (Duration: 40 Minutes - Max 40 Questions)", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        if stu_chap == "All Chapters (Combined)":
                            cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s AND teacher_id=%s ORDER BY RAND() LIMIT 40", (stu['class_name'], stu_sub, stu['teacher_id']))
                        else:
                            cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s AND chapter_name=%s AND teacher_id=%s ORDER BY RAND() LIMIT 40", (stu['class_name'], stu_sub, stu_chap, stu['teacher_id']))
                        raw_q = cursor.fetchall()
                    conn.close()

                    if not raw_q:
                        st.error("❌ এই বিষয়ে শিক্ষক কোনো প্রশ্ন যুক্ত করেননি!")
                    else:
                        # নিশ্চিত করা হচ্ছে যে সর্বোচ্চ ৪০টি প্রশ্নই র‍্যান্ডম হিসেবে আসবে, বেশি নয়
                        if len(raw_q) > 40:
                            raw_q = random.sample(raw_q, 40)
                        else:
                            random.shuffle(raw_q)

                        prepared_q = []
                        for q in raw_q:
                            opts = [q['option1'], q['option2'], q['option3'], q['option4']]
                            correct_txt = opts[q['correct_option'] - 1]
                            random.shuffle(opts)
                            prepared_q.append({
                                'id': q['id'], 'text': q['question_text'], 'image': q.get('image_path'),
                                'options': opts, 'correct': opts.index(correct_txt) + 1
                            })
                        
                        st.session_state.prepared_questions = prepared_q
                        st.session_state.student_info = {
                            'id': stu['id'], 'teacher_id': stu['teacher_id'], 'class': stu['class_name'], 
                            'roll': stu['userid'], 'name': stu['name'], 'sub': stu_sub, 'chap': stu_chap
                        }
                        st.session_state.user_answers = {}
                        st.session_state.exam_start_time = time.time()
                        st.session_state.exam_started = True
                        st.rerun()

        else:
            # 40-MINUTE TIMER & EXAM INTERFACE (MAX 40 QUESTIONS)
            info = st.session_state.student_info
            q_list = st.session_state.prepared_questions
            
            elapsed_time = time.time() - st.session_state.exam_start_time
            total_duration = 40 * 60  # 40 Minutes in seconds
            remaining_time = total_duration - elapsed_time

            if remaining_time <= 0:
                st.warning("⏰ 40 মিনিট সময় শেষ! আপনার উত্তরসমূহ স্বয়ংক্রিয়ভাবে জমা হচ্ছে...")
                score = submit_student_exam(q_list, info)
                st.session_state.exam_started = False
                st.session_state.exam_ready = False
                st.success(f"🎉 সময় সমাপ্তির কারণে উত্তর জমা নেওয়া হয়েছে। আপনার অর্জন: **{score} / {len(q_list)}**")
            else:
                mins, secs = divmod(int(remaining_time), 60)
                st.markdown(f"<div class='timer-box'>⏳ অবশিষ্ট সময়: {mins:02d} minute(s) {secs:02d} second(s) (40 Mins Limit)</div>", unsafe_allow_html=True)
                st.info(f"👤 **Student:** {info['name']} | **User ID:** {info['roll']} | **Subject:** {info['sub']} | **Total Questions:** {len(q_list)}")
                
                with st.form("exam_form"):
                    for idx, q in enumerate(q_list):
                        st.markdown(f"#### Q{idx+1}. {q['text']}")
                        if q['image']:
                            try:
                                st.image(q['image'], width=300)
                            except: pass
                        choice = st.radio(f"Select Option Q{idx+1}:", q['options'], index=None, key=f"q_{idx}")
                        if choice:
                            st.session_state.user_answers[idx] = q['options'].index(choice) + 1
                        st.divider()

                    submitted = st.form_submit_button("📤 Submit Final Exam", type="primary", use_container_width=True)

                if submitted:
                    score = submit_student_exam(q_list, info)
                    st.balloons()
                    st.success(f"🎉 পরীক্ষা সফলভাবে জমা হয়েছে! আপনার স্কোর: **{score} / {len(q_list)}**")
                    st.session_state.exam_started = False
                    st.session_state.exam_ready = False

# ================= 2. TEACHER PORTAL =================
elif menu == "👨‍🏫 Teacher Portal":
    st.markdown("<div class='banner'><h2>👨‍🏫 Teacher Management Dashboard</h2></div>", unsafe_allow_html=True)
    
    if "logged_teacher" not in st.session_state:
        st.session_state.logged_teacher = None

    if not st.session_state.logged_teacher:
        t_action = st.radio("Teacher Authorization", ["🔐 Teacher Login", "📝 New Teacher Signup"], horizontal=True)
        st.divider()

        if t_action == "📝 New Teacher Signup":
            st.subheader("👨‍🏫 Teacher Account Registration")
            with st.form("t_signup"):
                t_name = st.text_input("Full Name *")
                t_inst = st.text_input("Institute / Coaching Name")
                t_email = st.text_input("Email Address *")
                t_code = st.text_input("Create Custom Teacher Code (e.g. MATH_HUB) *")
                t_pwd = st.text_input("Password *", type="password")
                submit_t = st.form_submit_button("Register Teacher Account", type="primary")

            if submit_t:
                if not (t_name and t_email and t_code and t_pwd):
                    st.warning("⚠️ সমস্ত প্রয়োজনীয় বিবরণ প্রদান করুন!")
                else:
                    try:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            sql = "INSERT INTO teachers (teacher_name, institute_name, teacher_code, email, password, status) VALUES (%s, %s, %s, %s, %s, 'pending')"
                            cursor.execute(sql, (t_name, t_inst, t_code, t_email, t_pwd))
                            conn.commit()
                        conn.close()
                        st.success("🎉 রেজিস্ট্রেশন সম্পন্ন হয়েছে! অ্যাডমিন অনুমোদন করার পর আপনি 60 দিনের জন্য অ্যাক্সেস পাবেন।")
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif t_action == "🔐 Teacher Login":
            st.subheader("🔐 Teacher Login")
            col1, col2 = st.columns(2)
            with col1:
                t_login_id = st.text_input("Email or Teacher Code")
                t_login_pwd = st.text_input("Password", type="password")
            
            if st.button("Login to Dashboard", type="primary"):
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM teachers WHERE (email=%s OR teacher_code=%s) AND password=%s", (t_login_id, t_login_id, t_login_pwd))
                    teacher = cursor.fetchone()
                conn.close()

                if not teacher:
                    st.error("❌ ভুল লগইন তথ্য!")
                elif teacher['status'] != 'approved':
                    st.warning("⏳ আপনার শিক্ষক অ্যাকাউন্টটি অনুমোদিত নয় অথবা 60 দিনের মেয়াদ শেষ হয়ে গেছে। অ্যাডমিনের অনুমতি প্রয়োজন।")
                else:
                    st.session_state.logged_teacher = teacher
                    st.success(f"স্বাগতম, {teacher['teacher_name']} স্যার!")
                    st.rerun()

    else:
        teacher = st.session_state.logged_teacher
        st.sidebar.markdown(f"**👨‍🏫 Logged Teacher:**\n{teacher['teacher_name']}\nID: `{teacher['id']}` | Code: `{teacher['teacher_code']}`")
        if st.sidebar.button("🚪 Teacher Logout"):
            st.session_state.logged_teacher = None
            st.rerun()

        t_tab1, t_tab2, t_tab3, t_tab4 = st.tabs([
            "👥 Student Credentials & Management", 
            "📚 Subjects & Chapters", 
            "➕ Question Bank & Edit", 
            "📊 Results & PDF Reports"
        ])

        with t_tab1:
            st.subheader("📋 Registered Students List")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, teacher_id, name, class_name, school_name, userid, password, status, seat_for_exam, approved_at 
                    FROM students WHERE teacher_id=%s""", (teacher['id'],))
                stu_list = cursor.fetchall()
            conn.close()

            if stu_list:
                st.dataframe(stu_list, use_container_width=True)
                st.divider()
                col_x, col_y = st.columns(2)
                with col_x:
                    st.markdown("#### Approve / Reject Student (60 Days Renewal)")
                    p_dict = {f"{s['name']} (Class: {s['class_name']} | ID: {s['userid']}) - [{s['status']}]": s['id'] for s in stu_list}
                    sel_p = st.selectbox("Select Student", list(p_dict.keys()))
                    act_p = st.radio("Set Status (Approved valid for 60 Days):", ["approved", "rejected", "pending"], horizontal=True)
                    if st.button("Update Registration Status"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            app_date = datetime.now() if act_p == 'approved' else None
                            cursor.execute("UPDATE students SET status=%s, approved_at=%s WHERE id=%s", (act_p, app_date, p_dict[sel_p]))
                            conn.commit()
                        conn.close()
                        st.success("✅ স্ট্যাটাস ও মেয়াদ আপডেট করা হয়েছে!")
                        st.rerun()

                with col_y:
                    st.markdown("#### Exam Access Control (`seat_for_exam`)")
                    app_stus = [s for s in stu_list if s['status'] == 'approved']
                    if app_stus:
                        a_dict = {f"{s['name']} (ID: {s['userid']}) - Access: {s['seat_for_exam']}": s['id'] for s in app_stus}
                        sel_a = st.selectbox("Select Approved Student", list(a_dict.keys()))
                        act_a = st.radio("Exam Access Permission:", ["yes", "no"], horizontal=True)
                        if st.button("Update Exam Permission"):
                            conn = get_db_connection()
                            with conn.cursor() as cursor:
                                cursor.execute("UPDATE students SET seat_for_exam=%s WHERE id=%s", (act_a, a_dict[sel_a]))
                                conn.commit()
                            conn.close()
                            st.success("✅ অ্যাক্সেস আপডেট করা হয়েছে!")
                            st.rerun()

                st.divider()
                st.markdown("#### 🗑️ Delete Student Account")
                del_s_map = {f"{s['name']} (Class: {s['class_name']} | ID: {s['userid']})": s['id'] for s in stu_list}
                sel_del_s = st.selectbox("Select Student to Delete", list(del_s_map.keys()), key="t_del_stu_select")
                if st.button("🗑️ Delete Student Permanently", type="primary"):
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM students WHERE id=%s AND teacher_id=%s", (del_s_map[sel_del_s], teacher['id']))
                        conn.commit()
                    conn.close()
                    st.success("🗑️ ছাত্রের তথ্য ডিলিট করা হয়েছে!")
                    st.rerun()
            else:
                st.info("আপনার অধীনে কোনো ছাত্র নিবন্ধিত নেই।")

        with t_tab2:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Add Subject")
                s_cls = st.selectbox("Class", CLASSES, key="ts_cls")
                s_name = st.text_input("Subject Name")
                if st.button("Save Subject"):
                    if s_name:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("INSERT INTO subjects (teacher_id, class_name, subject_name) VALUES (%s, %s, %s)", (teacher['id'], s_cls, s_name))
                            conn.commit()
                        conn.close()
                        st.success("✅ সাবজেক্ট সেভ হয়েছে!")

            with col_b:
                st.subheader("Add Chapter")
                c_cls = st.selectbox("Class", CLASSES, key="tc_cls")
                
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s AND teacher_id=%s", (c_cls, teacher['id']))
                    subs = [r['subject_name'] for r in cursor.fetchall()]
                conn.close()

                c_sub = st.selectbox("Subject", subs if subs else ["None"])
                c_name = st.text_input("Chapter Name")
                if st.button("Save Chapter"):
                    if c_name and c_sub != "None":
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("INSERT INTO chapters (teacher_id, class_name, subject_name, chapter_name) VALUES (%s, %s, %s, %s)", (teacher['id'], c_cls, c_sub, c_name))
                            conn.commit()
                        conn.close()
                        st.success("✅ চ্যাপ্টার সেভ হয়েছে!")

        # TAB 3: QUESTION BANK & EDIT QUESTION
        with t_tab3:
            q_mode = st.radio("Question Action", ["➕ Add New Question", "✏️ View & Edit My Questions", "🗑️ Delete Question"], horizontal=True)
            st.divider()

            if q_mode == "➕ Add New Question":
                q_cls = st.selectbox("Class", CLASSES, key="tq_cls")
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s AND teacher_id=%s", (q_cls, teacher['id']))
                    q_subs = [r['subject_name'] for r in cursor.fetchall()]
                conn.close()

                q_sub = st.selectbox("Subject", q_subs if q_subs else ["None"], key="tq_sub")
                
                q_chaps = []
                if q_subs:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s AND teacher_id=%s", (q_cls, q_sub, teacher['id']))
                        q_chaps = [r['chapter_name'] for r in cursor.fetchall()]
                    conn.close()

                q_chap = st.selectbox("Chapter", q_chaps if q_chaps else ["None"], key="tq_chap")
                q_text = st.text_area("Question Text")
                
                q_img_file = st.file_uploader("Upload Image Diagram (Optional)", type=['png', 'jpg', 'jpeg'])
                img_url = None
                if q_img_file:
                    bytes_data = q_img_file.getvalue()
                    base64_str = base64.b64encode(bytes_data).decode('utf-8')
                    img_url = f"data:image/png;base64,{base64_str}"

                col1, col2 = st.columns(2)
                with col1:
                    opt_corr = st.text_input("✅ Correct Option")
                    opt_w1 = st.text_input("❌ Option 2")
                with col2:
                    opt_w2 = st.text_input("❌ Option 3")
                    opt_w3 = st.text_input("❌ Option 4")

                if st.button("Save Question to Bank", type="primary"):
                    if q_text and opt_corr and opt_w1 and opt_w2 and opt_w3 and q_chap != "None":
                        opts = [opt_corr, opt_w1, opt_w2, opt_w3]
                        random.shuffle(opts)
                        corr_idx = opts.index(opt_corr) + 1

                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            sql = """INSERT INTO questions 
                                     (teacher_id, class_name, subject_name, chapter_name, question_text, image_path, option1, option2, option3, option4, correct_option)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                            cursor.execute(sql, (teacher['id'], q_cls, q_sub, q_chap, q_text, img_url, opts[0], opts[1], opts[2], opts[3], corr_idx))
                            conn.commit()
                        conn.close()
                        st.success("✅ প্রশ্ন সেভ করা হয়েছে!")

            elif q_mode == "✏️ View & Edit My Questions":
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM questions WHERE teacher_id=%s ORDER BY id DESC", (teacher['id'],))
                    my_questions = cursor.fetchall()
                conn.close()

                if my_questions:
                    q_dict = {f"ID {q['id']} | [{q['class_name']} - {q['subject_name']}] : {q['question_text'][:50]}...": q for q in my_questions}
                    sel_q_key = st.selectbox("Select Question to Edit", list(q_dict.keys()))
                    selected_q = q_dict[sel_q_key]

                    with st.form("edit_q_form"):
                        st.subheader(f"Edit Question ID: {selected_q['id']}")
                        e_text = st.text_area("Question Text", value=selected_q['question_text'])
                        e_opt1 = st.text_input("Option 1", value=selected_q['option1'])
                        e_opt2 = st.text_input("Option 2", value=selected_q['option2'])
                        e_opt3 = st.text_input("Option 3", value=selected_q['option3'])
                        e_opt4 = st.text_input("Option 4", value=selected_q['option4'])
                        e_corr = st.selectbox("Correct Option Number (1-4)", [1, 2, 3, 4], index=int(selected_q['correct_option'])-1)

                        if st.form_submit_button("Update Question", type="primary"):
                            conn = get_db_connection()
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE questions 
                                    SET question_text=%s, option1=%s, option2=%s, option3=%s, option4=%s, correct_option=%s 
                                    WHERE id=%s AND teacher_id=%s
                                """, (e_text, e_opt1, e_opt2, e_opt3, e_opt4, e_corr, selected_q['id'], teacher['id']))
                                conn.commit()
                            conn.close()
                            st.success("✅ প্রশ্ন সফলভাবে আপডেট হয়েছে!")
                            st.rerun()
                else:
                    st.info("আপনার তৈরি কোনো প্রশ্ন পাওয়া যায়নি।")

            elif q_mode == "🗑️ Delete Question":
                del_cls = st.selectbox("Select Class", CLASSES, key="tdel_cls")
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, question_text FROM questions WHERE class_name=%s AND teacher_id=%s", (del_cls, teacher['id']))
                    del_q = cursor.fetchall()
                conn.close()

                if del_q:
                    q_dict = {f"ID: {q['id']} - {q['question_text'][:50]}...": q['id'] for q in del_q}
                    sel_q = st.selectbox("Select Question to Delete", list(q_dict.keys()))
                    if st.button("🗑️ Delete Selected Question", type="primary"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM questions WHERE id=%s", (q_dict[sel_q],))
                            conn.commit()
                        conn.close()
                        st.success("🗑️ প্রশ্ন মুছে ফেলা হয়েছে!")
                        st.rerun()

        with t_tab4:
            st.subheader("📊 Exam Performance & PDF Reports")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                    FROM exam_results WHERE teacher_id=%s ORDER BY exam_date DESC""", (teacher['id'],))
                t_results = cursor.fetchall()
            conn.close()

            if t_results:
                st.dataframe(t_results, use_container_width=True)
                pdf_bytes = generate_pdf_report(t_results, title=f"Exam Results - {teacher['teacher_name']}")
                st.download_button(
                    label="📥 Download Teacher Batch Result Sheet (PDF with Total)",
                    data=pdf_bytes,
                    file_name=f"Results_{teacher['teacher_code']}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.info("কোনো রেজাল্ট পাওয়া যায়নি।")

# ================= 3. VIEW RESULTS =================
elif menu == "📊 View Student Results":
    st.markdown("<div class='banner'><h2>📊 Individual Result Search</h2></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        search_cls = st.selectbox("Class", CLASSES)
    with col2:
        search_uid = st.text_input("Enter Student User ID")

    if st.button("🔍 Search Performance Record", use_container_width=True):
        if search_uid:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                    FROM exam_results WHERE class_name=%s AND roll_no=%s""", (search_cls, search_uid))
                rows = cursor.fetchall()
            conn.close()

            if rows:
                st.dataframe(rows, use_container_width=True)
                pdf_data = generate_pdf_report(rows, title=f"Result Sheet - {rows[0]['student_name']} ({search_uid})")
                st.download_button("📄 Download Individual PDF Result (With Total Marks)", data=pdf_data, file_name=f"Result_{search_uid}.pdf", mime="application/pdf")
            else:
                st.warning("❌ কোনো ফলাফল পাওয়া যায়নি!")

# ================= 4. SUPER ADMIN PANEL =================
elif menu == "👑 Super Admin Panel":
    st.markdown("<div class='banner'><h2>👑 Super Administrative Control</h2></div>", unsafe_allow_html=True)
    
    sa_pwd = st.text_input("🔐 Enter Super Admin Passcode", type="password")
    
    if sa_pwd == SUPER_ADMIN_PASSWORD:
        st.success("🔑 Admin Access Granted")
        
        admin_tab1, admin_tab2, admin_tab3 = st.tabs([
            "👨‍🏫 Teachers Master Control", 
            "🎓 All Students Master List", 
            "📝 All Questions Master Control & Edit"
        ])

        with admin_tab1:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, teacher_name, institute_name, teacher_code, email, password, status, approved_at FROM teachers")
                all_teachers = cursor.fetchall()
            conn.close()

            st.subheader("👨‍🏫 Registered Teachers Master List")
            if all_teachers:
                st.dataframe(all_teachers, use_container_width=True)
                st.divider()
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    st.subheader("🛡️ Approve / Block Teachers (60 Days Renewal)")
                    t_map = {f"ID: {t['id']} | {t['teacher_name']} ({t['email']}) - Status: {t['status']}": t['id'] for t in all_teachers}
                    sel_t = st.selectbox("Select Teacher Account", list(t_map.keys()))
                    new_t_status = st.radio("Account Permission:", ["approved", "blocked", "pending"], horizontal=True)

                    if st.button("Update Teacher Authorization", type="primary"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            app_date = datetime.now() if new_t_status == 'approved' else None
                            cursor.execute("UPDATE teachers SET status=%s, approved_at=%s WHERE id=%s", (new_t_status, app_date, t_map[sel_t]))
                            conn.commit()
                        conn.close()
                        st.success("✅ টিচারের স্ট্যাটাস ও মেয়াদ (60 Days) আপডেট করা হয়েছে!")
                        st.rerun()

                with col_t2:
                    st.subheader("🗑️ Delete Teacher Account")
                    del_t_map = {f"ID: {t['id']} | {t['teacher_name']} ({t['teacher_code']})": t['id'] for t in all_teachers}
                    sel_del_t = st.selectbox("Select Teacher to Delete", list(del_t_map.keys()), key="admin_del_t_select")
                    if st.button("🗑️ Delete Teacher Permanently", type="primary"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM teachers WHERE id=%s", (del_t_map[sel_del_t],))
                            conn.commit()
                        conn.close()
                        st.success("🗑️ টিচার মুছে ফেলা হয়েছে!")
                        st.rerun()

        with admin_tab2:
            st.subheader("🎓 All Registered Students Master List")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id AS student_id, s.teacher_id, t.teacher_name AS assigned_administrator,
                        s.name AS student_name, s.class_name, s.school_name, s.userid AS username,
                        s.password, s.status, s.seat_for_exam, s.approved_at
                    FROM students s
                    LEFT JOIN teachers t ON s.teacher_id = t.id
                    ORDER BY s.id DESC
                """)
                all_students = cursor.fetchall()
                
                cursor.execute("SELECT id, teacher_name, teacher_code, institute_name FROM teachers WHERE status='approved'")
                approved_teachers_list = cursor.fetchall()
            conn.close()

            if all_students:
                st.dataframe(all_students, use_container_width=True)
                st.divider()
                col_m1, col_m2 = st.columns(2)

                with col_m1:
                    st.subheader("🔄 Assign Teacher & Approve (60 Days)")
                    if approved_teachers_list:
                        s_assign_map = {f"ID: {s['student_id']} | {s['student_name']} (User: {s['username']})": s['student_id'] for s in all_students}
                        t_assign_map = {f"{t['teacher_name']} ({t['institute_name'] or 'Batch'}) - Code: {t['teacher_code']}": t['id'] for t in approved_teachers_list}

                        sel_s_for_t = st.selectbox("1. Select Student", list(s_assign_map.keys()))
                        sel_t_for_s = st.selectbox("2. Select Teacher to Assign", list(t_assign_map.keys()))

                        if st.button("Assign Teacher & Approve", type="primary"):
                            conn = get_db_connection()
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE students SET teacher_id=%s, status='approved', approved_at=%s WHERE id=%s", 
                                    (t_assign_map[sel_t_for_s], datetime.now(), s_assign_map[sel_s_for_t])
                                )
                                conn.commit()
                            conn.close()
                            st.success("✅ শিক্ষক বরাদ্দ এবং 60 দিনের মেয়াদে Approve করা হয়েছে!")
                            st.rerun()

                with col_m2:
                    st.subheader("🛡️ Global Student Status Update")
                    s_map = {f"Student ID: {s['student_id']} | {s['student_name']}": s['student_id'] for s in all_students}
                    sel_s = st.selectbox("Select Student Account", list(s_map.keys()))
                    new_s_status = st.radio("Student Registration Status:", ["approved", "rejected", "pending"], horizontal=True, key="admin_stu_status")
                    
                    if st.button("Update Student Status", type="primary"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            app_date = datetime.now() if new_s_status == 'approved' else None
                            cursor.execute("UPDATE students SET status=%s, approved_at=%s WHERE id=%s", (new_s_status, app_date, s_map[sel_s]))
                            conn.commit()
                        conn.close()
                        st.success("✅ ছাত্রের স্ট্যাটাস আপডেট করা হয়েছে!")
                        st.rerun()

                st.divider()
                st.subheader("🗑️ Delete Student Account (Global)")
                del_admin_s_map = {f"Student ID: {s['student_id']} | {s['student_name']}": s['student_id'] for s in all_students}
                sel_del_admin_s = st.selectbox("Select Student to Delete", list(del_admin_s_map.keys()), key="admin_del_stu_select")
                if st.button("🗑️ Delete Student Permanently", type="primary"):
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM students WHERE id=%s", (del_admin_s_map[sel_del_admin_s],))
                        conn.commit()
                    conn.close()
                    st.success("🗑️ অ্যাকাউন্ট মুছে ফেলা হয়েছে!")
                    st.rerun()

        # TAB 3: ADMIN ALL QUESTIONS MASTER VIEW & EDIT
        with admin_tab3:
            st.subheader("📝 Master Question Bank (View & Edit All Questions)")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT q.*, t.teacher_name 
                    FROM questions q 
                    LEFT JOIN teachers t ON q.teacher_id = t.id 
                    ORDER BY q.id DESC
                """)
                admin_all_q = cursor.fetchall()
            conn.close()

            if admin_all_q:
                st.dataframe(admin_all_q, use_container_width=True)
                st.divider()
                
                q_admin_dict = {f"Q-ID {q['id']} [Teacher: {q['teacher_name'] or 'Admin'}] [{q['class_name']}-{q['subject_name']}] : {q['question_text'][:50]}...": q for q in admin_all_q}
                sel_admin_q_key = st.selectbox("Select Any Question to Edit / Modify", list(q_admin_dict.keys()))
                selected_admin_q = q_admin_dict[sel_admin_q_key]

                with st.form("admin_edit_q_form"):
                    st.subheader(f"Admin Edit Question ID: {selected_admin_q['id']}")
                    a_q_text = st.text_area("Question Text", value=selected_admin_q['question_text'])
                    a_opt1 = st.text_input("Option 1", value=selected_admin_q['option1'])
                    a_opt2 = st.text_input("Option 2", value=selected_admin_q['option2'])
                    a_opt3 = st.text_input("Option 3", value=selected_admin_q['option3'])
                    a_opt4 = st.text_input("Option 4", value=selected_admin_q['option4'])
                    a_corr = st.selectbox("Correct Option Number (1-4)", [1, 2, 3, 4], index=int(selected_admin_q['correct_option'])-1)

                    if st.form_submit_button("Update Question (Admin Overwrite)", type="primary"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE questions 
                                SET question_text=%s, option1=%s, option2=%s, option3=%s, option4=%s, correct_option=%s 
                                WHERE id=%s
                            """, (a_q_text, a_opt1, a_opt2, a_opt3, a_opt4, a_corr, selected_admin_q['id']))
                            conn.commit()
                        conn.close()
                        st.success("✅ প্রশ্ন সফলভাবে আপডেট করা হয়েছে!")
                        st.rerun()
            else:
                st.info("কোনো প্রশ্ন যুক্ত করা নেই।")

# ================= MAIN WINDOW FOOTER =================
st.markdown("""
    <div class="footer">
        Created by <b>PARTHA PRATIM BHATTACHARYA</b> | Email: <a href="mailto:bhattacharyap72@gmail.com">bhattacharyap72@gmail.com</a>
    </div>
""", unsafe_allow_html=True)
