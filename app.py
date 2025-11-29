# Simplified Lost & Found College Project Backend
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db()
        with open(os.path.join(BASE_DIR, "schema.sql"), "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("Database created with sample data.")

@app.route("/")
def index():
    conn = get_db()
    data = conn.execute("SELECT * FROM reports WHERE status='approved'").fetchall()
    conn.close()
    return render_template("index.html", reports=data)

@app.route("/report/new", methods=["GET","POST"])
def new_report():
    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        location = request.form.get("location")
        description = request.form.get("description")
        file = request.files.get("photo")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db()
        conn.execute("INSERT INTO reports (name,age,location,description,status,photo_filename,created_at) VALUES (?,?,?,?,?,?,?)",
                     (name, age, location, description, "pending", filename, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        flash("Submitted for admin approval","success")
        return redirect(url_for("index"))
    return render_template("report_form.html")

ADMIN_USERNAME="adminanshika"
ADMIN_PASSWORD="arshika"

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["username"]==ADMIN_USERNAME and request.form["password"]==ADMIN_PASSWORD:
            session["admin"]=True
            return redirect(url_for("admin"))
        flash("Invalid Login","error")
    if not session.get("admin"):
        return render_template("admin_login.html")
    conn=get_db()
    reports=conn.execute("SELECT * FROM reports ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", reports=reports)

@app.route("/admin/approve/<int:id>")
def approve(id):
    if not session.get("admin"): 
        return redirect(url_for("admin"))
    conn=get_db()
    conn.execute("UPDATE reports SET status='approved' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:id>")
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    row = conn.execute("SELECT photo_filename FROM reports WHERE id=?", (id,)).fetchone()
    if row and row["photo_filename"]:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], row["photo_filename"]))
        except FileNotFoundError:
            pass
    conn.execute("DELETE FROM reports WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/uploads/<filename>")
def files(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
