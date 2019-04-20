import os

from flask import Flask, render_template, request, session, redirect, g
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


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('user', None)

    return render_template("index.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register/form/", methods=["POST"])
def register_form():
    """Register"""

    session.pop('user', None)

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")

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

    session['user'] = username

    return render_template("success_register.html")


@app.route("/login/")
def login():
    return render_template("login.html")


@app.route("/login/form/", methods=["POST"])
def login_form():
    """Log in"""

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")

    # Make sure the flight exists.
    user = db.execute("SELECT * FROM users WHERE name = :username AND password = :password",
                      {"username": username, "password": password}).fetchall()

    try:
        pw_db = user[0]["password"]
    except IndexError:
        return render_template("error_login.html", message="Username or password is incorrect.")

    if password != pw_db:
        return render_template("error_login.html", message="Username or password is incorrect.")

    if user != []:
        session['user'] = username
        return render_template("success_login.html", user_info=user)
    else:
        return render_template("error_login.html", message="Username or password is incorrect.")


@app.route("/book_search/", methods=["POST"])
def book_search():
    """Search for books and return the results"""

    # Get information about the book
    book_keywords = request.form.get("book_keywords")
    user_id = request.form.get("user_id")

    user = db.execute("SELECT * FROM users WHERE id = :user_id", {"user_id": user_id}).fetchall()

    book_results = db.execute("SELECT * FROM books WHERE isbn LIKE :b_key OR lower(title) LIKE :b_key OR lower(author) LIKE :b_key",
                              {"b_key": '%' + str(book_keywords) + '%'}).fetchall()

    return render_template("book_search.html", book_results=book_results, user=user)


@app.route("/book/<int:book_id>")
def book(book_id):
    book_info = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchall()

    if g.user:
        msg = "LOGGED"
    else:
        msg = "NOT LOGGED"

    return render_template("book.html", book=book_info, msg=msg)


@app.before_request
def check_if_logged():
    g.user = None

    if 'user' in session:
        g.user = session['user']


app.run(host="0.0.0.0")
