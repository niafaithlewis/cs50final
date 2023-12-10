# BIOBOSS

## DESIGN CHOICES

### Implementation Overview
Python with Flask = we chose to use python with a Flask framework because it is very suitable for creating a web-based app, as we had in mind. Python with Flask allowed us to do all of the backend development including:
- setting up routes for each page on the website based on the buttons that were clicked by the user (e.g. hompage, register, login, quiz)
- restrict users to only 3 page options (home, logic, register) until they registered and/or logged in when the Quiz and logout pages would be shown to them
- implement functions much easier using python's libraries, such as collecting the user's password from a form and using the hash function to privatize the user's sensitive information
- easy integration with frontend elements made with HTML and Jinja

Jinja = While Jinja was not strictly necessary to be used, we thought that it was a lot more efficient in the end to create templates that we could use in the HTML displays of our quizzes, that we could link to a tables which stored out questions and answers. Then, it would be much easier to add quizzes, questions and answers, instead of hard-coding them into the html pages. Jinja allowed our quiz page displays to be dynamic. We also used Jinja templating for displaying our navigation bar, so that it would be present in all of the web pages without coding each element of the navigation bar in every html page we created.

SQL = As mentioned for Jinja above, storing our questions and answers in tables proved to be much more efficient than coding them directly into HTML, so SQL was necessary for creating the database to store and link them all in. We also needed SQL to be able to store users' information (username, password, user_id) after they registered, so that we could keep track of their individual scores on quizzes.The bioboss database contains 6 tables:
answers, questions, quizzes, users, users_response and user_quiz_scores.

HTML = We needed HTML to be able to display each of our webpages. We tried to be creative in the way that our quiz oages were rendered. Since the topics of our quizzes are specified by id (e.g. geology is quiz_id = 1, genetics is quiz_id = 2, etc.) we wanted to figure out a way to not have to create individual html pages for each quiz by id. We did not want it to be static. So, we used Jinja to be able to connect each quiz_id to a certain link, and that link would inform each HTML page of which quiz information to display.     example: action="{{ url_for ('submit_quiz', quiz_id=quiz_id) }}" would be in our "quiz_page.html" that actaully displays the quiz information and "a href="{{ url_for('quiz_page', quiz_id=3) }}">Plants" would be in our "quiz.html" page that stores the links to all available quizzes by ID.

### Difficulties
During development, some of the difficulties we faced were:
- using Bootstrap styling in conjunction with our own stylesheet: This was difficult because often bootstraps style would override our own in places in the website where we had specified that certain elements be a certain style. We learned about the limitations of using !important tags in CSS, and how to achieve some styles without using Bootstrap.

- incrementing scores: Because of how our database was set up, we couldn't match user's scores with their user_id by the specific quiz they had completed. This led to difficulty keeping track of the scores we calculated based on their question_id and if that question_id had a 0 or 1 in their is_correct Boolean column. Eventually, we were able to fix this by creating another table where we could store users' scores connected to quiz_id, because modifying the previous users table would mean many modificiations to our previous functions.


## Authors:
### Nia Lewis
### Yusuf Yildirim
