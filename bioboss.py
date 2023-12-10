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
                quiz_id,
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
        return render_template("quiz_page.html", quiz=quiz, quiz_id=quiz_id)
    else:
        return "Quiz not found."

@app.route("/user_profile")
def user_profile():
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect("/login")

    user_id = session['user_id']

    # Fetch user data from the database
    user_data = get_user_data(user_id)

    if not user_data:
        # Handle case where user data is not found
        return "User not found", 404

    # Render the user profile template with user data
    return render_template("user_profile.html", user=user_data)


def insert_user_response(user_id, question_id, answer_id, is_correct):
    try:
        db = get_db_connection()

        query = """
            INSERT INTO users_response (user_id, question_id, answer_id, is_correct)
            VALUES (?, ?, ?, ?)
        """
        result = db.execute(query, (user_id, question_id, answer_id, is_correct))

        response_id = result.lastrowid

        db.commit()
        db.close()

        print("User response inserted successfully.")
        return response_id
    except sqlite3.Error as e:
        print(f"Error inserting user response: {e}")


def get_user_data(user_id):
    db = get_db_connection()
    user = db.execute("SELECT score FROM users WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return user if user else None


# Calculating user's score
def calculate_user_score(user_id):
    try:
        db = get_db_connection()
        query = """
            SELECT
                questions.question_id,
                answers.answer_id,
                users_response.is_correct
            FROM
                users_response
            JOIN
                questions ON users_response.question_id = questions.question_id
            JOIN
                answers ON users_response.answer_id = answers.answer_id
            WHERE
                users_response.user_id = ?
        """
        rows = db.execute(query, (user_id,)).fetchall()

        score = 0

        for row in rows:
            is_correct = row['is_correct']
            score += 1 if is_correct else 0


        update_query = "UPDATE users SET score = ? WHERE user_id = ?"
        db.execute(update_query, (score, user_id))
        db.commit()

        db.close()
        return score
    except sqlite3.Error as e:
        print(f"Error calculating user's score: {e}")
        return None

def check_answer(question_id, answer_id):
    db = get_db_connection()
    query = "SELECT is_correct FROM answers WHERE question_id = ? AND answer_id = ?"
    correct_answer = db.execute(query, (question_id, answer_id)).fetchone()

    return correct_answer['is_correct'] if correct_answer else False


@app.route("/submit_quiz/<int:quiz_id>", methods=["POST"])
def submit_quiz(quiz_id):
    # Assume user_id is stored in session
    if 'user_id' in session:
        user_id = session['user_id']

        quiz = get_quiz_by_id(quiz_id)

        # Check if the user has attempted a quiz before
        last_attempted_quiz_id = session.get('last_attempted_quiz_id')

        if last_attempted_quiz_id is not None and last_attempted_quiz_id != quiz_id:
            # Reset the user's score to zero if they are attempting a new quiz
            reset_user_score(user_id)

        # Update the last attempted quiz_id in the session
        session['last_attempted_quiz_id'] = quiz_id

        user_responses = {}
        for question in quiz['questions']:
            answer_id = int(request.form.get(f"answer_for_question_{question['question_id']}", -1))

            is_correct = check_answer(question['question_id'], answer_id)

            response_id = insert_user_response(user_id, question['question_id'], answer_id, is_correct)

            user_responses[question['question_id']] = {
                'response_id': response_id,
                'user_answer': answer_id,
                'is_correct': is_correct
            }

        score = calculate_user_score(user_id)
        return render_template("submit_quiz.html", quiz_id=quiz_id, user_id=user_id, score=score, user_responses=user_responses)
    else:
        return redirect("/login")

def reset_user_score(user_id):
    print("Resetting user score...")
    db = get_db_connection()
    db.execute("UPDATE users SET score = 0 WHERE user_id = ?", (user_id,))
    db.close()
    print("User score reset successfully.")


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
