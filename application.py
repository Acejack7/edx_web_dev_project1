import os
from flask import Flask, render_template, request, session, g
# from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Check for environment variable and set database url
if not os.getenv("DATABASE_URL"):
    db_url = "postgres://hlojtlqjgyszxx:0061b447e9dbc04cc25bc341745c006ae869096665107472c5f1eccf5446ec1e@ec2-54-228-252-67.eu-west-1.compute.amazonaws.com:5432/d4mg4mean0buf7"
else:
    db_url = os.getenv("DATABASE_URL")

# Configure session to use filesystem
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

# Set up database
engine = create_engine(db_url)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == 'POST':
        session.pop('user', None)

        # Get form information.
        username = request.form.get("username")
        password = request.form.get("password")

        if 'register' in request.form:
            # Check if user provided any username and password
            if username == "" or password == "":
                return render_template("error_register.html", message="Username and password fields cannot be empty.")

            # Check if user exists.
            user_exist = db.execute("SELECT name FROM users WHERE name = :username", {"username": username}).fetchall()
            if user_exist != []:
                return render_template("error_register.html", message="Username already taken.")

            # Add user to database.
            db.execute("INSERT INTO users (name, password) VALUES (:username, :password)",
                       {"username": username, "password": password})
            db.commit()

            # Create a session and return successful registration
            session['user'] = username
            message = f"You are logged as {username}."

            return render_template("index2.html", message=message)

        elif 'login' in request.form:
            # Check db for user
            user = db.execute("SELECT * FROM users WHERE name = :username AND password = :password",
                              {"username": username, "password": password}).fetchall()

            # Check if user's password is correct
            try:
                pw_db = user[0]["password"]
            except IndexError:
                return render_template("error_login.html", message="Username or password is incorrect.")

            if password != pw_db:
                return render_template("error_login.html", message="Username or password is incorrect.")

            if user != []:
                session['user'] = username
                message = f"You are logged as {username}."
                return render_template("index2.html", message=message)
            else:
                return render_template("error_login.html", message="Username or password is incorrect.")

        elif 'logout' in request.form:
            message = "Succesfully logged out."
            return render_template("index.html", message=message)

    return render_template("index.html")


@app.route("/book_search", methods=["POST"])
def book_search():
    """Search for books and return the results"""

    # Get information about the book
    book_keywords = request.form.get("book_keywords")
    user_id = request.form.get("user_id")

    user = db.execute("SELECT * FROM users WHERE id = :user_id", {"user_id": user_id}).fetchall()

    book_results = db.execute("SELECT * FROM books WHERE isbn LIKE :b_key OR lower(title) LIKE :b_key OR lower(author) LIKE :b_key",
                              {"b_key": '%' + str(book_keywords) + '%'}).fetchall()

    return render_template("book_search.html", book_results=book_results, user=user)


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    user = session['user']

    message = ''

    book_info = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchall()

    if request.method == "POST":
        # Get information about user id
        user_id = db.execute("SELECT id FROM users WHERE name = :user", {"user": user}).fetchall()

        # Check if user already reviewed the book
        current_review = db.execute("SELECT * FROM reviews WHERE books_id = :book_id AND reviews.users_id = :user_id",
                                   {"book_id": book_id, "user_id": user_id[0].id}).fetchall()
        if current_review != []:
            message = "You have already reviewed the book!"
            pass
        else:
            body = request.form.get("body")

            # Add review to database
            db.execute("INSERT INTO reviews (users_id, body, books_id) VALUES (:user_id, :body, :book_id)",
                    {"user_id": user_id[0].id, "body": body, "book_id": book_id})
            db.commit()

    book_reviews = db.execute("SELECT body, name FROM reviews, users WHERE books_id = :book_id AND reviews.users_id=users.id", {"book_id": book_id}).fetchall()

    return render_template("book.html", book=book_info, user=user, book_reviews=book_reviews, message=message)


@app.before_request
def check_if_logged():
    g.user = None

    if 'user' in session:
        g.user = session['user']


app.run(host="0.0.0.0")
