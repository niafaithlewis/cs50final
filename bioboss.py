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
    conn =sqlite3.connect('bioboss.db')
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
                questions.question_id
        """
        rows = db.execute(query, (quiz_id,)).fetchall()

        # Organize data into a dictionary
        quiz = {
            'topic': None,
            'description': None,
            'questions': []
        }

        current_question = None

        for row in rows:
            quiz_id, topic, description, question_id, question_text, answer_id, answer_text, is_correct = row

            if quiz['topic'] is None:
                quiz['topic'] = topic
                quiz['description'] = description

            # If this is a new question, create a new question dictionary and append it to the quiz
            if not current_question or current_question['question_id'] != question_id:
                current_question = {
                    'question_id': question_id,
                    'question_text': question_text,
                    'answers': []
                }
                quiz['questions'].append(current_question)

            # Create a new answer dictionary and append it to the current question's answers
            answer = {
                'answer_id': answer_id,
                'answer_text': answer_text,
                'is_correct': is_correct
            }
            current_question['answers'].append(answer)

        db.close()
        return quiz
    except sqlite3.Error as e:
        print("Error fetching quiz with ID {quiz_id}: {e}")
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

#Tracking User's Score

# Retrieving correct answers


#Calculating user's score


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation =request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("Must provide username and password")
            return redirect("/register")
        if password !=confirmation:
            flash("Passwords do not match")
            return redirect("/register")
        hash_pass = generate_password_hash(password)

        try:
            db =get_db_connection()
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_pass))
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
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        db.close()

        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid username and/or password")
            return redirect("/login")

        session["user_id"] =user["user_id"]

        return redirect ("/")
    else:
        return render_template("login.html")

@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")














































