CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    credits_taken INT DEFAULT 0
);
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    capacity INT,
    enrolled_students INT DEFAULT 0,
    is_required BOOLEAN,
    credits INT,
    course_time VARCHAR(255)
);
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    watching BOOLEAN NOT NULL DEFAULT FALSE
    course_id INT,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
); 
INSERT INTO students (name, department, credits_taken) VALUES
('Alice Wang', 'Computer Science', 18),
('Bob Lee', 'Electrical Engineering', 22),
('Carol Wu', 'Computer Science', 20); 
INSERT INTO courses (course_name, department, capacity, enrolled_students, is_required, credits, course_time) VALUES
('Introduction to Programming', 'Computer Science', 40, 0, TRUE, 3, 'Monday 9AM-12PM'),
('Data Structures', 'Computer Science', 35, 0, TRUE, 3, 'Wednesday 9AM-12PM'),
('Circuit Analysis', 'Electrical Engineering', 30, 0, TRUE, 4, 'Tuesday 2PM-5PM'),
('Digital Systems', 'Electrical Engineering', 30, 0, FALSE, 4, 'Thursday 2PM-5PM');
