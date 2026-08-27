import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)


# =========================================================
# CALCULATE HOURS
# =========================================================

def calculate_hours(
    check_in,
    check_out
):

    if not check_in or not check_out:
        return 0

    seconds = (
        check_out - check_in
    ).total_seconds()

    return max(
        0,
        seconds / 3600
    )


# =========================================================
# FORMAT HOURS
# =========================================================

def format_hours(hours):

    if hours is None:
        return "0h 0m"

    total_minutes = int(
        round(hours * 60)
    )

    hours_part = total_minutes // 60
    minutes_part = total_minutes % 60

    return (
        f"{hours_part}h "
        f"{minutes_part}m"
    )


# =========================================================
# EXPORT CSV
# =========================================================

def export_csv(
    records,
    filename
):

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Student ID",
            "Name",
            "Check In",
            "Check Out",
            "Status",
            "Total Hours"
        ])

        for attendance, student in records:

            hours = calculate_hours(
                attendance.check_in_time,
                attendance.check_out_time
            )

            check_in = (
                attendance.check_in_time.strftime(
                    "%d/%m/%Y %I:%M:%S %p"
                )
                if attendance.check_in_time
                else "-"
            )

            check_out = (
                attendance.check_out_time.strftime(
                    "%d/%m/%Y %I:%M:%S %p"
                )
                if attendance.check_out_time
                else "-"
            )

            writer.writerow([
                student.student_id,
                student.name,
                check_in,
                check_out,
                attendance.status,
                format_hours(hours)
            ])


# =========================================================
# EXPORT PDF
# =========================================================

def export_pdf(
    records,
    filename
):

    document = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Student Attendance Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    data = [[
        "Student ID",
        "Name",
        "Check In",
        "Check Out",
        "Status",
        "Hours"
    ]]

    for attendance, student in records:

        hours = calculate_hours(
            attendance.check_in_time,
            attendance.check_out_time
        )

        check_in = (
            attendance.check_in_time.strftime(
                "%d/%m/%Y %H:%M"
            )
            if attendance.check_in_time
            else "-"
        )

        check_out = (
            attendance.check_out_time.strftime(
                "%d/%m/%Y %H:%M"
            )
            if attendance.check_out_time
            else "-"
        )

        data.append([
            student.student_id,
            student.name,
            check_in,
            check_out,
            attendance.status,
            format_hours(hours)
        ])

    table = Table(
        data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#2563eb")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
        ])
    )

    elements.append(table)

    document.build(elements)