import streamlit as st
import pymysql
import pymysql.cursors
import random
import base64

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Online Examination Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS FOR BETTER UI =================
st.markdown("""
    <style>
    /* Main Background & Font */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Custom Headers */
    h1, h2, h3 {
        color: #1e3a8a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Card design for questions */
    .question-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border-left: 5px solid #2563eb;
    }
    
    /* Buttons Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Custom Banner */
    .banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
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

# ================= LOGIN SYSTEM =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<div class='banner'><h1>🎓 Online Examination System</h1><p>Secure Portal Login</p></div>", unsafe_allow_html=True)
    
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
menu = st.sidebar.radio("Select Module", ["📝 Student Exam Portal", "📊 View Results", "⚙️ Admin Panel"])

# ---------- 1. STUDENT EXAM PORTAL ----------
if menu == "📝 Student Exam Portal":
    st.markdown("<div class='banner'><h2>📝 Examination Portal</h2></div>", unsafe_allow_html=True)
    
    if "exam_started" not in st.session_state:
        st.session_state.exam_started = False

    if not st.session_state.exam_started:
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                stu_class = st.selectbox("📌 Select Class", CLASSES)
                stu_roll = st.text_input("🆔 Roll No", placeholder="e.g. 12")
                stu_name = st.text_input("👤 Student Name", placeholder="e.g. Rahul Sharma")

            # Load Subjects
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject_name FROM subjects WHERE class_name=%s", (stu_class,))
                subjects = [r['subject_name'] for r in cursor.fetchall()]
            conn.close()

            with col2:
                stu_sub = st.selectbox("📚 Select Subject", subjects if subjects else ["No Subjects Found"])
                
                chapters = []
                if subjects:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT chapter_name FROM chapters WHERE class_name=%s AND subject_name=%s", (stu_class, stu_sub))
                        chapters = [r['chapter_name'] for r in cursor.fetchall()]
                    conn.close()
                
                stu_chap = st.selectbox("📖 Select Chapter", ["All Chapters (Combined)"] + chapters)

            st.write("")
            if st.button("🚀 Start Exam Now", type="primary", use_container_width=True):
                if not (stu_roll and stu_name and subjects):
                    st.warning("⚠️ সকল তথ্য সঠিকভাবে পূরণ করুন!")
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
                        st.session_state.student_info = {'id': student_id, 'class': stu_class, 'roll': stu_roll, 'name': stu_name, 'sub': stu_sub, 'chap': stu_chap}
                        st.session_state.user_answers = {}
                        st.session_state.exam_started = True
                        st.rerun()

    else:
        # Candidate Info Header
        info = st.session_state.student_info
        st.info(f"👤 **Student:** {info['name']} | **Roll:** {info['roll']} | **Class:** {info['class']} | **Subject:** {info['sub']}")
        
        q_list = st.session_state.prepared_questions
        
        with st.form("exam_form"):
            for idx, q in enumerate(q_list):
                st.markdown(f"#### Q{idx+1}. {q['text']}")
                
                # Render Image if Available
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
                st.rerun()

# ---------- 2. VIEW RESULTS ----------
elif menu == "📊 View Results":
    st.markdown("<div class='banner'><h2>📊 Student Assessment Results</h2></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        res_cls = st.selectbox("Class", CLASSES)
    with col2:
        res_roll = st.text_input("Enter Student Roll No")

    if st.button("🔍 Search Performance Record", use_container_width=True):
        if res_roll:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT subject_name, chapter_name, score, total_questions, exam_date FROM exam_results WHERE class_name=%s AND roll_no=%s", (res_cls, res_roll))
                rows = cursor.fetchall()
            conn.close()

            if rows:
                st.dataframe(rows, use_container_width=True)
            else:
                st.warning("❌ কোনো ফলাফল পাওয়া যায়নি!")

# ---------- 3. ADMIN PANEL ----------
elif menu == "⚙️ Admin Panel":
    st.markdown("<div class='banner'><h2>⚙️ Administrative Control</h2></div>", unsafe_allow_html=True)
    
    admin_pwd = st.text_input("🔐 Enter Admin Passcode", type="password")
    
    if admin_pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["📚 Subjects & Chapters", "➕ Add Question (With Image)", "🗑️ Manage Questions"])

        with tab1:
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

        with tab2:
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
            
            # --- PHOTO UPLOAD OPTION ---
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
