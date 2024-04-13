from flask import Flask, request, jsonify, render_template
import mysql.connector

app = Flask(__name__)

# 設定資料庫連接
def db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  # XAMPP 預設用戶名
            password="",  # XAMPP 預設密碼通常為空
            database="university"
        )
    except mysql.connector.Error as error:
        print("Failed to connect to MySQL: {}", format(error))
    return conn

# 首頁
@app.route('/')
def index():
    return render_template('index.html')

# 加選課程
@app.route('/add_course', methods=['POST'])
def add_course():
    student_id = request.form['student_id']
    course_id = request.form['course_id']
    conn = db_connection()
    cursor = conn.cursor()

    # 檢查課程是否在學生所在的系
    cursor.execute("SELECT department FROM courses WHERE course_id = %s", (course_id,))
    course_dept_result = cursor.fetchone()
    if not course_dept_result:
        return jsonify({"error": "没有找到该课程。"}), 404

    course_dept = course_dept_result[0]
    
    cursor.execute("SELECT department FROM students WHERE student_id = %s", (student_id,))
    student_dept_result = cursor.fetchone()
    if not student_dept_result:
        return jsonify({"error": "没有找到该学生的资料。"}), 404

    student_dept = student_dept_result[0]
    if course_dept != student_dept:
        return jsonify({"error": "学生只能选择本系课程。"}), 400

    # 檢查課程是否已滿
    cursor.execute("SELECT capacity, enrolled_students FROM courses WHERE course_id = %s", (course_id,))
    capacity, enrolled_students = cursor.fetchone()
    if enrolled_students >= capacity:
        return jsonify({"error": "該課程已滿。"}), 400

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
        return jsonify({"error": "該課程與您現有的課程時間衝突。"}), 400

    # 檢查學分上限
    cursor.execute("SELECT SUM(c.credits) FROM courses c JOIN enrollments e ON c.course_id = e.course_id WHERE e.student_id = %s", (student_id,))
    total_credits = cursor.fetchone()[0] or 0
    cursor.execute("SELECT credits FROM courses WHERE course_id = %s", (course_id,))
    course_credits = cursor.fetchone()[0]
    if total_credits + course_credits > 30:
        return jsonify({"error": "選擇此課程將超出學分限制。"}), 400

    # 注冊課程
    cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
    cursor.execute("UPDATE courses SET enrolled_students = enrolled_students + 1 WHERE course_id = %s", (course_id,))
    conn.commit()
    return jsonify({"message": "課程添加成功"})


# 退選課程
@app.route('/drop_course', methods=['POST'])
def drop_course():
    student_id = request.form['student_id']
    course_id = request.form['course_id']
    conn = db_connection()
    cursor = conn.cursor()

    # 檢查課程是否必修
    cursor.execute("SELECT is_required FROM courses WHERE course_id = %s", (course_id,))
    is_required = cursor.fetchone()[0]
    if is_required:
        return jsonify({"warning": "您正試圖退出一門必修課程。"}), 400

    # 更新選課記錄和課程已選學生人數
    cursor.execute("DELETE FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    cursor.execute("UPDATE courses SET enrolled_students = enrolled_students - 1 WHERE course_id = %s", (course_id,))
    conn.commit()

    return jsonify({"message": "課程已成功退出"})


# 列出課程
@app.route('/list_courses')
def list_courses():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_id, course_name, available_slots FROM courses")
    courses = cursor.fetchall()
    return render_template('courses.html', courses=courses)

if __name__ == '__main__':
    app.run(debug=True)
