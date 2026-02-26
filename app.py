from flask import Flask, render_template, request, redirect, session, url_for
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Password used for edit/delete protection
ADMIN_PASSWORD = "8489"

DB_PATH = "database.db"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


# ================= DATABASE =================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        project_name TEXT,
        price REAL,
        image TEXT,
        client TEXT,
        contact TEXT,
        portfolio_url TEXT,
        rating REAL,
        status TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= FILE UPLOAD =================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = os.urandom(4).hex() + "_" + filename
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return filename
    return None


# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("select-role.html")


@app.route("/set-role/<role>")
def set_role(role):
    session.clear()
    session["user_id"] = 1
    session["role"] = role

    if role == "client":
        return redirect(url_for("dashboard"))
    elif role == "freelancer":
        return redirect(url_for("freelancer_dashboard"))
    return redirect(url_for("home"))


# ================= CLIENT DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if session.get("role") != "client":
        return redirect(url_for("home"))

    conn = db()
    projects = conn.execute("SELECT * FROM projects").fetchall()
    conn.close()

    total = len(projects)
    earnings = sum(float(p["price"] or 0) for p in projects)

    ratings = [float(p["rating"]) for p in projects if p["rating"]]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

    return render_template(
        "dashboard.html",
        projects=projects,
        total=total,
        earnings=earnings,
        rating=avg_rating
    )


# ================= FREELANCER DASHBOARD =================

@app.route("/freelancer-dashboard")
def freelancer_dashboard():
    if session.get("role") != "freelancer":
        return redirect(url_for("home"))

    conn = db()
    projects = conn.execute(
        "SELECT * FROM projects WHERE user_id = ?",
        (session.get("user_id"),)
    ).fetchall()
    conn.close()

    total = len(projects)
    earnings = sum(float(p["price"] or 0) for p in projects)

    ratings = [float(p["rating"]) for p in projects if p["rating"]]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

    return render_template(
        "freelancer-dashboard.html",
        projects=projects,
        total=total,
        earnings=earnings,
        rating=avg_rating
    )


# ================= PORTFOLIO =================

@app.route("/portfolio/<int:user_id>")
def portfolio(user_id):
    conn = db()
    projects = conn.execute(
        "SELECT * FROM projects WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()

    total_projects = len(projects)
    total_value = sum(float(p["price"] or 0) for p in projects)
    
    ratings = [float(p["rating"]) for p in projects if p["rating"]]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0

    return render_template(
        "portfolio.html",
        projects=projects,
        total_projects=total_projects,
        total_value=total_value,
        avg_rating=avg_rating
    )


# ================= ADD PROJECT =================

@app.route("/add", methods=["GET", "POST"])
def add():
    if not session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":

        image = None
        if "image" in request.files:
            image = save_uploaded_file(request.files["image"])

    # Fix price from 'budget' field in the form
    try:
        price = float(request.form.get("budget") or 0)
    except:
        price = 0

        # Fix rating
        try:
            rating = float(request.form.get("rating") or 0)
        except:
            rating = 0

        portfolio_url = request.form.get("portfolio_url") or ""

        conn = db()
        conn.execute("""
        INSERT INTO projects
        (user_id, project_name, price, image, client, contact, portfolio_url, rating, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.get("user_id"),
            request.form.get("title"),
            price,
            image,
            request.form.get("client"),
            request.form.get("contact"),
            portfolio_url,
            rating,
            request.form.get("status")
        ))
        conn.commit()
        conn.close()

        if session.get("role") == "client":
            return redirect(url_for("dashboard"))
        return redirect(url_for("freelancer_dashboard"))

    return render_template("add.html")


#!/ ================= EDIT (PASSWORD PROTECTED) =================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_password(id):
    # Require role to be set
    if not session.get("role"):
        return redirect(url_for("home"))

    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["edit_ok"] = True
            return redirect(url_for("edit_project", id=id))

        return render_template("edit-password.html", error="Wrong password")

    return render_template("edit-password.html")


@app.route("/edit-project/<int:id>", methods=["GET", "POST"])
def edit_project(id):
    # Must come from successful password check
    if not session.get("edit_ok"):
        return redirect(url_for("edit_password", id=id))

    conn = db()

    if request.method == "POST":
        image = None

        if "image" in request.files:
            image = save_uploaded_file(request.files["image"])

        # Fix price from 'budget' field in the form
        try:
            price = float(request.form.get("budget") or 0)
        except:
            price = 0

        # Fix rating
        try:
            rating = float(request.form.get("rating") or 0)
        except:
            rating = 0

        # Keep existing image if new one not uploaded
        cursor = conn.execute("SELECT image FROM projects WHERE id = ?", (id,))
        row = cursor.fetchone()
        current_image = row["image"] if row else None
        final_image = image or current_image

        conn.execute(
            """
            UPDATE projects
            SET project_name = ?,
                price = ?,
                client = ?,
                contact = ?,
                rating = ?,
                status = ?,
                image = ?
            WHERE id = ?
            """,
            (
                request.form.get("title"),
                price,
                request.form.get("client"),
                request.form.get("contact"),
                rating,
                request.form.get("status"),
                final_image,
                id,
            ),
        )
        conn.commit()
        conn.close()

        # Clear flag so URL can't be reused
        session.pop("edit_ok", None)

        if session.get("role") == "client":
            return redirect(url_for("dashboard"))
        return redirect(url_for("freelancer_dashboard"))

    # GET: load project and show edit form
    project = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (id,)
    ).fetchone()
    conn.close()

    if not project:
        # No such project, go back
        if session.get("role") == "client":
            return redirect(url_for("dashboard"))
        return redirect(url_for("freelancer_dashboard"))

    return render_template("edit.html", project=project)


# ================= DELETE (PASSWORD PROTECTED) =================

@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    # Require role to be set
    if not session.get("role"):
        return redirect(url_for("home"))

    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            conn = db()
            conn.execute("DELETE FROM projects WHERE id = ?", (id,))
            conn.commit()
            conn.close()

            if session.get("role") == "client":
                return redirect(url_for("dashboard"))
            return redirect(url_for("freelancer_dashboard"))

        return render_template("delete-password.html", error="Wrong password")

    return render_template("delete-password.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)