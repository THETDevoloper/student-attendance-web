import os

from datetime import datetime, date, time

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from database import (
    db,
    Student,
    Attendance
)

from report import (
    calculate_hours,
    format_hours,
    export_csv,
    export_pdf
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "student-attendance-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///attendance.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


with app.app_context():
    db.create_all()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required():

    return "logged_in" in session


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if (
            username == "admin"
            and password == "1234"
        ):

            session["logged_in"] = True
            session["username"] = username

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Incorrect username or password.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    student_count = Student.query.count()

    today = date.today()

    start = datetime.combine(
        today,
        time.min
    )

    end = datetime.combine(
        today,
        time.max
    )

    attendance_count = Attendance.query.filter(
        Attendance.check_in_time >= start,
        Attendance.check_in_time <= end
    ).count()

    checkout_count = Attendance.query.filter(
        Attendance.check_in_time >= start,
        Attendance.check_in_time <= end,
        Attendance.check_out_time.isnot(None)
    ).count()

    return render_template(
        "dashboard.html",
        student_count=student_count,
        attendance_count=attendance_count,
        checkout_count=checkout_count
    )


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
def students():

    if not login_required():
        return redirect(url_for("login"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    query = Student.query

    if search:

        query = query.filter(
            db.or_(
                Student.student_id.contains(search),
                Student.name.contains(search)
            )
        )

    students_list = query.order_by(
        Student.name
    ).all()

    return render_template(
        "students.html",
        students=students_list,
        search=search
    )


# =========================================================
# ADD STUDENT
# =========================================================

@app.route(
    "/students/add",
    methods=["POST"]
)
def add_student():

    if not login_required():
        return redirect(url_for("login"))

    student_id = request.form.get(
        "student_id",
        ""
    ).strip()

    name = request.form.get(
        "name",
        ""
    ).strip()

    gender = request.form.get(
        "gender",
        "Male"
    )

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    if not student_id or not name:

        flash(
            "Student ID and Name are required.",
            "warning"
        )

        return redirect(
            url_for("students")
        )

    existing = Student.query.filter_by(
        student_id=student_id
    ).first()

    if existing:

        flash(
            "Student ID already exists.",
            "danger"
        )

        return redirect(
            url_for("students")
        )

    student = Student(
        student_id=student_id,
        name=name,
        gender=gender,
        phone=phone,
        email=email
    )

    db.session.add(student)
    db.session.commit()

    flash(
        f"{name} added successfully.",
        "success"
    )

    return redirect(
        url_for("students")
    )


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route(
    "/students/delete/<int:student_id>",
    methods=["POST"]
)
def delete_student(student_id):

    if not login_required():
        return redirect(url_for("login"))

    student = db.session.get(
        Student,
        student_id
    )

    if not student:

        flash(
            "Student not found.",
            "danger"
        )

        return redirect(
            url_for("students")
        )

    db.session.delete(student)
    db.session.commit()

    flash(
        "Student deleted successfully.",
        "success"
    )

    return redirect(
        url_for("students")
    )


# =========================================================
# CHECK IN
# =========================================================

@app.route(
    "/checkin",
    methods=["GET", "POST"]
)
def checkin():

    if not login_required():
        return redirect(url_for("login"))

    students_list = Student.query.order_by(
        Student.name
    ).all()

    if request.method == "POST":

        student_id = request.form.get(
            "student_id"
        )

        student = db.session.get(
            Student,
            int(student_id)
        )

        if not student:

            flash(
                "Student not found.",
                "danger"
            )

            return redirect(
                url_for("checkin")
            )

        now = datetime.now()

        start = datetime.combine(
            now.date(),
            time.min
        )

        end = datetime.combine(
            now.date(),
            time.max
        )

        # IMPORTANT:
        # Only an OPEN attendance blocks Check In.
        # Completed records do NOT block another Check In.

        open_record = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.check_in_time >= start,
            Attendance.check_in_time <= end,
            Attendance.check_out_time.is_(None)
        ).first()

        if open_record:

            flash(
                f"{student.name} is already checked in. "
                f"Please Check Out first.",
                "warning"
            )

            return redirect(
                url_for("checkin")
            )

        attendance = Attendance(
            student_id=student.id,
            check_in_time=now,
            check_out_time=None,
            status="Present"
        )

        db.session.add(attendance)
        db.session.commit()

        flash(
            f"Check In successful: {student.name} "
            f"at {now.strftime('%I:%M:%S %p')}",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "checkin.html",
        students=students_list
    )


# =========================================================
# CHECK OUT
# =========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    if not login_required():
        return redirect(url_for("login"))

    today = date.today()

    start = datetime.combine(
        today,
        time.min
    )

    end = datetime.combine(
        today,
        time.max
    )

    # Only students with OPEN attendance records

    records = db.session.query(
        Attendance,
        Student
    ).join(
        Student,
        Attendance.student_id == Student.id
    ).filter(
        Attendance.check_in_time >= start,
        Attendance.check_in_time <= end,
        Attendance.check_out_time.is_(None)
    ).order_by(
        Student.name
    ).all()

    if request.method == "POST":

        student_id = request.form.get(
            "student_id"
        )

        student = db.session.get(
            Student,
            int(student_id)
        )

        if not student:

            flash(
                "Student not found.",
                "danger"
            )

            return redirect(
                url_for("checkout")
            )

        attendance = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.check_in_time >= start,
            Attendance.check_in_time <= end,
            Attendance.check_out_time.is_(None)
        ).order_by(
            Attendance.check_in_time.desc()
        ).first()

        if not attendance:

            flash(
                f"{student.name} must Check In first.",
                "warning"
            )

            return redirect(
                url_for("checkout")
            )

        now = datetime.now()

        attendance.check_out_time = now
        attendance.status = "Completed"

        db.session.commit()

        hours = calculate_hours(
            attendance.check_in_time,
            now
        )

        flash(
            f"Check Out successful: {student.name} | "
            f"{attendance.check_in_time.strftime('%I:%M %p')} → "
            f"{now.strftime('%I:%M %p')} | "
            f"{format_hours(hours)}",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "checkout.html",
        records=records
    )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    if not login_required():
        return redirect(url_for("login"))

    search = request.args.get(
        "student",
        ""
    ).strip()

    from_date = request.args.get(
        "from_date",
        ""
    ).strip()

    to_date = request.args.get(
        "to_date",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        "All"
    )

    query = db.session.query(
        Attendance,
        Student
    ).join(
        Student,
        Attendance.student_id == Student.id
    )

    if search:

        query = query.filter(
            db.or_(
                Student.student_id.contains(search),
                Student.name.contains(search)
            )
        )

    parsed_from = None
    parsed_to = None

    if from_date:

        try:

            parsed_from = datetime.strptime(
                from_date,
                "%d/%m/%Y"
            ).date()

            query = query.filter(
                Attendance.check_in_time >=
                datetime.combine(
                    parsed_from,
                    time.min
                )
            )

        except ValueError:

            flash(
                "From Date must be DD/MM/YYYY.",
                "warning"
            )

    if to_date:

        try:

            parsed_to = datetime.strptime(
                to_date,
                "%d/%m/%Y"
            ).date()

            query = query.filter(
                Attendance.check_in_time <=
                datetime.combine(
                    parsed_to,
                    time.max
                )
            )

        except ValueError:

            flash(
                "To Date must be DD/MM/YYYY.",
                "warning"
            )

    if (
        parsed_from
        and parsed_to
        and parsed_from > parsed_to
    ):

        flash(
            "From Date cannot be later than To Date.",
            "warning"
        )

    if selected_status != "All":

        query = query.filter(
            Attendance.status == selected_status
        )

    records = query.order_by(
        Attendance.check_in_time.desc()
    ).all()

    # =====================================================
    # TOTAL HOURS
    # =====================================================

    grand_total = 0

    student_totals = {}

    for attendance, student in records:

        hours = calculate_hours(
            attendance.check_in_time,
            attendance.check_out_time
        )

        grand_total += hours

        if student.id not in student_totals:

            student_totals[student.id] = {
                "student_id": student.student_id,
                "name": student.name,
                "hours": 0
            }

        student_totals[
            student.id
        ]["hours"] += hours

    return render_template(
        "reports.html",
        records=records,
        search=search,
        from_date=from_date,
        to_date=to_date,
        selected_status=selected_status,
        grand_total=grand_total,
        student_totals=student_totals,
        calculate_hours=calculate_hours,
        format_hours=format_hours
    )


# =========================================================
# EXPORT CSV
# =========================================================

@app.route("/reports/csv")
def reports_csv():

    if not login_required():
        return redirect(url_for("login"))

    records = get_filtered_records()

    if not records:

        flash(
            "No records to export.",
            "warning"
        )

        return redirect(
            url_for("reports")
        )

    filename = "attendance_report.csv"

    export_csv(
        records,
        filename
    )

    return send_file(
        filename,
        as_attachment=True,
        download_name=filename
    )


# =========================================================
# EXPORT PDF
# =========================================================

@app.route("/reports/pdf")
def reports_pdf():

    if not login_required():
        return redirect(url_for("login"))

    records = get_filtered_records()

    if not records:

        flash(
            "No records to export.",
            "warning"
        )

        return redirect(
            url_for("reports")
        )

    filename = "attendance_report.pdf"

    export_pdf(
        records,
        filename
    )

    return send_file(
        filename,
        as_attachment=True,
        download_name=filename
    )


# =========================================================
# FILTER FUNCTION
# =========================================================

def get_filtered_records():

    search = request.args.get(
        "student",
        ""
    ).strip()

    from_date = request.args.get(
        "from_date",
        ""
    ).strip()

    to_date = request.args.get(
        "to_date",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        "All"
    )

    query = db.session.query(
        Attendance,
        Student
    ).join(
        Student,
        Attendance.student_id == Student.id
    )

    if search:

        query = query.filter(
            db.or_(
                Student.student_id.contains(search),
                Student.name.contains(search)
            )
        )

    if from_date:

        try:

            day = datetime.strptime(
                from_date,
                "%d/%m/%Y"
            ).date()

            query = query.filter(
                Attendance.check_in_time >=
                datetime.combine(
                    day,
                    time.min
                )
            )

        except ValueError:
            pass

    if to_date:

        try:

            day = datetime.strptime(
                to_date,
                "%d/%m/%Y"
            ).date()

            query = query.filter(
                Attendance.check_in_time <=
                datetime.combine(
                    day,
                    time.max
                )
            )

        except ValueError:
            pass

    if selected_status != "All":

        query = query.filter(
            Attendance.status == selected_status
        )

    return query.order_by(
        Attendance.check_in_time.desc()
    ).all()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )