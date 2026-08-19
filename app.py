import streamlit as st
import pymysql
import pymysql.cursors
import random
import string
import base64
from datetime import date
from io import BytesIO

# --- ReportLab Imports for PDF Generation ---
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Online Examination Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= DARK THEME & CUSTOM CSS =================
st.markdown("""
    <style>
    /* Dark Background for Main App */
    .stApp, .main {
        background-color: #0e1117 !important;
        color: #e0e0e0 !important;
    }
    
    /* Headers Styling */
    h1, h2, h3, h4, h5, h6 {
        color: #60a5fa !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Text Input, Selectbox, Text Area Dark Styling */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>div, 
    .stTextArea>div>div>textarea,
    .stDateInput>div>div>input {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
        border-radius: 6px;
    }
    
    /* Buttons Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* Dark Custom Banner */
    .banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid #1e40af;
    }
    
    /* Dark Credentials Card */
    .cred-box {
        background-color: #1e293b;
        border-left: 6px solid #38bdf8;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
        color: #f1f5f9;
    }
    
    /* Card for Questions */
    .question-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border-left: 5px solid #3b82f6;
    }
    
    /* Dataframe Dark Mode */
    [data-testid="stDataFrame"] {
        background-color: #1f2937 !important;
        border-radius: 8px;
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
ADMIN_PASSWORD = "admin"

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

# ================= PDF GENERATOR FUNCTION =================
def generate_pdf_report(data_rows, title="Online Exam Result Sheet"):
    """Generates a downloadable PDF binary stream from database rows."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PDFTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=15,
        alignment=1 # Center
    )
    
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))
    
    if data_rows:
        # Table Header
        headers = list(data_rows[0].keys())
        table_data = [[str(h).replace('_', ' ').title() for h in headers]]
        
        # Table Data
        for row in data_rows:
            table_data.append([str(row[h]) if row[h] is not None else "" for h in headers])
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No exam records found.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ================= AUTO SETUP DATABASE TABLES =================
def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address TEXT,
                school_name VARCHAR(150),
                class_name VARCHAR(20) NOT NULL,
                dob DATE,
                userid VARCHAR(50) UNIQUE,
                password VARCHAR(50),
                seat_for_exam VARCHAR(10) DEFAULT 'yes'
            )""")
        
        existing_cols = []
        cursor.execute("SHOW COLUMNS FROM students")
        existing_cols = [row['Field'] for row in cursor.fetchall()]
        
        col_definitions = {
            'address': "TEXT",
            'school_name': "VARCHAR(150)",
            'dob': "DATE",
            'userid': "VARCHAR(50)",
            'password': "VARCHAR(50)",
            'seat_for_exam': "VARCHAR(10) DEFAULT 'yes'"
        }
        
        for col, dtype in col_definitions.items():
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE students ADD COLUMN {col} {dtype}")
                
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database Initialization Error: {e}")

setup_database()

# Helper function to generate Credentials
def generate_credentials(name):
    clean_name = "".join(e for e in name if e.isalnum()).lower()[:4]
    rand_num = random.randint(1000, 9999)
    userid = f"stu_{clean_name}{rand_num}"
    
    chars = string.ascii_letters + string.digits
    password = "".join(random.choice(chars) for _ in range(6))
    return userid, password

# ================= LOGIN SYSTEM =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<div class='banner'><h1>🎓 Online Examination System</h1><p>Secure Portal Authorization</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔑 Enter System Security Key")
            pwd = st.text_input("Access Password", type="password", placeholder="Enter authorization key")
            submit_login = st.form_submit_button("Enter Portal", use_container_width=True, type="primary")
            
            if submit_login:
                if pwd == "Exam2026#Access":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ ভুল পাসওয়ার্ড! সঠিক পাসওয়ার্ড দিন।")
    st.stop()

# ================= MAIN MENU =================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=100)
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select Module", ["📝 Student Portal", "📊 View Results", "⚙️ Admin Panel"])

# ---------- 1. STUDENT PORTAL ----------
if menu == "📝 Student Portal":
    st.markdown("<div class='banner'><h2>📝 Student Examination Portal</h2></div>", unsafe_allow_html=True)
    
    student_tab = st.radio("Choose Action", ["📋 New Student Registration", "🔑 Login & Start Exam"], horizontal=True)
    st.divider()

    # --- REGISTRATION SECTION ---
    if student_tab == "📋 New Student Registration":
        st.subheader("👤 Student Registration Form")
        
        with st.form("reg_form"):
            col1, col2 = st.columns(2)
            with col1:
                reg_name = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma")
                reg_school = st.text_input("School Name *", placeholder="e.g. ABC High School")
                reg_class = st.selectbox("Class *", CLASSES)
            with col2:
                reg_dob = st.date_input("Date of Birth *", min_value=date(1990, 1, 1), max_value=date.today())
                reg_address = st.text_area("Address *", placeholder="Enter full address")
                
            submit_reg = st.form_submit_button("Submit Registration", type="primary", use_container_width=True)

        if submit_reg:
            if not (reg_name and reg_school and reg_address):
                st.warning("⚠️ অনুগ্রহ করে সমস্ত প্রয়োজনীয় বিবরণ প্রদান করুন!")
            else:
                userid, password = generate_credentials(reg_name)
                
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        sql = """INSERT INTO students 
                                 (name, address, school_name, class_name, dob, userid, password, seat_for_exam)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, 'yes')"""
                        cursor.execute(sql, (reg_name, reg_address, reg_school, reg_class, reg_dob, userid, password))
                        conn.commit()
                    conn.close()
                    
                    st.success("🎉 রেজিস্ট্রেশন সফলভাবে সম্পন্ন হয়েছে!")
                    st.markdown(f"""
                        <div class='cred-box'>
                            <h4>📌 আপনার পরীক্ষার লগইন বিবরণ (Credentials):</h4>
                            <p><b>User ID:</b> <code>{userid}</code></p>
                            <p><b>Password:</b> <code>{password}</code></p>
                            <small>⚠️ এই User ID এবং Password টি লিখে রাখুন। পরীক্ষায় অংশগ্রহণের জন্য এটি প্রয়োজন হবে।</small>
                        </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"রেজিস্ট্রেশনে ত্রুটি ঘটেছে: {e}")

    # --- EXAM LOGIN SECTION ---
    elif student_tab == "🔑 Login & Start Exam":
        if "exam_started" not in st.session_state:
            st.session_state.exam_started = False

        if not st.session_state.exam_started:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔑 Student Authentication")
                login_uid = st.text_input("User ID", placeholder="Enter your generated User ID")
                login_pwd = st.text_input("Password", type="password", placeholder="Enter Password")

            if st.button("Verify & Proceed to Exam", type="primary"):
                if not (login_uid and login_pwd):
                    st.warning("⚠️ User ID এবং Password উভয়ই প্রদান করুন!")
                else:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM students WHERE userid=%s AND password=%s", (login_uid, login_pwd))
                        student = cursor.fetchone()
                    conn.close()

                    if not student:
                        st.error("❌ ভুল User ID অথবা Password!")
                    elif student['seat_for_exam'].lower() == 'no':
                        st.error("🚫 এডমিনিস্ট্রেটর আপনার পরীক্ষা দেওয়ার অনুমতি স্থগিত (Disable) করেছেন! আপনি আর পরীক্ষা দিতে পারবেন না।")
                    else:
                        st.session_state.logged_student = student
                        st.session_state.exam_ready = True
                        st.success(f"স্বাগতম, {student['name']}! আপনার অ্যাকাউন্ট অনুমোদিত হয়েছে।")

            # Subject & Chapter Selection
            if st.session_state.get("exam_ready", False):
                st.divider()
                st.subheader("📚 Select Exam Details")
                stu = st.session_state.logged_student
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"**Candidate:** {stu['name']} | **Class:** {stu['class_name']}")
                    
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s", (stu['class_name'],))
                        subjects = [r['subject_name'] for r in cursor.fetchall()]
                    conn.close()

                    stu_sub = st.selectbox("Select Subject", subjects if subjects else ["No Subjects Found"])

                with col_b:
                    chapters = []
                    if subjects:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s", (stu['class_name'], stu_sub))
                            chapters = [r['chapter_name'] for r in cursor.fetchall()]
                        conn.close()
                    
                    stu_chap = st.selectbox("Select Chapter", ["All Chapters (Combined)"] + chapters)

                if st.button("🚀 Start Exam Now", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        if stu_chap == "All Chapters (Combined)":
                            cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s ORDER BY RAND() LIMIT 40", (stu['class_name'], stu_sub))
                        else:
                            cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s AND chapter_name=%s ORDER BY RAND() LIMIT 40", (stu['class_name'], stu_sub, stu_chap))
                        raw_q = cursor.fetchall()
                    conn.close()

                    if not raw_q:
                        st.error("❌ এই বিষয়টি বা চ্যাপ্টারে কোনো প্রশ্ন যুক্ত করা নেই!")
                    else:
                        prepared_q = []
                        for q in raw_q:
                            opts = [q['option1'], q['option2'], q['option3'], q['option4']]
                            correct_txt = opts[q['correct_option'] - 1]
                            random.shuffle(opts)
                            prepared_q.append({
                                'id': q['id'],
                                'text': q['question_text'],
                                'image': q.get('image_path'),
                                'options': opts,
                                'correct': opts.index(correct_txt) + 1
                            })
                        
                        st.session_state.prepared_questions = prepared_q
                        st.session_state.student_info = {
                            'id': stu['id'], 
                            'class': stu['class_name'], 
                            'roll': stu['userid'], 
                            'name': stu['name'], 
                            'sub': stu_sub, 
                            'chap': stu_chap
                        }
                        st.session_state.user_answers = {}
                        st.session_state.exam_started = True
                        st.rerun()

        else:
            # Candidate Exam Interface
            info = st.session_state.student_info
            st.info(f"👤 **Student:** {info['name']} | **User ID:** {info['roll']} | **Class:** {info['class']} | **Subject:** {info['sub']}")
            
            q_list = st.session_state.prepared_questions
            
            with st.form("exam_form"):
                for idx, q in enumerate(q_list):
                    st.markdown(f"#### Q{idx+1}. {q['text']}")
                    
                    if q['image']:
                        try:
                            st.image(q['image'], width=350)
                        except:
                            pass
                    
                    choice = st.radio(f"Select Option for Q{idx+1}:", q['options'], index=None, key=f"q_{idx}")
                    if choice:
                        st.session_state.user_answers[idx] = q['options'].index(choice) + 1
                    st.divider()

                submitted = st.form_submit_button("📤 Submit Final Exam", type="primary", use_container_width=True)

            if submitted:
                score = 0
                for idx, q in enumerate(q_list):
                    if st.session_state.user_answers.get(idx) == q['correct']:
                        score += 1
                
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    sql = """INSERT INTO exam_results 
                             (student_id, class_name, roll_no, student_name, subject_name, chapter_name, score, total_questions)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql, (
                        info['id'], info['class'], info['roll'], info['name'], 
                        info['sub'], info['chap'], score, len(q_list)
                    ))
                    conn.commit()
                conn.close()

                st.balloons()
                st.success(f"🎉 পরীক্ষা সফলভাবে জমা হয়েছে! আপনার স্কোর: **{score} / {len(q_list)}**")
                if st.button("⬅️ Back to Home"):
                    st.session_state.exam_started = False
                    st.session_state.exam_ready = False
                    st.rerun()

# ---------- 2. VIEW RESULTS & PDF DOWNLOAD ----------
elif menu == "📊 View Results":
    st.markdown("<div class='banner'><h2>📊 Student Assessment Results</h2></div>", unsafe_allow_html=True)
    
    res_mode = st.radio("Select View Mode", ["👤 Individual Student Result", "📋 Total / All Students Results"], horizontal=True)
    st.divider()

    # --- 1. INDIVIDUAL STUDENT RESULT ---
    if res_mode == "👤 Individual Student Result":
        col1, col2 = st.columns(2)
        with col1:
            res_cls = st.selectbox("Class", CLASSES)
        with col2:
            res_uid = st.text_input("Enter Student User ID")

        if st.button("🔍 Search Performance Record", use_container_width=True):
            if res_uid:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                        FROM exam_results 
                        WHERE class_name=%s AND roll_no=%s""", (res_cls, res_uid))
                    rows = cursor.fetchall()
                conn.close()

                if rows:
                    st.dataframe(rows, use_container_width=True)
                    
                    # Generate PDF for Individual Student
                    pdf_data = generate_pdf_report(rows, title=f"Exam Result - {rows[0]['student_name']} ({res_uid})")
                    st.download_button(
                        label="📄 Download Student Result (PDF)",
                        data=pdf_data,
                        file_name=f"Result_{res_uid}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.warning("❌ কোনো ফলাফল পাওয়া যায়নি!")

    # --- 2. TOTAL / ALL STUDENTS RESULTS ---
    else:
        st.subheader("📋 Overall Assessment Summary")
        filter_cls = st.selectbox("Filter by Class (Optional)", ["All Classes"] + CLASSES)
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if filter_cls == "All Classes":
                cursor.execute("""
                    SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                    FROM exam_results ORDER BY exam_date DESC""")
            else:
                cursor.execute("""
                    SELECT student_name, roll_no AS user_id, class_name, subject_name, chapter_name, score, total_questions, exam_date 
                    FROM exam_results WHERE class_name=%s ORDER BY exam_date DESC""", (filter_cls,))
            all_rows = cursor.fetchall()
        conn.close()

        if all_rows:
            st.dataframe(all_rows, use_container_width=True)
            
            # Generate PDF for Total Results
            pdf_all_data = generate_pdf_report(all_rows, title=f"All Exam Results Report ({filter_cls})")
            st.download_button(
                label="📥 Download Total Results Report (PDF)",
                data=pdf_all_data,
                file_name=f"Total_Exam_Results_{filter_cls.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("কোনো পরীক্ষার ফলাফল ডাটাবেসে পাওয়া যায়নি।")

# ---------- 3. ADMIN PANEL ----------
elif menu == "⚙️ Admin Panel":
    st.markdown("<div class='banner'><h2>⚙️ Administrative Control</h2></div>", unsafe_allow_html=True)
    
    admin_pwd = st.text_input("🔐 Enter Admin Passcode", type="password")
    
    if admin_pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Student Credentials & Seat Control", "📚 Subjects & Chapters", "➕ Add Question", "🗑️ Manage Questions"])

        # TAB 1: STUDENT CREDENTIALS & SEAT MANAGEMENT
        with tab1:
            st.subheader("📋 Registered Students Master Database")
            
            if st.button("🔄 Refresh Student Data"):
                st.rerun()

            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, class_name, school_name, address, dob, userid, password, seat_for_exam FROM students")
                students_data = cursor.fetchall()
            conn.close()

            if students_data:
                st.dataframe(students_data, use_container_width=True)
                
                # Download Registered Students PDF
                students_pdf = generate_pdf_report(students_data, title="Registered Students Master List")
                st.download_button(
                    label="📥 Download Registered Students List (PDF)",
                    data=students_pdf,
                    file_name="Registered_Students_List.pdf",
                    mime="application/pdf"
                )
                
                st.divider()
                st.subheader("🚫 Modify Student Exam Permission (`seat_for_exam`)")
                
                stu_dict = {f"{s['name']} (ID: {s['userid']} | Class: {s['class_name']}) - Permission: {s['seat_for_exam']}": s['id'] for s in students_data}
                selected_stu_str = st.selectbox("Select Student to Modify Access", list(stu_dict.keys()))
                new_status = st.radio("Exam Access Permission:", ["yes", "no"], horizontal=True)

                if st.button("Update Access Permission", type="primary"):
                    target_id = stu_dict[selected_stu_str]
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("UPDATE students SET seat_for_exam=%s WHERE id=%s", (new_status, target_id))
                        conn.commit()
                    conn.close()
                    st.success(f"✅ অনুমতির স্থিতি সফলভাবে '{new_status}'-এ আপডেট করা হয়েছে!")
                    st.rerun()
            else:
                st.info("কোনো রেজিস্ট্রেশন ডাটা পাওয়া যায়নি।")

        # TAB 2: SUBJECTS & CHAPTERS
        with tab2:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Add Subject")
                sub_cls = st.selectbox("Class", CLASSES, key="s_cls")
                sub_name = st.text_input("Subject Title")
                if st.button("Save Subject"):
                    if sub_name:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("INSERT INTO subjects (class_name, subject_name) VALUES (%s, %s)", (sub_cls, sub_name))
                            conn.commit()
                        conn.close()
                        st.success("✅ সাবজেক্ট যুক্ত হয়েছে!")

            with col_b:
                st.subheader("Add Chapter")
                chap_cls = st.selectbox("Class", CLASSES, key="c_cls")
                
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s", (chap_cls,))
                    subs = [r['subject_name'] for r in cursor.fetchall()]
                conn.close()

                chap_sub = st.selectbox("Subject", subs if subs else ["None"])
                chap_name = st.text_input("Chapter Title")
                if st.button("Save Chapter"):
                    if chap_name and chap_sub != "None":
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("INSERT INTO chapters (class_name, subject_name, chapter_name) VALUES (%s, %s, %s)", (chap_cls, chap_sub, chap_name))
                            conn.commit()
                        conn.close()
                        st.success("✅ চ্যাপ্টার যুক্ত হয়েছে!")

        # TAB 3: ADD QUESTION
        with tab3:
            st.subheader("Create New Question")
            q_cls = st.selectbox("Class", CLASSES, key="q_cls")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s", (q_cls,))
                q_subs = [r['subject_name'] for r in cursor.fetchall()]
            conn.close()

            q_sub = st.selectbox("Subject", q_subs if q_subs else ["None"], key="q_sub")
            
            q_chaps = []
            if q_subs:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s", (q_cls, q_sub))
                    q_chaps = [r['chapter_name'] for r in cursor.fetchall()]
                conn.close()

            q_chap = st.selectbox("Chapter", q_chaps if q_chaps else ["None"], key="q_chap")
            
            q_text = st.text_area("Question Text / Statement")
            
            q_img_file = st.file_uploader("🖼️ Upload Diagram/Image (Optional)", type=['png', 'jpg', 'jpeg'])
            img_url = None
            if q_img_file:
                bytes_data = q_img_file.getvalue()
                base64_str = base64.b64encode(bytes_data).decode('utf-8')
                img_url = f"data:image/png;base64,{base64_str}"
                st.image(q_img_file, caption="Uploaded Preview", width=200)

            col1, col2 = st.columns(2)
            with col1:
                opt_corr = st.text_input("✅ Correct Answer")
                opt_w1 = st.text_input("❌ Option 2 (Incorrect)")
            with col2:
                opt_w2 = st.text_input("❌ Option 3 (Incorrect)")
                opt_w3 = st.text_input("❌ Option 4 (Incorrect)")

            if st.button("💾 Save Question", type="primary", use_container_width=True):
                if q_text and opt_corr and opt_w1 and opt_w2 and opt_w3 and q_chap != "None":
                    opts = [opt_corr, opt_w1, opt_w2, opt_w3]
                    random.shuffle(opts)
                    corr_idx = opts.index(opt_corr) + 1

                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        sql = """INSERT INTO questions 
                                 (class_name, subject_name, chapter_name, question_text, image_path, option1, option2, option3, option4, correct_option)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                        cursor.execute(sql, (q_cls, q_sub, q_chap, q_text, img_url, opts[0], opts[1], opts[2], opts[3], corr_idx))
                        conn.commit()
                    conn.close()
                    st.success("✅ প্রশ্ন সফলভাবে সংরক্ষণ করা হয়েছে!")

        # TAB 4: DELETE QUESTION
        with tab4:
            st.subheader("Delete Question")
            del_cls = st.selectbox("Class", CLASSES, key="del_cls")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, question_text FROM questions WHERE class_name=%s", (del_cls,))
                del_questions = cursor.fetchall()
            conn.close()

            if del_questions:
                q_dict = {f"ID: {q['id']} - {q['question_text'][:50]}...": q['id'] for q in del_questions}
                selected_q = st.selectbox("Select Question", list(q_dict.keys()))
                
                if st.button("🗑️ Delete Selected Question", type="primary"):
                    q_id = q_dict[selected_q]
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM questions WHERE id=%s", (q_id,))
                        conn.commit()
                    conn.close()
                    st.success("🗑️ প্রশ্ন মুছে ফেলা হয়েছে!")
                    st.rerun()
