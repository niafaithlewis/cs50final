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

def get_db_connection():
    conn =sqlite3.connect('bioboss_db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")

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
            db.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)"), (username, username, hash_pass)
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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
















