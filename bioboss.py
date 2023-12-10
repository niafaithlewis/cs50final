import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from functools import wraps

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

def update_cumulative_score(user_id, additional_score):
    try:
        db = get_db_connection()
        current_cumulative_score = db.execute("SELECT cumulative_score FROM users WHERE user_id = ?", (user_id,)).fetchone()
        current_cumulative = current_cumulative_score['cumulative_score'] if current_cumulative_score['cumulative_score'] is not None else 0
        additional_score = additional_score if additional_score is not None else 0

        new_cumulative_score = current_cumulative + additional_score

        db.execute("UPDATE users SET cumulative_score = ? WHERE user_id = ?", (new_cumulative_score, user_id))
        db.commit()
        db.close()
    except sqlite3.Error as e:
        print(f"Error updating cumulative score for user_id {user_id}: {e}")

def get_scoreboard():
    db = get_db_connection()
    users = db.execute(
        "SELECT username, cumulative_score FROM users ORDER BY cumulative_score DESC LIMIT 20"
    ).fetchall()
    db.close()
    return users


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def reset_current_quiz_score(user_id):
    try:
        db = get_db_connection()
        db.execute("UPDATE users SET score = 0 WHERE user_id = ?", (user_id,))
        db.commit()
        db.close()
        print("Current quiz score reset successfully for user_id:", user_id)
    except sqlite3.Error as e:
        print(f"Error resetting current quiz score for user_id {user_id}: {e}")

def has_user_answered_question(user_id, question_id):
    db = get_db_connection()
    response = db.execute("SELECT * FROM users_response WHERE user_id = ? AND question_id = ?", (user_id, question_id)).fetchone()
    db.close()
    return response is not None


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
                questions.explanation,
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

        quiz = {"quiz_id": quiz_id, "topic": None, "description": None, "questions": []}
        current_question = None

        for row in rows:
            (
                quiz_id,
                topic,
                description,
                question_id,
                question_text,
                explanation,  # Extract the explanation
                answer_id,
                answer_text,
                is_correct,
            ) = row

            if quiz["topic"] is None:
                quiz["topic"] = topic
                quiz["description"] = description

            if not current_question or current_question["question_id"] != question_id:
                current_question = {
                    "question_id": question_id,
                    "question_text": question_text,
                    "explanation": explanation,  # Add the explanation
                    "answers": []
                }
                quiz["questions"].append(current_question)

            answer = {
                "answer_id": answer_id,
                "answer_text": answer_text,
                "is_correct": is_correct
            }
            current_question["answers"].append(answer)

        db.close()
        return quiz
    except sqlite3.Error as e:
        print(f"Error fetching quiz with ID {quiz_id}: {e}")
        return None



@app.route("/quiz/<int:quiz_id>")
def quiz_page(quiz_id):
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect("/login")

    user_id = session['user_id']

    # Reset score if the user is retaking the same quiz
    if session.get('last_attempted_quiz_id') == quiz_id:
        reset_current_quiz_score(user_id)
        print(f"Score reset for user_id {user_id} on retaking quiz {quiz_id}")

    # Update the last attempted quiz_id in the session
    session['last_attempted_quiz_id'] = quiz_id

    # Get details from the database based on quiz_id
    quiz = get_quiz_by_id(quiz_id)
    if quiz:
        return render_template("quiz_page.html", quiz=quiz, quiz_id=quiz_id)
    else:
        return "Quiz not found."




