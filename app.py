from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename
import tempfile
import sqlite3

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

app=Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key="secret"

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

# Use /tmp for Vercel compatibility, but for Railway use persistent if possible
if USE_POSTGRES:
    DB_PATH = None  # We'll use DATABASE_URL
else:
    DB_PATH = os.path.join(tempfile.gettempdir(), 'freelancer.db') if os.environ.get('VERCEL') else 'database.db'

app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
 if file and file.filename != '' and allowed_file(file.filename):
  filename = secure_filename(file.filename)
  filename = f"{os.urandom(4).hex()}_{filename}"
  file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
  return filename
 return None

def get_cursor(conn):
    return conn.cursor()

def execute_query(cursor, query, params=()):
    if USE_POSTGRES:
        query = query.replace('%', '%s')
    cursor.execute(query, params)
    return cursor

def db():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = db()
    cursor = get_cursor(conn)
    id_type = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    # Create users table
    execute_query(cursor, f"""
CREATE TABLE IF NOT EXISTS users (
    id {id_type},
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")
    # Create projects table
    execute_query(cursor, f"""
CREATE TABLE IF NOT EXISTS projects (
    id {id_type},
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    price REAL NOT NULL,
    image TEXT,
    client TEXT,
    contact TEXT,
    rating REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")
    # Create reviews table
    execute_query(cursor, f"""
CREATE TABLE IF NOT EXISTS reviews (
    id {id_type},
    project_id INTEGER NOT NULL,
    client_name TEXT,
    review TEXT,
    rating REAL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
""")
    # Add status column if it doesn't exist
    try:
        execute_query(cursor, "ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'pending'")
    except:
        pass  # Column already exists
    # Add created_date column if it doesn't exist
    try:
        execute_query(cursor, "ALTER TABLE projects ADD COLUMN created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except:
        pass  # Column already exists
    conn.commit()
    if USE_POSTGRES:
        cursor.close()
    conn.close()

# Initialize database on startup
init_db()

@app.route("/")
def home():
 if "user_id" in session:
  if session.get("role")=="client":
   return redirect("/dashboard")
  else:
   return redirect("/freelancer-dashboard")
 return redirect("/login")

@app.route("/login")
def login():
 return render_template("role-select.html")

@app.route("/client-login")
def client_login():
 session["user_id"]=1
 session["role"]="client"
 return redirect("/dashboard")

@app.route("/freelancer-login")
def freelancer_login():
 session["user_id"]=1
 session["role"]="freelancer"
 return redirect("/freelancer-dashboard")

@app.route("/dashboard")
def dashboard():
 if "user_id" not in session or session.get("role")!="client":
  return redirect("/login")
 conn=db()
 cursor = get_cursor(conn)
 execute_query(cursor, "SELECT * FROM projects")
 projects = cursor.fetchall()
 if USE_POSTGRES:
     cursor.close()
 total=len(projects)
 earnings=sum([p['price'] for p in projects]) if projects else 0
 rating=sum([p['rating'] for p in projects])/total if total > 0 else 0
 return render_template("dashboard.html",total=total,earnings=earnings,rating=round(rating,1),projects=projects,session=session)

@app.route("/freelancer-dashboard")
def freelancer_dashboard():
 if "user_id" not in session or session.get("role")!="freelancer":
  return redirect("/login")
 conn=db()
 cursor = get_cursor(conn)
 execute_query(cursor, "SELECT * FROM projects")
 projects = cursor.fetchall()
 if USE_POSTGRES:
     cursor.close()
 total=len(projects)
 earnings=sum([p['price'] for p in projects]) if projects else 0
 rating=sum([p['rating'] for p in projects])/total if total > 0 else 0
 return render_template("freelancer-dashboard.html",total=total,earnings=earnings,rating=round(rating,1),projects=projects,session=session)

@app.route("/portfolio/<int:id>")
def portfolio(id):
 conn=db()
 cursor = get_cursor(conn)
 execute_query(cursor, "SELECT * FROM projects WHERE user_id=%s", (id,))
 projects = cursor.fetchall()
 if USE_POSTGRES:
     cursor.close()
 return render_template("portfolio.html",projects=projects)

@app.route("/review/<int:id>",methods=["GET","POST"])
def review(id):
 if "user_id" not in session:
  return redirect("/login")
 if request.method=="POST":
  try:
   conn=db()
   cursor = get_cursor(conn)
   execute_query(cursor, "INSERT INTO reviews(project_id,client_name,review,rating) VALUES(%s,%s,%s,%s)",
   (id,request.form.get("client",""),request.form.get("review",""),request.form.get("rating",0)))
   conn.commit()
   if USE_POSTGRES:
       cursor.close()
  except Exception as e:
   pass
  if session.get("role")=="freelancer":
   return redirect("/freelancer-dashboard")
  else:
   return redirect("/dashboard")
 return render_template("review.html")

@app.route("/add", methods=["GET", "POST"])
def add():
 if "user_id" not in session or session.get("role")!="client":
  return redirect("/login")
 if request.method=="POST":
  image_filename = None
  if "image" in request.files:
   image_filename = save_uploaded_file(request.files["image"])
  conn=db()
  cursor = get_cursor(conn)
  execute_query(cursor, "INSERT INTO projects(user_id,project_name,price,image,client,rating,status) VALUES(%s,%s,%s,%s,%s,%s,%s)",
  (1,request.form["title"],request.form["budget"],image_filename,request.form.get("contact",""),request.form["rating"],request.form.get("status","pending")))
  conn.commit()
  if USE_POSTGRES:
      cursor.close()
  return redirect("/dashboard")
 return render_template("add.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
 if "user_id" not in session or session.get("role")!="freelancer":
  return redirect("/login")
 
 if request.method=="POST" and "password_verified" not in session:
  password = request.form.get("password", "").strip()
  if password == "848912":
   session["password_verified"]=True
   return redirect(f"/edit/{id}")
  else:
   return render_template("edit-password.html", id=id, error="Invalid password")
 
 if "password_verified" not in session:
  return render_template("edit-password.html", id=id)
 
 conn=db()
 if request.method=="POST" and "password_verified" in session:
  image_filename = None
  cursor = get_cursor(conn)
  if "image" in request.files and request.files["image"].filename:
   image_filename = save_uploaded_file(request.files["image"])
   execute_query(cursor, "UPDATE projects SET project_name=%s, price=%s, image=%s, client=%s, rating=%s, status=%s WHERE id=%s",
   (request.form["title"],request.form["budget"],image_filename,request.form.get("contact",""),request.form["rating"],request.form.get("status","pending"),id))
  else:
   execute_query(cursor, "UPDATE projects SET project_name=%s, price=%s, client=%s, rating=%s, status=%s WHERE id=%s",
   (request.form["title"],request.form["budget"],request.form.get("contact",""),request.form["rating"],request.form.get("status","pending"),id))
  conn.commit()
  if USE_POSTGRES:
      cursor.close()
  session.pop("password_verified", None)
  return redirect("/freelancer-dashboard")
 cursor = get_cursor(conn)
 execute_query(cursor, "SELECT * FROM projects WHERE id=%s", (id,))
 project = cursor.fetchone()
 if USE_POSTGRES:
     cursor.close()
 return render_template("edit.html", project=project)

@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
 if "user_id" not in session or session.get("role")!="freelancer":
  return redirect("/login")
 
 if request.method=="POST" and "delete_password_verified" not in session:
  password = request.form.get("password", "").strip()
  if password == "848912":
   session["delete_password_verified"]=True
   return redirect(f"/delete/{id}")
  else:
   return render_template("delete-password.html", id=id, error="Invalid password")
 
 if "delete_password_verified" not in session:
  return render_template("delete-password.html", id=id)
 
 conn=db()
 cursor = get_cursor(conn)
 execute_query(cursor, "DELETE FROM projects WHERE id=%s", (id,))
 conn.commit()
 if USE_POSTGRES:
     cursor.close()
 session.pop("delete_password_verified", None)
 return redirect("/freelancer-dashboard")

@app.route("/admin")
def admin():
 conn=db()
 cursor = get_cursor(conn)
 execute_query(cursor, "SELECT * FROM users")
 users = cursor.fetchall()
 execute_query(cursor, "SELECT * FROM projects")
 projects = cursor.fetchall()
 if USE_POSTGRES:
     cursor.close()
 return render_template("admin.html",users=users,projects=projects)

@app.route("/logout")
def logout():
 session.clear()
 return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


