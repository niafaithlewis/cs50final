# BIOBOSS

This is our final project to end off the Fall semester of CS50

## Overview of the project

### Video Demo: link

### Description:
Our final project is a website trivia game that allows users to play quizzes, get scores and learn some bilogy facts along the way if they didn't know them already. Currently, the user can choose from 3 different biology topics for the quiz (plants, genetics and geology), but the set up fo the quiz display is dynamic, not hard-coded. The questions and answers are stored in a database, so more quizzes can be added relatively easily.

## For the implementation of this project we used
- python (for the backend),
- flask web framework,
- CSS - for style ,
- SQL - for storing tables (database) and jinja templating (for dynamic HTML pages)

## Getting Started

### SQL

All of our quiz information, as said before is stored in the bioboss database (bioboss.db), along with user information.

The bioboss.db is required to run this website, since most functions first requre access to the database to run. Most routes must interact with the database, either for modification or acessing information purposes, so this bioboss.db should be sotred in the same directory as the python file.

The bioboss database contains 6 tables:
answers, questions, quizzes, users, users_response and user_quiz_scores. Ensure all tables are present in the database before running the web app.

### cs50.dev
cs50.dev is sufficient for running this web app, since it was used to create it. Follow the usage directions inf the section below if using cs50.dev to run this program.

## Usage
1. Download the bioboss.zip file
    - This should include the following folders and the corresponding files:
        - bioboss.db
        - bioboss.py
        - DESIGN.md
        - READme.md
        - static/
        - static/genetics.png
        - static/plants.png
        - static/style.css
        - static/geology.png
        - templates/
        - templates/quiz.html
        - templates/quiz_page.html
        - templates/register.html
        - templates/logout.html
        - templates/submit_quiz.html
        - templates/login.html
        - templates/index.html
        - templates/navbar.html
        - templates/user_profile.html

2. If bioboss folder has been downloaded, drag and drop the file in your file explorer in cs50.dev
3. Clear the working directory
4. Unzip file by running: unzip bioboss.zip.
5. Remove the zip file with rm bioboss.zip.
6. Enter the Bioboss directory by: cd bioboss
7. Run ls to check that you have all the files listed above.
8. Run the following command in the terminal: python bioboss.py
9. Then run: export FLASK_APP=bioboss
10. Finally, run: flask run
11. Click the link generated
12. Register, then log in to be able to access the quiz modules.
13. Have fun playing Bioboss!




Authors
Nia Faith Lewis
Yusuf Yildirim


