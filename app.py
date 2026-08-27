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
    send_file,
)

from database import (
    SessionLocal,
    Student,
    Attendance,
    init_db,
)

from report import (
    calculate_hours,
    format_hours,
    export_csv,
    export_pdf,
)


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "student-attendance-secret-key"
)


# =========================================================
# DATABASE
# =========================================================

init_db()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required():

    return "logged_in" in session


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
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

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Incorrect username or password.",
            "error"
        )

    if login_required():

        return redirect(
            url_for("dashboard")
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

        return redirect(
            url_for("login")
        )

    db = SessionLocal()

    try:

        today = date.today()

        start = datetime.combine(
            today,
            time.min
        )

        end = datetime.combine(
            today,
            time.max
        )

        student_count = db.query(
            Student
        ).count()

        attendance_count = db.query(
            Attendance
        ).filter(
            Attendance.check_in_time >= start,
            Attendance.check_in_time <= end
        ).count()

        checkout_count = db.query(
            Attendance
        ).filter(
            Attendance.check_in_time >= start,
            Attendance.check_in_time <= end,
            Attendance.check_out_time.isnot(None)
        ).count()

        present_count = db.query(
            Attendance
        ).filter(
            Attendance.check_in_time >= start,
            Attendance.check_in_time <= end,
            Attendance.status == "Present"
        ).count()

        return render_template(
            "dashboard.html",
            student_count=student_count,
            attendance_count=attendance_count,
            checkout_count=checkout_count,
            present_count=present_count
        )

    finally:

        db.close()


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
def students():

    if not login_required():

        return redirect(
            url_for("login")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    db = SessionLocal()

    try:

        query = db.query(Student)

        if search:

            query = query.filter(
                (
                    Student.student_id.contains(
                        search
                    )
                )
                |
                (
                    Student.name.contains(
                        search
                    )
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

    finally:

        db.close()


# =========================================================
# ADD STUDENT
# =========================================================

@app.route(
    "/students/add",
    methods=["GET", "POST"]
)
def add_student():

    if not login_required():

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

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
            ""
        ).strip()

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
                "error"
            )

            return redirect(
                url_for("add_student")
            )

        db = SessionLocal()

        try:

            existing = db.query(
                Student
            ).filter(
                Student.student_id == student_id
            ).first()

            if existing:

                flash(
                    "Student ID already exists.",
                    "error"
                )

                return redirect(
                    url_for("add_student")
                )

            student = Student(
                student_id=student_id,
                name=name,
                gender=gender,
                phone=phone,
                email=email
            )

            db.add(student)
            db.commit()

            flash(
                f"{name} added successfully.",
                "success"
            )

            return redirect(
                url_for("students")
            )

        except Exception as e:

            db.rollback()

            flash(
                f"Database Error: {e}",
                "error"
            )

            return redirect(
                url_for("add_student")
            )

        finally:

            db.close()

    return render_template(
        "add_student.html"
    )


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route(
    "/students/delete/<int:student_id>",
    methods=["POST", "GET"]
)
def delete_student(student_id):

    if not login_required():

        return redirect(
            url_for("login")
        )

    db = SessionLocal()

    try:

        student = db.query(
            Student
        ).filter(
            Student.id == student_id
        ).first()

        if student:

            db.delete(student)
            db.commit()

            flash(
                "Student deleted successfully.",
                "success"
            )

        else:

            flash(
                "Student not found.",
                "error"
            )

    except Exception as e:

        db.rollback()

        flash(
            f"Delete Error: {e}",
            "error"
        )

    finally:

        db.close()

    return redirect(
        url_for("students")
    )


# =========================================================
# CHECK IN
# =========================================================

@app.route(
    "/check-in",
    methods=["GET", "POST"]
)
def check_in():

    if not login_required():

        return redirect(
            url_for("login")
        )

    db = SessionLocal()

    try:

        students_list = db.query(
            Student
        ).order_by(
            Student.name
        ).all()

        if request.method == "POST":

            student_id = request.form.get(
                "student_id",
                ""
            ).strip()

            student = db.query(
                Student
            ).filter(
                Student.student_id == student_id
            ).first()

            if not student:

                flash(
                    "Student not found.",
                    "error"
                )

                return redirect(
                    url_for("check_in")
                )

            open_record = db.query(
                Attendance
            ).filter(
                Attendance.student_id == student.id,
                Attendance.check_out_time.is_(None)
            ).order_by(
                Attendance.check_in_time.desc()
            ).first()

            if open_record:

                flash(
                    f"{student.name} is already checked in. "
                    "Please Check Out first.",
                    "error"
                )

                return redirect(
                    url_for("check_in")
                )

            now = datetime.now()

            attendance = Attendance(
                student_id=student.id,
                check_in_time=now,
                check_out_time=None,
                status="Present"
            )

            db.add(attendance)
            db.commit()

            flash(
                f"{student.name} checked in at "
                f"{now.strftime('%I:%M:%S %p')}.",
                "success"
            )

            return redirect(
                url_for("check_in")
            )

        return render_template(
            "checkin.html",
            students=students_list
        )

    finally:

        db.close()


# =========================================================
# CHECK OUT
# =========================================================

@app.route(
    "/check-out",
    methods=["GET", "POST"]
)
def check_out():

    if not login_required():

        return redirect(
            url_for("login")
        )

    db = SessionLocal()

    try:

        records = db.query(
            Attendance,
            Student
        ).join(
            Student,
            Attendance.student_id == Student.id
        ).filter(
            Attendance.check_out_time.is_(None)
        ).order_by(
            Student.name
        ).all()

        if request.method == "POST":

            student_id = request.form.get(
                "student_id",
                ""
            ).strip()

            student = db.query(
                Student
            ).filter(
                Student.student_id == student_id
            ).first()

            if not student:

                flash(
                    "Student not found.",
                    "error"
                )

                return redirect(
                    url_for("check_out")
                )

            attendance = db.query(
                Attendance
            ).filter(
                Attendance.student_id == student.id,
                Attendance.check_out_time.is_(None)
            ).order_by(
                Attendance.check_in_time.desc()
            ).first()

            if not attendance:

                flash(
                    f"{student.name} must Check In first.",
                    "error"
                )

                return redirect(
                    url_for("check_out")
                )

            now = datetime.now()

            attendance.check_out_time = now
            attendance.status = "Completed"

            db.commit()

            hours = calculate_hours(
                attendance.check_in_time,
                now
            )

            flash(
                f"{student.name} checked out. "
                f"Total: {format_hours(hours)}.",
                "success"
            )

            return redirect(
                url_for("check_out")
            )

        open_students = [
            student
            for attendance, student in records
        ]

        return render_template(
            "checkout.html",
            students=open_students
        )

    finally:

        db.close()


# =========================================================
# ATTENDANCE
# =========================================================

@app.route("/attendance")
def attendance():

    if not login_required():

        return redirect(
            url_for("login")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    db = SessionLocal()

    try:

        query = db.query(
            Attendance,
            Student
        ).join(
            Student,
            Attendance.student_id == Student.id
        )

        if search:

            query = query.filter(
                (
                    Student.student_id.contains(
                        search
                    )
                )
                |
                (
                    Student.name.contains(
                        search
                    )
                )
            )

        records = query.order_by(
            Attendance.check_in_time.desc()
        ).all()

        return render_template(
            "attendance.html",
            records=records,
            search=search,
            calculate_hours=calculate_hours,
            format_hours=format_hours
        )

    finally:

        db.close()


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    if not login_required():

        return redirect(
            url_for("login")
        )

    student_search = request.args.get(
        "student",
        ""
    ).strip()

    from_text = request.args.get(
        "from_date",
        ""
    ).strip()

    to_text = request.args.get(
        "to_date",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        "All"
    )

    records = get_filtered_records(
        student_search,
        from_text,
        to_text,
        selected_status
    )

    grand_total = 0
    student_totals = {}

    for attendance_record, student in records:

        hours = calculate_hours(
            attendance_record.check_in_time,
            attendance_record.check_out_time
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
        student_search=student_search,
        from_text=from_text,
        to_text=to_text,
        selected_status=selected_status,
        grand_total=grand_total,
        student_totals=student_totals,
        calculate_hours=calculate_hours,
        format_hours=format_hours
    )


# =========================================================
# GET FILTERED RECORDS
# =========================================================

def get_filtered_records(
    student_search="",
    from_text="",
    to_text="",
    selected_status="All"
):

    db = SessionLocal()

    try:

        query = db.query(
            Attendance,
            Student
        ).join(
            Student,
            Attendance.student_id == Student.id
        )

        if student_search:

            query = query.filter(
                (
                    Student.student_id.contains(
                        student_search
                    )
                )
                |
                (
                    Student.name.contains(
                        student_search
                    )
                )
            )

        if from_text:

            try:

                from_day = datetime.strptime(
                    from_text,
                    "%d/%m/%Y"
                ).date()

                query = query.filter(
                    Attendance.check_in_time >=
                    datetime.combine(
                        from_day,
                        time.min
                    )
                )

            except ValueError:

                pass

        if to_text:

            try:

                to_day = datetime.strptime(
                    to_text,
                    "%d/%m/%Y"
                ).date()

                query = query.filter(
                    Attendance.check_in_time <=
                    datetime.combine(
                        to_day,
                        time.max
                    )
                )

            except ValueError:

                pass

        if selected_status in [
            "Present",
            "Completed"
        ]:

            query = query.filter(
                Attendance.status == selected_status
            )

        return query.order_by(
            Attendance.check_in_time.desc()
        ).all()

    finally:

        db.close()


# =========================================================
# EXPORT CSV
# =========================================================

@app.route("/reports/export/csv")
def export_report_csv():

    if not login_required():

        return redirect(
            url_for("login")
        )

    student_search = request.args.get(
        "student",
        ""
    ).strip()

    from_text = request.args.get(
        "from_date",
        ""
    ).strip()

    to_text = request.args.get(
        "to_date",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        "All"
    )

    records = get_filtered_records(
        student_search,
        from_text,
        to_text,
        selected_status
    )

    if not records:

        flash(
            "No records to export.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    os.makedirs(
        "exports",
        exist_ok=True
    )

    path = os.path.join(
        "exports",
        "attendance_report.csv"
    )

    export_csv(
        records,
        path
    )

    return send_file(
        path,
        as_attachment=True,
        download_name="attendance_report.csv",
        mimetype="text/csv"
    )


# =========================================================
# EXPORT PDF
# =========================================================

@app.route("/reports/export/pdf")
def export_report_pdf():

    if not login_required():

        return redirect(
            url_for("login")
        )

    student_search = request.args.get(
        "student",
        ""
    ).strip()

    from_text = request.args.get(
        "from_date",
        ""
    ).strip()

    to_text = request.args.get(
        "to_date",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        "All"
    )

    records = get_filtered_records(
        student_search,
        from_text,
        to_text,
        selected_status
    )

    if not records:

        flash(
            "No records to export.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    os.makedirs(
        "exports",
        exist_ok=True
    )

    path = os.path.join(
        "exports",
        "attendance_report.pdf"
    )

    export_pdf(
        records,
        path
    )

    return send_file(
        path,
        as_attachment=True,
        download_name="attendance_report.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )