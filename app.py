from flask import Flask, request, jsonify, render_template, redirect, session,url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 設定資料庫連接
def db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root", 
            password="", 
            database="university"
        )
    except mysql.connector.Error as error:
        print("Failed to connect to MySQL: {}", format(error))
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        student_id = request.form['student_id']
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if student:
            session['student_id'] = student['student_id']
            return redirect(url_for('index'))
        else:
            error = "未找到學生資料，請重試。"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('student_id', None)
    return redirect('/login')


# 首頁
@app.route('/')
def index():
    if 'student_id' not in session:
        return redirect('/login')
    student_id = session['student_id']
    conn = db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT department FROM students WHERE student_id = %s", (student_id,))
    result = cursor.fetchone()
    if result:
        department = result['department']
        # 獲取系部的所有課程
        cursor.execute("SELECT * FROM courses WHERE department = %s", (department,))
        courses = cursor.fetchall()
        # 確定哪些課程已被學生選擇
        cursor.execute("SELECT course_id FROM enrollments WHERE student_id = %s", (student_id,))
        enrolled_courses = {row['course_id'] for row in cursor.fetchall()}

        for course in courses:
            course['enrolled'] = course['course_id'] in enrolled_courses
        # 計算已選課程的學分總和
        cursor.execute("SELECT SUM(c.credits) as total_credits FROM courses c JOIN enrollments e ON c.course_id = e.course_id WHERE e.student_id = %s", (student_id,))
        total_credits = cursor.fetchone()['total_credits'] or 0

        return render_template('index.html', student_id=student_id, courses=courses, total_credits=total_credits)

    return "加載課程出錯或未找到學生系部"


# 加選課程
@app.route('/add_course', methods=['POST'])
def add_course():
    student_id = session['student_id']
    course_id = request.form['course_id']
    conn = db_connection()
    cursor = conn.cursor()

    # 檢查課程是否在學生所在的系
    cursor.execute("SELECT department FROM courses WHERE course_id = %s", (course_id,))
    course_dept_result = cursor.fetchone()
    if not course_dept_result:
        return"error : 沒有找到該課程。"

    course_dept = course_dept_result[0]
    
    cursor.execute("SELECT department FROM students WHERE student_id = %s", (student_id,))
    student_dept_result = cursor.fetchone()
    if not student_dept_result:
        return "error:沒有找到該學生的資料。"

    student_dept = student_dept_result[0]
    if course_dept != student_dept:
        return "error:學生只能選擇本系課程。"

    # 檢查課程是否已滿
    cursor.execute("SELECT capacity, enrolled_students FROM courses WHERE course_id = %s", (course_id,))
    capacity, enrolled_students = cursor.fetchone()
    if enrolled_students >= capacity:
        return "error : 該課程已滿。"

    # 檢查時間衝突
    cursor.execute("SELECT course_time FROM courses WHERE course_id = %s", (course_id,))
    new_course_time = cursor.fetchone()[0]
    cursor.execute("""
        SELECT c.course_time 
        FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE e.student_id = %s
    """, (student_id,))
    existing_times = cursor.fetchall()
    if any(new_course_time == time[0] for time in existing_times):
        return "error : 該課程與您現有的課程時間衝突。"

    # 檢查學分上限
    cursor.execute("SELECT SUM(c.credits) FROM courses c JOIN enrollments e ON c.course_id = e.course_id WHERE e.student_id = %s", (student_id,))
    total_credits = cursor.fetchone()[0] or 0
    cursor.execute("SELECT credits FROM courses WHERE course_id = %s", (course_id,))
    course_credits = cursor.fetchone()[0]
    if total_credits + course_credits > 30:
        return "error : 選擇此課程將超出學分限制。"
    
    # 注冊課程
    cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
    cursor.execute("UPDATE courses SET enrolled_students = enrolled_students + 1 WHERE course_id = %s", (course_id,))
    conn.commit()
    return "message : 課程添加成功"


# 退選課程
@app.route('/drop_course', methods=['POST'])
def drop_course():
    student_id = session['student_id']
    course_id = request.form['course_id']
    conn = db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT credits FROM courses WHERE course_id = %s", (course_id,))
    course_data = cursor.fetchone()
    if not course_data:
        return "error: 無法找到該課程。"

    course_credits = course_data[0]

    # 檢查學生目前的總學分
    cursor.execute("""
        SELECT SUM(c.credits) 
        FROM courses c 
        JOIN enrollments e ON c.course_id = e.course_id 
        WHERE e.student_id = %s
    """, (student_id,))
    credits_data = cursor.fetchone()
    total_credits = credits_data[0] or 0

    # 檢查退課後學分是否低於最低要求
    if total_credits - course_credits < 9:
        return "error: 退課後學分將低於最低要求。"
    
    # 檢查課程是否必修
    cursor.execute("SELECT is_required FROM courses WHERE course_id = %s", (course_id,))
    is_required = cursor.fetchone()[0]
    if is_required:
        return "warning : 您正試圖退出一門必修課程。"

    # 更新選課記錄和課程已選學生人數
    cursor.execute("DELETE FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    cursor.execute("UPDATE courses SET enrolled_students = enrolled_students - 1 WHERE course_id = %s", (course_id,))
    conn.commit()
    return "message : 課程已成功退出"

# 關注課程
#@app.route('/watch_course', methods=['POST'])
#def watch_course():
#   return '未知錯誤發生'

# 列出課程
@app.route('/view_courses', methods=['POST'])
def view_courses():
    student_id = session['student_id']
    conn = db_connection()
    cursor = conn.cursor()

    query = """
    SELECT c.course_id, c.course_name, c.course_time 
    FROM courses c
    JOIN enrollments e ON c.course_id = e.course_id
    WHERE e.student_id = %s
    ORDER BY c.course_time
    """
    cursor.execute(query, (student_id,))
    courses = cursor.fetchall()

    if not courses:
        return "error : 此學生未找到課程。"
    return render_template('courses.html', courses=courses)

if __name__ == '__main__':
    app.run(debug=True)

