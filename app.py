from flask import Flask, render_template, request, redirect, session, url_for
import os
import sqlite3
from werkzeug.utils import secure_filename

# =========================
# DATABASE CONFIG
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "secret123"

# SQLite file
DB_PATH = "database.db"

# Upload folder
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


# =========================
# FILE UPLOAD
# =========================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):

    if file and allowed_file(file.filename):

        filename = secure_filename(file.filename)
        filename = os.urandom(4).hex() + "_" + filename

        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        return filename

    return None


# =========================
# DATABASE CONNECTION
# =========================

def db():

    if USE_POSTGRES:

        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )

    else:

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

    return conn


def execute_query(cursor, query, params=()):

    if not USE_POSTGRES:
        query = query.replace("%s", "?")

    cursor.execute(query, params)


# =========================
# INIT DATABASE
# =========================

def init_db():

    conn = db()
    cursor = conn.cursor()

    id_type = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

    execute_query(cursor, f"""
    CREATE TABLE IF NOT EXISTS users (
        id {id_type},
        name TEXT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    execute_query(cursor, f"""
    CREATE TABLE IF NOT EXISTS projects (
        id {id_type},
        user_id INTEGER,
        project_name TEXT,
        price REAL,
        image TEXT,
        client TEXT,
        contact TEXT,
        rating REAL DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    execute_query(cursor, f"""
    CREATE TABLE IF NOT EXISTS reviews (
        id {id_type},
        project_id INTEGER,
        client_name TEXT,
        review TEXT,
        rating REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if "user_id" in session:

        if session["role"] == "client":
            return redirect("/dashboard")

        else:
            return redirect("/freelancer-dashboard")

    return redirect("/login")


# =========================
# LOGIN
# =========================

@app.route("/login")
def login():
    return render_template("role-select.html")


@app.route("/client-login")
def client_login():

    session["user_id"] = 1
    session["role"] = "client"

    return redirect("/dashboard")


@app.route("/freelancer-login")
def freelancer_login():

    session["user_id"] = 1
    session["role"] = "freelancer"

    return redirect("/freelancer-dashboard")


# =========================
# CLIENT DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = db()
    cursor = conn.cursor()

    execute_query(cursor, "SELECT * FROM projects")

    projects = cursor.fetchall()

    total = len(projects)

    earnings = sum(float(p["price"]) for p in projects) if total else 0

    rating = sum(float(p["rating"]) for p in projects) / total if total else 0

    conn.close()

    return render_template(
        "dashboard.html",
        projects=projects,
        total=total,
        earnings=earnings,
        rating=round(rating, 1)
    )


# =========================
# FREELANCER DASHBOARD
# =========================

@app.route("/freelancer-dashboard")
def freelancer_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = db()
    cursor = conn.cursor()

    execute_query(cursor,
        "SELECT * FROM projects WHERE user_id=%s",
        (session["user_id"],)
    )

    projects = cursor.fetchall()

    total = len(projects)

    earnings = sum(float(p["price"]) for p in projects) if total else 0

    rating = sum(float(p["rating"]) for p in projects) / total if total else 0

    conn.close()

    return render_template(
        "freelancer-dashboard.html",
        projects=projects,
        total=total,
        earnings=earnings,
        rating=round(rating, 1)
    )


# =========================
# PORTFOLIO ROUTE
# =========================

@app.route("/portfolio/<int:user_id>")
def portfolio(user_id):

    conn = db()
    cursor = conn.cursor()

    execute_query(cursor,
        "SELECT * FROM projects WHERE user_id=%s",
        (user_id,)
    )

    projects = cursor.fetchall()

    total = len(projects)

    earnings = sum(float(p["price"]) for p in projects) if total else 0

    rating = sum(float(p["rating"]) for p in projects) / total if total else 0

    conn.close()

    return render_template(
        "portfolio.html",
        projects=projects,
        total=total,
        earnings=earnings,
        rating=round(rating, 1)
    )


# =========================
# ADD PROJECT
# =========================

@app.route("/add", methods=["GET", "POST"])
def add():

    if request.method == "POST":

        image = None

        if "image" in request.files:
            image = save_uploaded_file(request.files["image"])

        conn = db()
        cursor = conn.cursor()

        execute_query(cursor, """
        INSERT INTO projects
        (user_id, project_name, price, image, client, contact, rating, status)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            session["user_id"],
            request.form.get("title"),
            request.form.get("budget"),
            image,
            request.form.get("client"),
            request.form.get("contact"),
            request.form.get("rating"),
            request.form.get("status")
        ))

        conn.commit()
        conn.close()

        return redirect("/freelancer-dashboard")

    return render_template("add.html")


# =========================
# DELETE
# =========================

@app.route("/delete/<int:id>")
def delete(id):

    conn = db()
    cursor = conn.cursor()

    execute_query(cursor,
        "DELETE FROM projects WHERE id=%s",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/freelancer-dashboard")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)