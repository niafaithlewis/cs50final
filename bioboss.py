import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    return render_template("index.html")


def get_db_connection():
    conn = sqlite3.connect("bioboss.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_quiz_by_id(quiz_id):
    try:
        db = get_db_connection()
        query = """
            SELECT
                quizzes.quiz_id,
                quizzes.topic,
                quizzes.description,
                questions.question_id,
                questions.question_text,
                answers.answer_id,
                answers.answer_text,
                answers.is_correct
            FROM
                quizzes
            JOIN
                questions ON quizzes.quiz_id = questions.quiz_id
            JOIN
                answers ON questions.question_id = answers.question_id
            WHERE
                quizzes.quiz_id = ?
            ORDER BY
                questions.question_id, answers.answer_id
        """
        rows = db.execute(query, (quiz_id,)).fetchall()

        # Initialize quiz dictionary with quiz_id
        quiz = {"quiz_id": quiz_id, "topic": None, "description": None, "questions": []}

        current_question = None

        for row in rows:
            (
                qz_id,  # Use a different variable name to avoid confusion with the parameter quiz_id
                topic,
                description,
                question_id,
                question_text,
                answer_id,
                answer_text,
                is_correct,
            ) = row

            if quiz["topic"] is None:
                quiz["topic"] = topic
                quiz["description"] = description

            # If this is a new question, create a new question dictionary and append it to the quiz
            if not current_question or current_question["question_id"] != question_id:
                current_question = {
                    "question_id": question_id,
                    "question_text": question_text,
                    "answers": [],
                }
                quiz["questions"].append(current_question)

            # Create a new answer dictionary and append it to the current question's answers
            answer = {
                "answer_id": answer_id,
                "answer_text": answer_text,
                "is_correct": is_correct,
            }
            current_question["answers"].append(answer)

        db.close()
        return quiz
    except sqlite3.Error as e:
        print(f"Error fetching quiz with ID {quiz_id}: {e}")
        return None


# Displaying quiz page
@app.route("/quiz/<int:quiz_id>")
def quiz_page(quiz_id):
    # Get details from the database based on quiz_id
    quiz = get_quiz_by_id(quiz_id)
    if quiz:
        return render_template("quiz_page.html", quiz=quiz)
    else:
        return "Quiz not found."

@app.route("/user_profile")
def user_profile():
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch user data from the database
    user_data = get_user_data(user_id)

    if not user_data:
        # Handle case where user data is not found
        return "User not found", 404

    # Render the user profile template with user data
    return render_template("user_profile.html", user=user_data)

def get_user_data(user_id):
    db = get_db_connection()
    user = db.execute("SELECT *, cumulative_score FROM users WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return user if user else None

@app.route("/submit_quiz/<int:quiz_id>", methods=["POST"])
def submit_quiz(quiz_id):
    # Assume user_id is stored in session
    user_id = session["user_id"]

    # Retrieve user's answers from the form submission
    user_answers = request.form.to_dict()

    # Get correct answers from the database
    correct_answers = get_correct_answers(quiz_id)

    # Calculate score for the current quiz and track results
    score = 0
    user_results = {}  # Store question results

    for question_id, user_answer in user_answers.items():
        if correct_answers.get(question_id) == user_answer:
            score += 1
            user_results[question_id] = {'user_answer': user_answer, 'correct': True}
        else:
            user_results[question_id] = {'user_answer': user_answer, 'correct': False}

    db = get_db_connection()
    # Store the score in the database and update cumulative score
    user = db.execute("SELECT cumulative_score FROM users WHERE user_id = ?", (user_id,)).fetchone()
    current_cumulative_score = user["cumulative_score"] if user else 0

    new_cumulative_score = current_cumulative_score + score
    db.execute("UPDATE users SET cumulative_score = ? WHERE user_id = ?", (new_cumulative_score, user_id))
    db.execute("INSERT INTO quiz_results (user_id, quiz_id, score) VALUES (?, ?, ?)", (user_id, quiz_id, score))
    db.commit()

    # Fetch detailed question and answer information
    detailed_results = get_detailed_results(quiz_id, user_results)

    db.close()

    # Redirect to a results page with detailed results
    return render_template("quiz_results.html", score=score, results=detailed_results)

def get_correct_answers(quiz_id):
    db = get_db_connection()
    try:
        query = """
            SELECT
                questions.question_id,
                answers.answer_id
            FROM
                answers
            JOIN
                questions ON answers.question_id = questions.question_id
            WHERE
                questions.quiz_id = ? AND answers.is_correct = 1
        """
        rows = db.execute(query, (quiz_id,)).fetchall()
        correct_answers = {str(row['question_id']): str(row['answer_id']) for row in rows}
        return correct_answers
    except sqlite3.Error as e:
        print(f"Error fetching correct answers for quiz ID {quiz_id}: {e}")
        return {}
    finally:
        db.close()


def get_detailed_results(quiz_id, user_results):
    db = get_db_connection()
    detailed_results = []
    for question_id, result in user_results.items():
        question = db.execute("SELECT question_text FROM questions WHERE question_id = ?", (question_id,)).fetchone()
        correct_answer = db.execute("SELECT answer_text FROM answers WHERE question_id = ? AND is_correct = 1", (question_id,)).fetchone()
        user_answer_text = db.execute("SELECT answer_text FROM answers WHERE answer_id = ?", (result['user_answer'],)).fetchone()

        if question and correct_answer and user_answer_text:
            detailed_results.append({
                'question': question['question_text'],
                'correct_answer': correct_answer['answer_text'],
                'user_answer': user_answer_text['answer_text'],
                'is_correct': result['correct']
            })
        else:
            print(f"Error: Missing data for question_id {question_id}")
    db.close()
    return detailed_results


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("Must provide username and password")
            return redirect("/register")
        if password != confirmation:
            flash("Passwords do not match")
            return redirect("/register")
        hash_pass = generate_password_hash(password)

        try:
            db = get_db_connection()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_pass),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username already taken")
            return redirect("/register")
        finally:
            db.close()

        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please provide username and password")
            return redirect("/login")

        db = get_db_connection()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        db.close()

        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid username and/or password")
            return redirect("/login")

        session["user_id"] = user["user_id"]

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
