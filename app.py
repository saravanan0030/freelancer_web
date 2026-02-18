from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from werkzeug.utils import secure_filename
import tempfile

app=Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key="secret"

# Use /tmp for Vercel compatibility
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

def db():
 return sqlite3.connect(DB_PATH)

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
 projects=conn.execute("SELECT * FROM projects").fetchall()
 total=len(projects)
 earnings=sum([p[3] for p in projects]) if projects else 0
 rating=sum([p[7] for p in projects])/total if total > 0 else 0
 return render_template("dashboard.html",total=total,earnings=earnings,rating=round(rating,1),projects=projects,session=session)

@app.route("/freelancer-dashboard")
def freelancer_dashboard():
 if "user_id" not in session or session.get("role")!="freelancer":
  return redirect("/login")
 conn=db()
 projects=conn.execute("SELECT * FROM projects").fetchall()
 total=len(projects)
 earnings=sum([p[3] for p in projects]) if projects else 0
 rating=sum([p[7] for p in projects])/total if total > 0 else 0
 return render_template("freelancer-dashboard.html",total=total,earnings=earnings,rating=round(rating,1),projects=projects,session=session)

@app.route("/portfolio/<int:id>")
def portfolio(id):
 conn=db()
 projects=conn.execute("SELECT * FROM projects WHERE user_id=?",(id,)).fetchall()
 return render_template("portfolio.html",projects=projects)

@app.route("/review/<int:id>",methods=["GET","POST"])
def review(id):
 if "user_id" not in session:
  return redirect("/login")
 if request.method=="POST":
  try:
   conn=db()
   conn.execute("INSERT INTO reviews(project_id,client_name,review,rating) VALUES(?,?,?,?)",
   (id,request.form.get("client",""),request.form.get("review",""),request.form.get("rating",0)))
   conn.commit()
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
  conn.execute("INSERT INTO projects(user_id,project_name,price,image,client,rating) VALUES(?,?,?,?,?,?)",
  (1,request.form["title"],request.form["budget"],image_filename,request.form.get("contact",""),request.form["rating"]))
  conn.commit()
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
  if "image" in request.files and request.files["image"].filename:
   image_filename = save_uploaded_file(request.files["image"])
   conn.execute("UPDATE projects SET project_name=?, price=?, image=?, client=?, rating=? WHERE id=?",
   (request.form["title"],request.form["budget"],image_filename,request.form.get("contact",""),request.form["rating"],id))
  else:
   conn.execute("UPDATE projects SET project_name=?, price=?, client=?, rating=? WHERE id=?",
   (request.form["title"],request.form["budget"],request.form.get("contact",""),request.form["rating"],id))
  conn.commit()
  session.pop("password_verified", None)
  return redirect("/freelancer-dashboard")
 project=conn.execute("SELECT * FROM projects WHERE id=?", (id,)).fetchone()
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
 conn.execute("DELETE FROM projects WHERE id=?", (id,))
 conn.commit()
 session.pop("delete_password_verified", None)
 return redirect("/freelancer-dashboard")

@app.route("/admin")
def admin():
 conn=db()
 users=conn.execute("SELECT * FROM users").fetchall()
 projects=conn.execute("SELECT * FROM projects").fetchall()
 return render_template("admin.html",users=users,projects=projects)

@app.route("/logout")
def logout():
 session.clear()
 return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

