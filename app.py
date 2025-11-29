import os, sqlite3, math
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, send_from_directory, session, flash
)
from werkzeug.utils import secure_filename

# --- basic config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- db helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Run schema.sql every time on start so new tables (comments, sos_events)
    are created if they don't exist.
    """
    conn = get_db()
    with open(os.path.join(BASE_DIR, "schema.sql"), "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database checked/initialized.")

# optional helper if you later store lat/lon for real nearby distance
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# --- public pages ---

@app.route("/")
def index():
    """Home page: approved reports + comments."""
    conn = get_db()
    reports = conn.execute(
        "SELECT * FROM reports WHERE status='approved' ORDER BY id DESC"
    ).fetchall()
    comment_rows = conn.execute(
        "SELECT * FROM comments ORDER BY created_at ASC"
    ).fetchall()
    conn.close()

    comments = {}
    for c in comment_rows:
        comments.setdefault(c["report_id"], []).append(c)

    return render_template("index.html", reports=reports, comments=comments)

@app.route("/report/new", methods=["GET", "POST"])
def new_report():
    """Form to create a new report (status = pending)."""
    if request.method == "POST":
        name = request.form.get("name") or ""
        age = request.form.get("age") or None
        location = request.form.get("location") or ""
        description = request.form.get("description") or ""
        file = request.files.get("photo")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_db()
        conn.execute(
            """INSERT INTO reports
               (name, age, location, description, status, photo_filename, created_at)
               VALUES (?, ?, ?, ?, 'pending', ?, ?)""",
            (name, age, location, description, filename, created_at),
        )
        conn.commit()
        conn.close()
        flash("Submitted for admin approval.", "success")
        return redirect(url_for("index"))

    return render_template("report_form.html")

@app.route("/report/<int:report_id>/comment", methods=["POST"])
def add_comment(report_id):
    """Add public comment to a report + optional helper mark."""
    author = request.form.get("author") or "Anonymous"
    text = request.form.get("text") or ""
    is_helper = 1 if request.form.get("is_helper") == "on" else 0

    if not text.strip():
        flash("Comment text is required.", "error")
        return redirect(url_for("index"))

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_db()
    conn.execute(
        """INSERT INTO comments (report_id, author, text, is_helper, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (report_id, author, text, is_helper, created_at),
    )
    conn.commit()
    conn.close()
    flash("Comment added.", "success")
    return redirect(url_for("index"))

@app.route("/sos", methods=["GET", "POST"])
def sos():
    """
    SOS page.
    User enters name + message + location.
    We save it and show reports whose location text looks similar.
    """
    nearby_reports = []
    if request.method == "POST":
        name = request.form.get("name") or "Anonymous"
        message = request.form.get("message") or "SOS"
        location_text = request.form.get("location_text") or ""
        lat = request.form.get("lat") or None
        lon = request.form.get("lon") or None
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = get_db()
        conn.execute(
            """INSERT INTO sos_events
               (name, message, location_text, latitude, longitude, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, message, location_text, lat, lon, created_at),
        )
        # "Nearby help" = simple match on location text for now
        nearby_reports = conn.execute(
            "SELECT * FROM reports WHERE status='approved' AND location LIKE ? ORDER BY id DESC",
            (f"%{location_text}%",),
        ).fetchall()
        conn.commit()
        conn.close()
        flash("SOS recorded (demo only, not real emergency service).", "success")

    return render_template("sos.html", nearby_reports=nearby_reports)

# --- admin ---

ADMIN_USERNAME = "adminanshika"
ADMIN_PASSWORD = "arshika"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME
            and request.form.get("password") == ADMIN_PASSWORD
        ):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Invalid login.", "error")

    if not session.get("admin"):
        return render_template("admin_login.html")

    conn = get_db()
    reports = conn.execute("SELECT * FROM reports ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", reports=reports)

@app.route("/admin/approve/<int:id>")
def approve(id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    conn.execute("UPDATE reports SET status='approved' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:id>")
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    row = conn.execute(
        "SELECT photo_filename FROM reports WHERE id=?", (id,)
    ).fetchone()
    if row and row["photo_filename"]:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], row["photo_filename"]))
        except FileNotFoundError:
            pass
    conn.execute("DELETE FROM reports WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# --- static files ---

@app.route("/uploads/<filename>")
def files(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --- start ---

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
