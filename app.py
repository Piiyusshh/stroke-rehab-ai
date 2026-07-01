import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import csv
from datetime import datetime
from jinja2 import Environment

# Import models and utils
from models import db, User, Plan, Progress
from utils.plan_engine import generate_plan

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///rehab.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add Jinja2 globals
app.jinja_env.globals['now'] = datetime.now

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ---------------------- LOGIN MANAGER ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------- ROUTES ----------------------
@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please provide username, email, and password.")
            return redirect(url_for("register"))

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already exists. Choose another.")
            return redirect(url_for("register"))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already exists. Choose another.")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful — please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    plans = Plan.query.filter_by(user_id=current_user.id).all()
    progress_data = []
    for plan in plans:
        progress = Progress.query.filter_by(plan_id=plan.id).order_by(Progress.date).all()
        progress_data.append({
            'plan_id': plan.id,
            'dates': [p.date.isoformat() for p in progress],
            'walk_speeds': [p.walk_speed for p in progress if p.walk_speed],
            'grip_strengths': [p.grip_strength for p in progress if p.grip_strength],
            'adherences': [p.adherence for p in progress]
        })
    return render_template("dashboard.html", plans=plans, progress_data=progress_data)


@app.route("/create_plan")
@login_required
def create_plan():
    return render_template("create_plan.html")


@app.route("/plan", methods=["POST"])
@login_required
def plan():
    patient_name = request.form.get("patient_name", "").strip()
    age = request.form.get("age", "").strip()
    sex = request.form.get("sex", "").strip()
    stroke_type = request.form.get("stroke_type", "").strip()
    nihss = request.form.get("nihss", "").strip()
    affected_side = request.form.get("affected_side", "").strip()
    weeks_post_stroke = request.form.get("weeks_post_stroke", "").strip()
    comorbidities = request.form.getlist("comorbidities") or []
    goals = request.form.getlist("goals") or []

    try:
        age_i = int(age)
        nihss_i = int(nihss)
        weeks_i = int(weeks_post_stroke)
    except ValueError:
        flash("Please enter valid numeric values for Age / NIHSS / Weeks post stroke.")
        return redirect(url_for("create_plan"))

    input_data = {
        "age": age_i,
        "sex": sex,
        "stroke_type": stroke_type,
        "nihss": nihss_i,
        "affected_side": affected_side,
        "weeks_post_stroke": weeks_i,
        "comorbidities": comorbidities,
        "goals": goals,
    }

    # Get average adherence from existing progress for this user, default 3
    avg_adherence = db.session.query(db.func.avg(Progress.adherence)).filter(Progress.user_id == current_user.id).scalar() or 3
    plan_dict = generate_plan(input_data, adherence=int(avg_adherence))

    p = Plan(
        patient_name=patient_name,
        age=age_i,
        sex=sex,
        stroke_type=stroke_type,
        nihss=nihss_i,
        affected_side=affected_side,
        weeks_post_stroke=weeks_i,
        comorbidities=",".join(comorbidities),
        goals=",".join(goals),
        input_data=json.dumps(input_data),
        plan_data=json.dumps(plan_dict),
        user_id=current_user.id,
    )
    db.session.add(p)
    db.session.commit()

    return render_template("plan.html", plan=plan_dict, patient_name=patient_name)


# ---------------------- NEW ROUTES ----------------------
@app.route("/add_progress/<int:plan_id>", methods=["GET", "POST"])
@login_required
def add_progress(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    if request.method == "POST":
        try:
            walk_speed = float(request.form.get("walk_speed", 0)) if request.form.get("walk_speed") else None
            grip_strength = float(request.form.get("grip_strength", 0)) if request.form.get("grip_strength") else None
            adherence = int(request.form.get("adherence", 0))
        except ValueError:
            flash("Invalid numeric values.")
            return redirect(request.url)

        progress = Progress(
            plan_id=plan_id,
            user_id=current_user.id,
            walk_speed=walk_speed,
            grip_strength=grip_strength,
            adherence=adherence
        )
        db.session.add(progress)
        db.session.commit()
        flash("Progress added successfully.")
        return redirect(url_for("view_progress", plan_id=plan_id))

    return render_template("progress.html", plan=plan)


@app.route("/view_progress/<int:plan_id>")
@login_required
def view_progress(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    progress = Progress.query.filter_by(plan_id=plan_id).order_by(Progress.date).all()
    return render_template("progress.html", plan=plan, progress=progress, view=True)


@app.route("/generate_report/<int:plan_id>")
@login_required
def generate_report(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    progress = Progress.query.filter_by(plan_id=plan_id).order_by(Progress.date).all()
    plan_data = json.loads(plan.plan_data)

    # Generate PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.drawString(100, height - 50, f"Stroke Rehab Report for {plan.patient_name}")
    c.drawString(100, height - 70, f"Generated on {datetime.now().strftime('%Y-%m-%d')}")

    y = height - 100
    c.drawString(100, y, f"Patient Age: {plan.age}, Sex: {plan.sex}, Stroke Type: {plan.stroke_type}")
    y -= 20
    c.drawString(100, y, f"NIHSS: {plan.nihss}, Affected Side: {plan.affected_side}, Weeks Post Stroke: {plan.weeks_post_stroke}")
    y -= 20
    c.drawString(100, y, f"Predicted Recovery Progress: {plan_data['meta'].get('predicted_recovery_progress', 'N/A')}%")

    y -= 40
    c.drawString(100, y, "Progress History:")
    y -= 20
    for p in progress:
        c.drawString(120, y, f"Date: {p.date}, Walk Speed: {p.walk_speed or 'N/A'} m/s, Grip: {p.grip_strength or 'N/A'} kg, Adherence: {p.adherence}")
        y -= 20
        if y < 100:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"report_{plan.patient_name}.pdf", mimetype='application/pdf')


@app.route("/export_progress/<int:plan_id>")
@login_required
def export_progress(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    progress = Progress.query.filter_by(plan_id=plan_id).order_by(Progress.date).all()

    # Generate CSV
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Walk Speed (m/s)', 'Grip Strength (kg)', 'Adherence (sessions)'])
    for p in progress:
        writer.writerow([p.date, p.walk_speed or '', p.grip_strength or '', p.adherence])

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"progress_{plan.patient_name}.csv", mimetype='text/csv')


@app.route("/view_plan/<int:plan_id>")
@login_required
def view_plan(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    plan_data = json.loads(plan.plan_data)
    return render_template("plan_detail.html", plan=plan_data, meta=plan)


@app.route("/plans_list")
@login_required
def plans_list():
    plans = Plan.query.filter_by(user_id=current_user.id).order_by(Plan.created_at.desc()).all()
    return render_template("plans_list.html", plans=plans)


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
