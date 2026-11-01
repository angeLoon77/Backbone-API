import os
import psycopg2
import datetime
import bcrypt
from dotenv import load_dotenv

load_dotenv()

EXERCISES = [
    # chest
    ("Bench Press", "chest"),
    ("Bench Press Smith Machine", "chest"),
    ("Dumbbell Press", "chest"),
    ("Incline Press", "chest"),
    ("Smith Incline Press", "chest"),
    ("Dumbbell Incline Press", "chest"),
    ("Decline Chest Press", "chest"),
    ("Machine Chest Press", "chest"),
    ("Pec Deck", "chest"),
    ("Dumbbell Fly", "chest"),
    ("Incline Dumbbell Fly", "chest"),
    ("Cable Fly", "chest"),
    ("High To Low", "chest"),
    ("Low To High", "chest"),
    ("Chest Dips", "chest"),
    # legs
    ("Leg Press", "legs"),
    ("Squat", "legs"),
    ("Smith Machine Squat", "legs"),
    ("Front Squat", "legs"),
    ("Hack Squat", "legs"),
    ("Bulgarian Split Squat", "legs"),
    ("Lunge", "legs"),
    ("Walking Lunge", "legs"),
    ("Romanian Deadlift", "legs"),
    ("Stiff Leg Deadlift", "legs"),
    ("Seated Leg Curl", "legs"),
    ("Lying Leg Curl", "legs"),
    ("Leg Extension", "legs"),
    ("Hip Adduction", "legs"),
    # glutes
    ("Hip Thrust", "glutes"),
    ("Glute Bridge", "glutes"),
    ("Hip Abduction", "glutes"),
    ("Cable Kickback", "glutes"),
    ("Glute Kickback Machine", "glutes"),
    # calves
    ("Calf Raise", "calves"),
    ("Seated Calf Raise", "calves"),
    ("Standing Calf Raise", "calves"),
    ("Donkey Calf Raise", "calves"),
    # shoulders
    ("Shoulder Press", "shoulders"),
    ("Dumbbell Shoulder Press", "shoulders"),
    ("Machine Shoulder Press", "shoulders"),
    ("Military Press", "shoulders"),
    ("Arnold Press", "shoulders"),
    ("Lateral Raise", "shoulders"),
    ("Cable Lateral Raise", "shoulders"),
    ("Front Raise", "shoulders"),
    ("Rear Delt Fly", "shoulders"),
    ("Reverse Pec Deck", "shoulders"),
    ("Face Pull", "shoulders"),
    ("Upright Row", "shoulders"),
    # back
    ("Deadlift", "back"),
    ("Rack Pull", "back"),
    ("Pull-Up", "back"),
    ("Chin-Up", "back"),
    ("Lat Pulldown Wide", "back"),
    ("Front Pulldown", "back"),
    ("Lat Pulldown Close", "back"),
    ("Straight Arm Pulldown", "back"),
    ("T-Bar Row", "back"),
    ("Seated Row", "back"),
    ("Machine Row", "back"),
    ("Chest Supported Row", "back"),
    ("Bent Over Row", "back"),
    ("One Arm Row", "back"),
    ("Pullover", "back"),
    ("Back Extension", "back"),
    # biceps
    ("Barbell Curl", "biceps"),
    ("EZ Bar Curl", "biceps"),
    ("Incline Dumbbell Curl", "biceps"),
    ("Dumbbell Curl", "biceps"),
    ("Alternate Hammer Curl", "biceps"),
    ("Hammer Curl", "biceps"),
    ("Preacher Curl", "biceps"),
    ("Cable Curl", "biceps"),
    ("Concentration Curl", "biceps"),
    ("Spider Curl", "biceps"),
    # triceps
    ("Triceps Pushdown", "triceps"),
    ("Triceps Pulley", "triceps"),
    ("Skull Crusher", "triceps"),
    ("Bench Dips", "triceps"),
    ("Triceps Dips", "triceps"),
    ("Close Grip Bench Press", "triceps"),
    ("Overhead Triceps Extension", "triceps"),
    ("Dumbbell Overhead Triceps Extension", "triceps"),
    ("Triceps Extension", "triceps"),
    ("Triceps Kickback", "triceps"),
    # forearms
    ("Wrist Curl", "forearms"),
    ("Reverse Wrist Curl", "forearms"),
    ("Reverse Curl", "forearms"),
    # core
    ("Cable Crunch", "core"),
    ("Hanging Leg Raise", "core"),
    # traps
    ("Shrug", "traps"),
    ("Dumbbell Shrug", "traps"),
]


# CONNECTION

def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not found on .env")
    return psycopg2.connect(database_url)


# CREATE TABLES 

def init_db():
    create_exercise_table()
    create_users_table()
    create_prs_table()
    add_exercises()


def create_exercise_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exercises
        (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        muscle_group TEXT NOT NULL
        )
        """)
    conn.commit()
    cur.close()
    conn.close()


def create_users_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users
        (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
        )
        """)
    conn.commit()
    cur.close()
    conn.close()


def create_prs_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prs
        (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        exercise_id INTEGER NOT NULL,
        weight DOUBLE PRECISION NOT NULL,
        reps INTEGER NOT NULL,
        date DATE NOT NULL,
        FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """)
    conn.commit()
    cur.close()
    conn.close()


def add_exercises():
    conn = get_connection()
    cur = conn.cursor()
    for name, group in EXERCISES:
        cur.execute(
            "INSERT INTO exercises (name, muscle_group) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (name, group),
        )
    conn.commit()
    cur.close()
    conn.close()


# USERS

def register_user(username, password):
    username = username.strip().lower()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, hash) VALUES (%s, %s) RETURNING id",
            (username, password_hash),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Insert did not return an id")
        user_id = row[0]
        conn.commit()
        cur.close()
        return user_id
    except psycopg2.IntegrityError:
        conn.rollback()
        raise ValueError("Username already exists")
    finally:
        conn.close()


def login(username, password):
    username = username.strip().lower()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, hash FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if row is None:
        return None

    user_id, password_hash = row
    if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
        return user_id
    return None


# PRS

def get_prs(user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT exercises.name, prs.weight, prs.reps
            FROM prs JOIN exercises ON prs.exercise_id = exercises.id
            WHERE prs.user_id = %s
            ORDER BY prs.weight, prs.reps
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    prs = {}
    for name, weight, reps in rows:
        prs[name.lower()] = {"weight": weight, "reps": reps}
    return prs


def add_pr(user_id, exercise_id, weight, reps, date):
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date)
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO prs (user_id, exercise_id, weight, reps, date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user_id, exercise_id, weight, reps, date),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Insert did not return an id")
        pr_id = row[0]
        conn.commit()
        cur.close()
        return pr_id
    except psycopg2.IntegrityError:
        conn.rollback()
        raise ValueError("Invalid Data: user or exercise not found, or a required field is missing")
    finally:
        conn.close()

def delete_pr(pr_id, user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM prs WHERE id = %s AND user_id = %s",
            (pr_id, user_id),
        )
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()