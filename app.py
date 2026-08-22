import streamlit as st
import streamlit.components.v1 as components
import pymysql
import pymysql.cursors
import random
import string
import base64
import time
import urllib.request
import os
from datetime import date, datetime
from io import BytesIO

# --- ReportLab Imports for PDF Generation ---
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ================= BENGALI FONT SETUP FOR REPORTLAB =================
@st.cache_resource
def setup_bengali_font():
    font_path = "NotoSansBengali-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/notosansbengali/NotoSansBengali%5Bwdth%2Cwght%5D.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            pass
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('NotoBengali', font_path))
            return 'NotoBengali'
        except Exception:
            return 'Helvetica'
    return 'Helvetica'

PDF_FONT = setup_bengali_font()

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Multi-Tenant Examination Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
    <style>
    .stApp, .main {
        background-color: #0b0f19 !important;
        color: #f3f4f6 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #60a5fa !important;
        font-weight: bold !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #60a5fa !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700 !important;
    }
    label, div[data-testid="stMarkdownContainer"] p {
        color: #f9fafb !important;
        font-weight: 600 !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 2px solid #4b5563 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="textarea"] > textarea, .stTextArea textarea {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 2px solid #4b5563 !important;
        border-radius: 6px !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 700;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
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
    .footer {
        position: fixed;
        left: 0; bottom: 0; width: 100%;
        background-color: #030712;
        color: #9ca3af;
        text-align: center;
        padding: 8px 0;
        font-size: 0.9rem;
        border-top: 1px solid #1f2937;
        z-index: 9999;
    }
    .footer a { color: #38bdf8 !important; text-decoration: none; font-weight: bold; }
    .main .block-container { padding-bottom: 60px; }
    </style>
""", unsafe_allow_html=True)

# ================= DB CONFIGURATION =================
DB_CONFIG = {
    'host': 'sql12.freesqldatabase.com',
    'user': 'sql12835523',
    'password': 'iWsuYeRXjL',
    'database': 'sql12835523',
    'port': 3306,
    'charset': 'utf8mb4'
}

CLASSES = ['Class V', 'Class VI', 'Class VII', 'Class VIII', 'Class IX', 'Class X', 'Class XI', 'Class XII']
SUPER_ADMIN_PASSWORD = "M@m0ni4thjune"

@st.cache_resource
def get_db_connection():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    with conn.cursor() as cursor:
        cursor.execute("SET NAMES utf8mb4;")
        cursor.execute("SET CHARACTER SET utf8mb4;")
        cursor.execute("SET character_set_connection=utf8mb4;")
    return conn

# ================= REAL-TIME TIMER =================
def render_digital_timer(seconds_left):
    timer_html = f"""
    <div id="digital-timer-container" style="
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        color: #ffffff; padding: 12px 20px; border-radius: 10px;
        text-align: center; font-family: 'Courier New', Courier, monospace;
        font-size: 1.5rem; font-weight: bold; border: 2px solid #ef4444; margin-bottom: 15px;">
        ⏱️ TIME REMAINING: <span id="timer-display" style="color: #fde047;">--:--</span>
    </div>
    <script>
        var totalSeconds = {int(seconds_left)};
        function updateTimer() {{
            if (totalSeconds <= 0) {{
                document.getElementById("timer-display").innerHTML = "00:00 (TIME EXPIRED)";
                return;
            }}
            var mins = Math.floor(totalSeconds / 60);
            var secs = totalSeconds % 60;
            document.getElementById("timer-display").innerHTML = (mins < 10 ? "0" + mins : mins) + ":" + (secs < 10 ? "0" + secs : secs);
            totalSeconds--;
        }}
        updateTimer();
        setInterval(updateTimer, 1000);
    </script>
    """
    components.html(timer_html, height=75)

def process_uploaded_image(img_file):
    if img_file is not None:
        bytes_data = img_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode('utf-8')
        return f"data:{img_file.type};base64,{base64_str}"
    return None

# ================= PDF GENERATOR =================
def generate_pdf_report(data_rows, title="Exam Result Sheet"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('PDFTitle', parent=styles['Heading1'], fontName=PDF_FONT, fontSize=18, textColor=colors.HexColor("#1e3a8a"), spaceAfter=15, alignment=1)
    cell_style = ParagraphStyle('PDFCell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, leading=12)
    header_style = ParagraphStyle('PDFHeader', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, textColor=colors.whitesmoke, leading=12)

    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    
    if data_rows:
        headers = list(data_rows[0].keys())
        table_data = [[Paragraph(str(h).replace('_', ' ').title(), header_style) for h in headers]]
        
        total_obtained = 0
        total_max = 0

        for row in data_rows:
            row_cells = [Paragraph(str(row[h]) if row[h] is not None else "", cell_style) for h in headers]
            table_data.append(row_cells)
            if 'score' in row and row['score'] is not None: total_obtained += int(row['score'])
            if 'total_questions' in row and row['total_questions'] is not None: total_max += int(row['total_questions'])
            
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))
        summary_style = ParagraphStyle('PDFSummary', parent=styles['Normal'], fontName=PDF_FONT, fontSize=11)
        elements.append(Paragraph(f"<b>Total Score Obtained:</b> {total_obtained} / {total_max}", summary_style))
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generate_student_detailed_pdf(info, q_list, user_answers):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('PDFTitle', parent=styles['Heading1'], fontName=PDF_FONT, fontSize=18, textColor=colors.HexColor("#1e3a8a"), spaceAfter=15, alignment=1)
    cell_style = ParagraphStyle('PDFCell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=8, leading=11)
    header_style = ParagraphStyle('PDFHeader', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, textColor=colors.whitesmoke, leading=12)
    info_style = ParagraphStyle('PDFInfo', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, textColor=colors.HexColor("#0f172a"), leading=12)

    elements.append(Paragraph("Student Examination Answer Sheet", title_style))
    elements.append(Spacer(1, 5))
    
    header_data = [
        [Paragraph(f"<b>Student Name:</b> {info['name']}", info_style), Paragraph(f"<b>User ID:</b> {info['roll']}", info_style)],
        [Paragraph(f"<b>Class:</b> {info['class']}", info_style), Paragraph(f"<b>Subject:</b> {info['sub']}", info_style)],
        [Paragraph(f"<b>Chapter:</b> {info['chap']}", info_style), Paragraph(f"<b>Exam Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style)]
    ]
    header_table = Table(header_data, colWidths=[260, 260])
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    table_data = [[
        Paragraph("<b>Q#</b>", header_style), 
        Paragraph("<b>Question</b>", header_style), 
        Paragraph("<b>Your Answer</b>", header_style), 
        Paragraph("<b>Correct Answer</b>", header_style), 
        Paragraph("<b>Result</b>", header_style)
    ]]
    score = 0
    
    for idx, q in enumerate(q_list):
        u_ans_idx = user_answers.get(idx)
        u_ans_txt = q['options'][u_ans_idx - 1] if u_ans_idx else "Not Answered"
        c_ans_txt = q['options'][q['correct'] - 1]
        
        is_correct = (u_ans_idx == q['correct'])
        if is_correct:
            score += 1
            res_txt = "<font color='green'><b>Correct</b></font>"
        else:
            res_txt = "<font color='red'><b>Incorrect</b></font>"
            
        p_q = Paragraph(str(q['text']), cell_style)
        p_u = Paragraph(str(u_ans_txt), cell_style)
        p_c = Paragraph(str(c_ans_txt), cell_style)
        p_r = Paragraph(res_txt, cell_style)
        
        table_data.append([Paragraph(str(idx + 1), cell_style), p_q, p_u, p_c, p_r])
        
    q_table = Table(table_data, colWidths=[30, 210, 110, 110, 60], repeatRows=1)
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(q_table)
    elements.append(Spacer(1, 10))
    
    summary_style = ParagraphStyle('PDFSummary', parent=styles['Normal'], fontName=PDF_FONT, fontSize=11)
    elements.append(Paragraph(f"<b>Total Score Obtained:</b> {score} / {len(q_list)}", summary_style))
    elements.append(Spacer(1, 20))
    
    sig_data = [
        [Paragraph(f"<b>Teacher Name:</b> {info.get('teacher_name', 'N/A')}", info_style), Paragraph("", info_style)],
        [Paragraph(f"<b>Subject:</b> {info['sub']}", info_style), Paragraph("________________________", info_style)],
        [Paragraph("", info_style), Paragraph("<b>Teacher's Signature</b>", info_style)]
    ]
    sig_table = Table(sig_data, colWidths=[300, 220])
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ================= DB SETUP =================
def setup_database():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
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
                ) DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci""")

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
                ) DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    teacher_id INT NOT NULL,
                    class_name VARCHAR(20) NOT NULL,
                    subject_name VARCHAR(100) NOT NULL
                ) DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    teacher_id INT NOT NULL,
                    class_name VARCHAR(20) NOT NULL,
                    subject_name VARCHAR(100) NOT NULL,
                    chapter_name VARCHAR(100) NOT NULL
                ) DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci""")

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
                ) DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci""")

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
                ) DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci""")
            conn.commit()
    except Exception as e:
        st.error(f"Database Initialization Error: {e}")

setup_database()

def generate_credentials(name):
    clean_name = "".join(e for e in name if e.isalnum()).lower()[:4]
    rand_num = random.randint(1000, 9999)
    userid = f"stu_{clean_name}{rand_num}"
    chars = string.ascii_letters + string.digits
    password = "".join(random.choice(chars) for _ in range(6))
    return userid, password

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

        teacher_map = {"🏛️ System Administrator (Assign Teacher Later)": None}
        for t in approved_teachers:
            label = f"{t['teacher_name']} ({t['institute_name'] or 'Private Batch'}) - Code: {t['teacher_code']}"
            teacher_map[label] = t['id']

        with st.form("stu_reg_form"):
            selected_t_str = st.selectbox("Select Administrator / Teacher *", list(teacher_map.keys()))
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
                st.warning("⚠️ সমস্ত প্রয়োজনীয় বিবরণ পূরণ করুন!")
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
                    
                    st.success("🎉 রেজিস্ট্রেশন আবেদন জমা হয়েছে!")
                    st.markdown(f"""
                        <div class='cred-box'>
                            <h4>📌 আপনার পরীক্ষার লগইন ক্রিডেনশিয়াল:</h4>
                            <p><b>User ID:</b> <code>{userid}</code></p>
                            <p><b>Password:</b> <code>{password}</code></p>
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

                if not student:
                    st.error("❌ ভুল User ID বা Password!")
                elif student['status'] != 'approved':
                    st.warning("⏳ আপনার অ্যাকাউন্টটি অনুমোদিত নয়।")
                elif not student['teacher_id']:
                    st.warning("⚠️ আপনাকে এখনো কোনো শিক্ষক বরাদ্দ করা হয়নি!")
                elif student['seat_for_exam'].lower() == 'no':
                    st.error("🚫 আপনার পরীক্ষা দেওয়ার অনুমতি স্থগিত রাখা রয়েছে।")
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
                    st.info(f"**Candidate:** {stu['name']} | **Class:** {stu['class_name']}")
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s AND teacher_id=%s", (stu['class_name'], stu['teacher_id']))
                        subjects = [r['subject_name'] for r in cursor.fetchall()]

                    stu_sub = st.selectbox("Select Subject", subjects if subjects else ["No Subjects Found"])

                with col_b:
                    chapters = []
                    if subjects:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s AND teacher_id=%s", (stu['class_name'], stu_sub, stu['teacher_id']))
                            chapters = [r['chapter_name'] for r in cursor.fetchall()]
                    
                    stu_chap = st.selectbox("Select Chapter", ["All Chapters (Combined)"] + chapters)

                if st.button("🚀 Start Exam Now", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        if stu_chap == "All Chapters (Combined)":
                            cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s AND teacher_id=%s ORDER BY RAND() LIMIT 40", (stu['class_name'], stu_sub, stu['teacher_id']))
                        else:
                            cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s AND chapter_name=%s AND teacher_id=%s ORDER BY RAND() LIMIT 40", (stu['class_name'], stu_sub, stu_chap, stu['teacher_id']))
                        raw_q = cursor.fetchall()
                        
                        cursor.execute("SELECT teacher_name FROM teachers WHERE id=%s", (stu['teacher_id'],))
                        t_rec = cursor.fetchone()
                        t_name = t_rec['teacher_name'] if t_rec else "N/A"

                    if not raw_q:
                        st.error("❌ এই বিষয়ে কোনো প্রশ্ন পাওয়া যায়নি!")
                    else:
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
                            'id': stu['id'], 'teacher_id': stu['teacher_id'], 'teacher_name': t_name, 
                            'class': stu['class_name'], 'roll': stu['userid'], 'name': stu['name'], 
                            'sub': stu_sub, 'chap': stu_chap
                        }
                        st.session_state.user_answers = {}
                        st.session_state.exam_start_time = time.time()
                        st.session_state.exam_started = True
                        st.session_state.exam_finished = False
                        st.rerun()

        else:
            info = st.session_state.student_info
            q_list = st.session_state.prepared_questions
            
            if not st.session_state.get("exam_finished", False):
                elapsed_time = time.time() - st.session_state.exam_start_time
                remaining_time = (40 * 60) - elapsed_time

                if remaining_time <= 0:
                    st.warning("⏰ সময় শেষ! উত্তরপত্র স্বয়ংক্রিয়ভাবে জমা হচ্ছে...")
                    st.session_state.last_score = submit_student_exam(q_list, info)
                    st.session_state.exam_finished = True
                    st.rerun()
                else:
                    render_digital_timer(remaining_time)
                    st.info(f"👤 **Student:** {info['name']} | **Subject:** {info['sub']}")
                    
                    with st.form("exam_form"):
                        for idx, q in enumerate(q_list):
                            st.markdown(f"#### Q{idx+1}. {q['text']}")
                            if q['image']:
                                try: st.image(q['image'], width=300)
                                except: pass
                            choice = st.radio(f"Select Option Q{idx+1}:", q['options'], index=None, key=f"q_{idx}")
                            if choice:
                                st.session_state.user_answers[idx] = q['options'].index(choice) + 1
                            st.divider()

                        submitted = st.form_submit_button("📤 Submit Final Exam", type="primary", use_container_width=True)

                    if submitted:
                        st.session_state.last_score = submit_student_exam(q_list, info)
                        st.session_state.exam_finished = True
                        st.rerun()
            else:
                st.balloons()
                st.success(f"🎉 পরীক্ষা সফলভাবে জমা হয়েছে! আপনার স্কোর: **{st.session_state.last_score} / {len(q_list)}**")
                detailed_pdf_bytes = generate_student_detailed_pdf(info, q_list, st.session_state.user_answers)
                
                st.download_button(
                    label="📄 Download Detailed Answer Sheet (A4 PDF)",
                    data=detailed_pdf_bytes,
                    file_name=f"AnswerSheet_{info['roll']}_{info['sub']}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                if st.button("🔄 Back to Dashboard"):
                    st.session_state.exam_started = False
                    st.session_state.exam_ready = False
                    st.session_state.exam_finished = False
                    st.rerun()

# ================= 2. TEACHER PORTAL =================
elif menu == "👨‍🏫 Teacher Portal":
    st.markdown("<div class='banner'><h2>👨‍🏫 Teacher Dashboard</h2></div>", unsafe_allow_html=True)
    
    if "logged_teacher" not in st.session_state:
        st.session_state.logged_teacher = None

    if not st.session_state.logged_teacher:
        t_action = st.radio("Teacher Authorization", ["🔐 Teacher Login", "📝 New Teacher Signup"], horizontal=True)
        st.divider()

        if t_action == "📝 New Teacher Signup":
            with st.form("t_signup"):
                t_name = st.text_input("Full Name *")
                t_inst = st.text_input("Institute / Coaching Name")
                t_email = st.text_input("Email Address *")
                t_code = st.text_input("Teacher Code *")
                t_pwd = st.text_input("Password *", type="password")
                submit_t = st.form_submit_button("Register Teacher Account", type="primary")

            if submit_t and t_name and t_email and t_code and t_pwd:
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        sql = "INSERT INTO teachers (teacher_name, institute_name, teacher_code, email, password, status) VALUES (%s, %s, %s, %s, %s, 'pending')"
                        cursor.execute(sql, (t_name, t_inst, t_code, t_email, t_pwd))
                        conn.commit()
                    st.success("🎉 রেজিস্ট্রেশন সফল হয়েছে! অ্যাডমিন অনুমোদনের অপেক্ষা করুন।")
                except Exception as e:
                    st.error(f"Error: {e}")

        elif t_action == "🔐 Teacher Login":
            col1, col2 = st.columns(2)
            with col1:
                t_login_id = st.text_input("Email or Teacher Code")
                t_login_pwd = st.text_input("Password", type="password")
            
            if st.button("Login", type="primary"):
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM teachers WHERE (email=%s OR teacher_code=%s) AND password=%s", (t_login_id, t_login_id, t_login_pwd))
                    teacher = cursor.fetchone()

                if not teacher or teacher['status'] != 'approved':
                    st.error("❌ লগইন ব্যাহত হয়েছে অথবা অনুমোদন বাকি!")
                else:
                    st.session_state.logged_teacher = teacher
                    st.rerun()

    else:
        teacher = st.session_state.logged_teacher
        st.sidebar.markdown(f"**👨‍🏫 Teacher:** {teacher['teacher_name']}")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_teacher = None
            st.rerun()

        t_tab1, t_tab2, t_tab3, t_tab4 = st.tabs([
            "👥 Student Management", 
            "📚 Subjects & Chapters", 
            "➕ Question Bank (Single Form)", 
            "📊 Results & PDF Reports"
        ])

        # --- TAB 1: STUDENT MANAGEMENT & SEARCH ---
        with t_tab1:
            st.subheader("📋 Student List & Search Filter")
            search_student = st.text_input("🔍 Search Student by Name / User ID", key="search_stu_key")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                if search_student:
                    cursor.execute("""SELECT id, name, class_name, userid, status, seat_for_exam 
                                      FROM students WHERE teacher_id=%s AND (name LIKE %s OR userid LIKE %s)""", 
                                   (teacher['id'], f"%{search_student}%", f"%{search_student}%"))
                else:
                    cursor.execute("""SELECT id, name, class_name, userid, status, seat_for_exam 
                                      FROM students WHERE teacher_id=%s""", (teacher['id'],))
                stu_list = cursor.fetchall()

            if stu_list:
                st.dataframe(stu_list, use_container_width=True)
                col_x, col_y = st.columns(2)
                with col_x:
                    st.markdown("#### Update Status")
                    p_dict = {f"{s['name']} ({s['userid']})": s['id'] for s in stu_list}
                    sel_p = st.selectbox("Select Student", list(p_dict.keys()), key="sel_stu_status_key")
                    act_p = st.radio("Set Status:", ["approved", "rejected", "pending"], horizontal=True)
                    if st.button("Update Status"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            app_date = datetime.now() if act_p == 'approved' else None
                            cursor.execute("UPDATE students SET status=%s, approved_at=%s WHERE id=%s", (act_p, app_date, p_dict[sel_p]))
                            conn.commit()
                        st.success("✅ স্ট্যাটাস পরিবর্তিত হয়েছে!")
                        st.rerun()
                with col_y:
                    st.markdown("#### Delete Student")
                    if st.button("🗑️ Delete Selected Student", type="primary"):
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM students WHERE id=%s", (p_dict[sel_p],))
                            conn.commit()
                        st.success("🗑️ অ্যাকাউন্ট মুছে দেওয়া হয়েছে!")
                        st.rerun()

        # --- TAB 2: SUBJECTS & CHAPTERS ---
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
                        st.success("✅ সাবজেক্ট সেভ হয়েছে!")

            with col_b:
                st.subheader("Add Chapter")
                c_cls = st.selectbox("Class", CLASSES, key="tc_cls")
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s AND teacher_id=%s", (c_cls, teacher['id']))
                    subs = [r['subject_name'] for r in cursor.fetchall()]

                c_sub = st.selectbox("Subject", subs if subs else ["None"])
                c_name = st.text_input("Chapter Name")
                if st.button("Save Chapter") and c_name and c_sub != "None":
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("INSERT INTO chapters (teacher_id, class_name, subject_name, chapter_name) VALUES (%s, %s, %s, %s)", (teacher['id'], c_cls, c_sub, c_name))
                        conn.commit()
                    st.success("✅ চ্যাপ্টার সেভ হয়েছে!")

        # --- TAB 3: QUESTION BANK (SOLVED: SINGLE FORM ENTRY & CLEAR) ---
        with t_tab3:
            st.subheader("➕ Question Entry Form")
            
            q_cls = st.selectbox("Select Class", CLASSES, key="form_q_cls")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s AND teacher_id=%s", (q_cls, teacher['id']))
                q_subs = [r['subject_name'] for r in cursor.fetchall()]

            q_sub = st.selectbox("Select Subject", q_subs if q_subs else ["None"], key="form_q_sub")
            
            q_chaps = []
            if q_subs:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s AND teacher_id=%s", (q_cls, q_sub, teacher['id']))
                    q_chaps = [r['chapter_name'] for r in cursor.fetchall()]

            q_chap = st.selectbox("Select Chapter", q_chaps if q_chaps else ["None"], key="form_q_chap")

            # COMPLETE SINGLE FORM FOR QUESTION & ALL OPTIONS
            with st.form("single_question_entry_form", clear_on_submit=True):
                q_text = st.text_area("Question Text (বাংলা টাইপ করুন)", help="এখানে প্রশ্ন লিখুন")
                q_img_file = st.file_uploader("📷 Optional Diagram/Image", type=['png', 'jpg', 'jpeg'])
                
                c1, c2 = st.columns(2)
                with c1:
                    opt_corr = st.text_input("✅ Correct Option (Option 1)")
                    opt_w1 = st.text_input("❌ Option 2")
                with c2:
                    opt_w2 = st.text_input("❌ Option 3")
                    opt_w3 = st.text_input("❌ Option 4")

                submit_q = st.form_submit_button("💾 Save Entire Question & Options", type="primary", use_container_width=True)

            if submit_q:
                if q_text and opt_corr and opt_w1 and opt_w2 and opt_w3 and q_chap != "None":
                    img_url = process_uploaded_image(q_img_file)
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
                    st.success("✅ প্রশ্ন ও সমস্ত অপশন সফলভাবে সেভ হয়েছে এবং টেক্সটবক্স ফাঁকা করা হয়েছে!")
                else:
                    st.error("⚠️ সমস্ত বিবরণ ও অপশন সঠিকভাবে পূরণ করুন!")

        # --- TAB 4: RESULTS ---
        with t_tab4:
            st.subheader("📊 Exam Results")
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                    FROM exam_results WHERE teacher_id=%s ORDER BY exam_date DESC""", (teacher['id'],))
                t_results = cursor.fetchall()

            if t_results:
                st.dataframe(t_results, use_container_width=True)
                pdf_bytes = generate_pdf_report(t_results, title=f"Results - {teacher['teacher_name']}")
                st.download_button("📥 Download Results PDF", data=pdf_bytes, file_name=f"Results_{teacher['teacher_code']}.pdf", mime="application/pdf")

# ================= 3. VIEW RESULTS =================
elif menu == "📊 View Student Results":
    st.markdown("<div class='banner'><h2>📊 Individual Result Search</h2></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: search_cls = st.selectbox("Class", CLASSES)
    with col2: search_uid = st.text_input("Enter Student User ID")

    if st.button("🔍 Search Record", use_container_width=True) and search_uid:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                FROM exam_results WHERE class_name=%s AND roll_no=%s""", (search_cls, search_uid))
            rows = cursor.fetchall()

        if rows:
            st.dataframe(rows, use_container_width=True)
            pdf_data = generate_pdf_report(rows, title=f"Result Sheet - {rows[0]['student_name']}")
            st.download_button("📄 Download Individual PDF", data=pdf_data, file_name=f"Result_{search_uid}.pdf", mime="application/pdf")

# ================= 4. SUPER ADMIN PANEL =================
elif menu == "👑 Super Admin Panel":
    st.markdown("<div class='banner'><h2>👑 Super Administrative Control</h2></div>", unsafe_allow_html=True)
    if st.text_input("🔐 Enter Passcode", type="password") == SUPER_ADMIN_PASSWORD:
        st.success("🔑 Admin Access Granted")
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, teacher_name, teacher_code, email, status FROM teachers")
            all_teachers = cursor.fetchall()
            cursor.execute("SELECT id, name, class_name, userid, status FROM students")
            all_students = cursor.fetchall()

        st.subheader("Teachers Master Control")
        st.dataframe(all_teachers, use_container_width=True)
        
        st.subheader("Students Master Control")
        st.dataframe(all_students, use_container_width=True)

# ================= FOOTER =================
st.markdown("""
    <div class="footer">
        Created by <b>PARTHA PRATIM BHATTACHARYA</b> | Email: <a href="mailto:bhattacharyap72@gmail.com">bhattacharyap72@gmail.com</a>
    </div>
""", unsafe_allow_html=True)
