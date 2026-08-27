import csv
import os

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.units import mm


# =========================================================
# CALCULATE HOURS
# =========================================================

def calculate_hours(check_in, check_out):

    if not check_in or not check_out:
        return 0.0

    seconds = (
        check_out - check_in
    ).total_seconds()

    return seconds / 3600


# =========================================================
# FORMAT HOURS
# =========================================================

def format_hours(hours):

    total_minutes = int(
        round(hours * 60)
    )

    h = total_minutes // 60
    m = total_minutes % 60

    return f"{h}h {m}m"


# =========================================================
# CSV
# =========================================================

def export_csv(records, filename):

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
            "Gender",
            "Check In",
            "Check Out",
            "Status",
            "Total Hours"
        ])

        for attendance, student in records:

            check_in = ""

            if attendance.check_in_time:
                check_in = attendance.check_in_time.strftime(
                    "%d/%m/%Y %I:%M:%S %p"
                )

            check_out = ""

            if attendance.check_out_time:
                check_out = attendance.check_out_time.strftime(
                    "%d/%m/%Y %I:%M:%S %p"
                )

            hours = calculate_hours(
                attendance.check_in_time,
                attendance.check_out_time
            )

            writer.writerow([
                student.student_id,
                student.name,
                student.gender or "",
                check_in,
                check_out,
                attendance.status or "",
                format_hours(hours)
            ])

    return os.path.abspath(filename)


# =========================================================
# PDF
# =========================================================

def export_pdf(
    records,
    filename,
    title="Student Attendance Report"
):

    document = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            title,
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 8)
    )

    generated = datetime.now().strftime(
        "%d/%m/%Y %I:%M:%S %p"
    )

    story.append(
        Paragraph(
            f"Generated: {generated}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 12)
    )

    data = [[
        "Student ID",
        "Name",
        "Gender",
        "Check In",
        "Check Out",
        "Status",
        "Total Hours"
    ]]

    grand_total = 0

    for attendance, student in records:

        check_in = ""

        if attendance.check_in_time:
            check_in = attendance.check_in_time.strftime(
                "%d/%m/%Y %I:%M %p"
            )

        check_out = "-"

        if attendance.check_out_time:
            check_out = attendance.check_out_time.strftime(
                "%I:%M %p"
            )

        hours = calculate_hours(
            attendance.check_in_time,
            attendance.check_out_time
        )

        grand_total += hours

        data.append([
            student.student_id,
            student.name,
            student.gender or "",
            check_in,
            check_out,
            attendance.status or "",
            format_hours(hours)
        ])

    data.append([
        "",
        "",
        "",
        "",
        "",
        "GRAND TOTAL",
        format_hours(grand_total)
    ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            30 * mm,
            45 * mm,
            25 * mm,
            43 * mm,
            35 * mm,
            30 * mm,
            30 * mm
        ]
    )

    table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.black
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -2),
                [
                    colors.white,
                    colors.lightgrey
                ]
            ),

            (
                "BACKGROUND",
                (0, -1),
                (-1, -1),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, -1),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )

    story.append(table)

    document.build(story)

    return os.path.abspath(filename)