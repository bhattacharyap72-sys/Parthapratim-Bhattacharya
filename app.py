import streamlit as st
import pymysql
import pymysql.cursors
import random
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

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

# ================= DATABASE CONNECTION =================
def get_db_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def setup_database():
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_name VARCHAR(20) NOT NULL,
                subject_name VARCHAR(100) NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_name VARCHAR(20) NOT NULL,
                subject_name VARCHAR(100) NOT NULL,
                chapter_name VARCHAR(150) NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_name VARCHAR(20) NOT NULL,
                subject_name VARCHAR(100) NOT NULL,
                chapter_name VARCHAR(150) NOT NULL,
                question_text TEXT NOT NULL,
                image_path VARCHAR(255) DEFAULT NULL,
                option1 VARCHAR(255) NOT NULL,
                option2 VARCHAR(255) NOT NULL,
                option3 VARCHAR(255) NOT NULL,
                option4 VARCHAR(255) NOT NULL,
                correct_option INT NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_name VARCHAR(20) NOT NULL,
                roll_no VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                class_name VARCHAR(20) NOT NULL,
                roll_no VARCHAR(50) NOT NULL,
                student_name VARCHAR(100) NOT NULL,
                subject_name VARCHAR(100) NOT NULL,
                chapter_name VARCHAR(150) NOT NULL,
                score INT NOT NULL,
                total_questions INT NOT NULL,
                exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )""")
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database setup error: {e}")

setup_database()

# Page Config
st.set_page_config(page_title="Online Examination System", layout="wide")

# ================= LOGIN SYSTEM =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 System Authorization")
    pwd = st.text_input("Enter Security Password:", type="password")
    if st.button("Login"):
        if pwd == "Exam2026#Access":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("ভুল পাসওয়ার্ড! আবার চেষ্টা করুন।")
    st.stop()

# ================= MAIN MENU =================
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Student Exam Portal", "View Student Results", "Admin Panel"])

# ---------- 1. STUDENT EXAM PORTAL ----------
if menu == "Student Exam Portal":
    st.header("📝 Online Exam Portal")
    
    if "exam_started" not in st.session_state:
        st.session_state.exam_started = False

    if not st.session_state.exam_started:
        col1, col2 = st.columns(2)
        with col1:
            stu_class = st.selectbox("Select Class", CLASSES)
            stu_roll = st.text_input("Roll No")
            stu_name = st.text_input("Student Name")

        # Load Subjects
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s", (stu_class,))
            subjects = [r['subject_name'] for r in cursor.fetchall()]
        conn.close()

        with col2:
            stu_sub = st.selectbox("Select Subject", subjects if subjects else ["No Subjects Found"])
            
            # Load Chapters
            chapters = []
            if subjects:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s", (stu_class, stu_sub))
                    chapters = [r['chapter_name'] for r in cursor.fetchall()]
                conn.close()
            
            stu_chap = st.selectbox("Select Chapter", ["All Chapters (Combined)"] + chapters)

        if st.button("Start Exam (40 Min)", type="primary"):
            if not (stu_roll and stu_name and subjects):
                st.warning("সকল বিবরণ সঠিকভাবে প্রদান করুন!")
            else:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO students (class_name, roll_no, name) VALUES (%s, %s, %s)", (stu_class, stu_roll, stu_name))
                    conn.commit()
                    student_id = cursor.lastrowid

                    if stu_chap == "All Chapters (Combined)":
                        cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s ORDER BY RAND() LIMIT 40", (stu_class, stu_sub))
                    else:
                        cursor.execute("SELECT * FROM questions WHERE class_name=%s AND subject_name=%s AND chapter_name=%s ORDER BY RAND() LIMIT 40", (stu_class, stu_sub, stu_chap))
                    raw_q = cursor.fetchall()
                conn.close()

                if not raw_q:
                    st.error("এই সাবজেক্ট/চ্যাপ্টারে কোনো প্রশ্ন পাওয়া যায়নি!")
                else:
                    prepared_q = []
                    for q in raw_q:
                        opts = [q['option1'], q['option2'], q['option3'], q['option4']]
                        correct_txt = opts[q['correct_option'] - 1]
                        random.shuffle(opts)
                        prepared_q.append({
                            'id': q['id'],
                            'text': q['question_text'],
                            'options': opts,
                            'correct': opts.index(correct_txt) + 1
                        })
                    
                    st.session_state.prepared_questions = prepared_q
                    st.session_state.student_info = {'id': student_id, 'class': stu_class, 'roll': stu_roll, 'name': stu_name, 'sub': stu_sub, 'chap': stu_chap}
                    st.session_state.user_answers = {}
                    st.session_state.exam_started = True
                    st.rerun()

    else:
        st.subheader(f"Student: {st.session_state.student_info['name']} (Roll: {st.session_state.student_info['roll']})")
        st.caption(f"Subject: {st.session_state.student_info['sub']} | Chapter: {st.session_state.student_info['chap']}")
        
        q_list = st.session_state.prepared_questions
        
        with st.form("exam_form"):
            for idx, q in enumerate(q_list):
                st.write(f"**Q{idx+1}. {q['text']}**")
                choice = st.radio(f"Select option for Q{idx+1}", q['options'], index=None, key=f"q_{idx}")
                if choice:
                    st.session_state.user_answers[idx] = q['options'].index(choice) + 1
                st.divider()

            submitted = st.form_submit_button("Submit Exam", type="primary")

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
                    st.session_state.student_info['id'],
                    st.session_state.student_info['class'],
                    st.session_state.student_info['roll'],
                    st.session_state.student_info['name'],
                    st.session_state.student_info['sub'],
                    st.session_state.student_info['chap'],
                    score,
                    len(q_list)
                ))
                conn.commit()
            conn.close()

            st.balloons()
            st.success(f"পরীক্ষা সম্পন্ন হয়েছে! আপনার প্রাপ্ত নম্বর: {score} / {len(q_list)}")
            if st.button("Back to Home"):
                st.session_state.exam_started = False
                st.rerun()

# ---------- 2. VIEW STUDENT RESULTS ----------
elif menu == "View Student Results":
    st.header("📊 Student Results & History")
    
    col1, col2 = st.columns(2)
    with col1:
        res_cls = st.selectbox("Class", CLASSES)
    with col2:
        res_roll = st.text_input("Roll No to Search")

    if st.button("Search Results"):
        if res_roll:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject_name, chapter_name, score, total_questions, exam_date FROM exam_results WHERE class_name=%s AND roll_no=%s", (res_cls, res_roll))
                rows = cursor.fetchall()
            conn.close()

            if rows:
                st.dataframe(rows)
            else:
                st.warning("কোনো রেকর্ড পাওয়া যায়নি!")
        else:
            st.warning("রোল নম্বর প্রদান করুন!")

# ---------- 3. ADMIN PANEL ----------
elif menu == "Admin Panel":
    st.header("⚙️ Admin Panel")
    admin_pwd = st.text_input("Enter Admin Password", type="password")
    
    if admin_pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["Add Subject & Chapter", "Add Question", "Delete Questions"])

        with tab1:
            st.subheader("Add Subject")
            sub_cls = st.selectbox("Class for Subject", CLASSES, key="sub_cls")
            sub_name = st.text_input("Subject Name")
            if st.button("Save Subject"):
                if sub_name:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("INSERT INTO subjects (class_name, subject_name) VALUES (%s, %s)", (sub_cls, sub_name))
                        conn.commit()
                    conn.close()
                    st.success("সাবজেক্ট যুক্ত হয়েছে!")

            st.divider()
            st.subheader("Add Chapter")
            chap_cls = st.selectbox("Class for Chapter", CLASSES, key="chap_cls")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s", (chap_cls,))
                subs = [r['subject_name'] for r in cursor.fetchall()]
            conn.close()

            chap_sub = st.selectbox("Select Subject", subs if subs else ["None"])
            chap_name = st.text_input("Chapter Name")
            if st.button("Save Chapter"):
                if chap_name and chap_sub != "None":
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("INSERT INTO chapters (class_name, subject_name, chapter_name) VALUES (%s, %s, %s)", (chap_cls, chap_sub, chap_name))
                        conn.commit()
                    conn.close()
                    st.success("চ্যাপ্টার যুক্ত হয়েছে!")

        with tab2:
            st.subheader("Add New Question")
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
            
            q_text = st.text_area("Question Text")
            opt_corr = st.text_input("Correct Answer Option")
            opt_w1 = st.text_input("Wrong Option 1")
            opt_w2 = st.text_input("Wrong Option 2")
            opt_w3 = st.text_input("Wrong Option 3")

            if st.button("Save Question"):
                if q_text and opt_corr and opt_w1 and opt_w2 and opt_w3 and q_chap != "None":
                    opts = [opt_corr, opt_w1, opt_w2, opt_w3]
                    random.shuffle(opts)
                    corr_idx = opts.index(opt_corr) + 1

                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        sql = """INSERT INTO questions 
                                 (class_name, subject_name, chapter_name, question_text, option1, option2, option3, option4, correct_option)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                        cursor.execute(sql, (q_cls, q_sub, q_chap, q_text, opts[0], opts[1], opts[2], opts[3], corr_idx))
                        conn.commit()
                    conn.close()
                    st.success("প্রশ্ন সফলভাবে যোগ করা হয়েছে!")

        with tab3:
            st.subheader("Delete Question")
            del_cls = st.selectbox("Class", CLASSES, key="del_cls")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, question_text FROM questions WHERE class_name=%s", (del_cls,))
                del_questions = cursor.fetchall()
            conn.close()

            if del_questions:
                q_dict = {f"ID: {q['id']} - {q['question_text'][:50]}...": q['id'] for q in del_questions}
                selected_q = st.selectbox("Select Question to Delete", list(q_dict.keys()))
                
                if st.button("Delete Question", type="primary"):
                    q_id = q_dict[selected_q]
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM questions WHERE id=%s", (q_id,))
                        conn.commit()
                    conn.close()
                    st.success("প্রশ্ন মুছে ফেলা হয়েছে!")
                    st.rerun()
            else:
                st.info("কোনো প্রশ্ন পাওয়া যায়নি।")
