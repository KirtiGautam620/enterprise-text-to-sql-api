import sqlite3
from pathlib import Path


DB_PATH = Path("data/beaver_sample.db")

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS departments")
cursor.execute("DROP TABLE IF EXISTS students")
cursor.execute("DROP TABLE IF EXISTS courses")
cursor.execute("DROP TABLE IF EXISTS enrollments")

cursor.execute("""
CREATE TABLE departments (
    dept_id INTEGER PRIMARY KEY,
    dept_name TEXT,
    school_name TEXT
)
""")

cursor.execute("""
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    student_name TEXT,
    dept_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    course_name TEXT,
    dept_id INTEGER,
    is_online INTEGER
)
""")

cursor.execute("""
CREATE TABLE enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    course_id INTEGER,
    dept_id INTEGER
)
""")

cursor.executemany(
    "INSERT INTO departments VALUES (?, ?, ?)",
    [
        (1, "Computer Science", "Engineering"),
        (2, "Mathematics", "Science"),
        (3, "Physics", "Science")
    ]
)

cursor.executemany(
    "INSERT INTO students VALUES (?, ?, ?)",
    [
        (1, "Asha", 1),
        (2, "Ravi", 1),
        (3, "Meera", 2),
        (4, "Kabir", 1),
        (5, "Naina", 3)
    ]
)

cursor.executemany(
    "INSERT INTO courses VALUES (?, ?, ?, ?)",
    [
        (101, "Algorithms", 1, 0),
        (102, "Databases", 1, 0),
        (103, "Online Python", 1, 1),
        (201, "Calculus", 2, 0),
        (301, "Quantum Mechanics", 3, 0)
    ]
)

cursor.executemany(
    "INSERT INTO enrollments VALUES (?, ?, ?, ?)",
    [
        (1, 1, 101, 1),
        (2, 2, 101, 1),
        (3, 4, 102, 1),
        (4, 3, 201, 2),
        (5, 5, 301, 3),
        (6, 1, 103, 1)
    ]
)

connection.commit()
connection.close()

print("Sample database created successfully.")