@app.route("/user_profile")
def user_profile():
    if 'user_id' not in session:
        return redirect("/login")

    user_id = session['user_id']
    db = get_db_connection()
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    db.close()

    if not user:
        return "User not found", 404

    return render_template("user_profile.html", user=user)




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
    user = db.execute("SELECT username, cumulative_score FROM users WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return user if user else None



# Calculating user's score
def calculate_user_score(user_id, quiz_id):
    try:
        db = get_db_connection()
        query = """
            SELECT SUM(is_correct) as score
            FROM (
                SELECT
                    users_response.is_correct,
                    ROW_NUMBER() OVER (PARTITION BY users_response.question_id ORDER BY users_response.timestamp ASC) as rn
                FROM users_response
                JOIN questions ON users_response.question_id = questions.question_id
                WHERE users_response.user_id = ? AND questions.quiz_id = ?
            )
            WHERE rn = 1
        """
        score = db.execute(query, (user_id, quiz_id)).fetchone()['score']
        db.close()
        return score or 0
    except sqlite3.Error as e:
        print(f"Error calculating user's score: {e}")
        return 0




def check_answer(question_id, answer_id):
    db = get_db_connection()
    query = "SELECT is_correct FROM answers WHERE question_id = ? AND answer_id = ?"
    correct_answer = db.execute(query, (question_id, answer_id)).fetchone()

    return correct_answer['is_correct'] if correct_answer else False


@app.route("/submit_quiz/<int:quiz_id>", methods=["POST"])
def submit_quiz(quiz_id):
    if 'user_id' not in session:
        return redirect("/login")

    user_id = session['user_id']
    quiz = get_quiz_by_id(quiz_id)

    if quiz:
        user_responses = {}
        correct_answers = {}
        for question in quiz['questions']:
            answer_id = int(request.form.get(f"answer_for_question_{question['question_id']}", -1))

            # Check if user has already answered this question
            if not has_user_answered_question(user_id, question['question_id']):
                is_correct = check_answer(question['question_id'], answer_id)
                response_id = insert_user_response(user_id, question['question_id'], answer_id, is_correct)

                user_responses[question['question_id']] = {
                    'question_text': question['question_text'],
                    'user_answer': answer_id,
                    'is_correct': is_correct
                }

            # Find the correct answer for this question
            correct_answer = next((a for a in question['answers'] if a['is_correct']), None)
            correct_answers[question['question_id']] = {
                'answer_text': correct_answer['answer_text'] if correct_answer else "No answer",
                'explanation': question['explanation']
            }

        # Recalculate score (only considering first response for each question)
        current_quiz_score = calculate_user_score(user_id, quiz_id)

        # Update cumulative score only if this is the first submission for this quiz attempt
        if session.get('last_score_update_quiz_id') != quiz_id:
            update_cumulative_score(user_id, current_quiz_score)
            session['last_score_update_quiz_id'] = quiz_id

        return render_template("quiz_results.html", quiz_id=quiz_id, user_id=user_id, score=current_quiz_score, user_responses=user_responses, correct_answers=correct_answers)
    else:
        flash("Quiz not found.")
        return redirect("/quiz")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("Must provide username, password, and confirm password", "error")
            return redirect("/register")

        if password != confirmation:
            flash("Passwords do not match", "error")
            return redirect("/register")

        hash_pass = generate_password_hash(password)

        try:
            db = get_db_connection()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_pass)
            )
            db.commit()
            flash("Registration successful! Welcome to BioBoss!", "success")
        except sqlite3.IntegrityError:
            flash("Username already taken", "error")
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
            flash("Please provide username and password", "error")
            return redirect("/login")

        db = get_db_connection()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        db.close()

        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid username and/or password", "error")
            return redirect("/login")

        session["user_id"] = user["user_id"]
        return redirect("/")
    else:
        return render_template("login.html")



@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Fetch the current password hash from the database
        user_id = session["user_id"]
        db = get_db_connection()  # Get the database connection
        user_data = db.execute("SELECT password FROM users WHERE user_id = ?", (user_id,)).fetchone()
        db.close()  # Close the database connection

        if not user_data or not check_password_hash(user_data["password"], old_password):
            flash("Invalid old password", "error")
            return render_template("change_password.html")

        if not new_password or new_password != confirmation:
            flash("New passwords don't match or are invalid", "error")
            return render_template("change_password.html")

        # Update the password in the database
        new_password_hash = generate_password_hash(new_password)
        db = get_db_connection()  # Get the database connection
        db.execute("UPDATE users SET password = ? WHERE user_id = ?", (new_password_hash, user_id))
        db.commit()
        db.close()  # Close the database connection

        flash("Password changed successfully!", "success")
        return redirect("/")

    else:
        return render_template("change_password.html")

@app.route("/scoreboard")
def scoreboard():
    users = get_scoreboard()
    return render_template("scoreboard.html", users=users)

# Make sure the upload folder exists
UPLOAD_FOLDER = 'static/profile_pics'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/update_profile_pic", methods=["POST"])
@login_required
def update_profile_pic():
    # Check if the post request has the file part
    if 'profile_pic' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['profile_pic']

    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Update user's profile picture in database
        user_id = session['user_id']
        db = get_db_connection()
        db.execute("UPDATE users SET profile_pic = ? WHERE user_id = ?", (filename, user_id))
        db.commit()
        db.close()

        flash('Profile picture updated successfully!')
        return redirect("/user_profile")

    flash('Invalid file type')
    return redirect("/user_profile")

@app.route("/logout")
def logout():
    session.pop('last_attempted_quiz_id', None)
    session.pop('last_score_update_quiz_id', None)
    session.clear()
    return redirect("/")

