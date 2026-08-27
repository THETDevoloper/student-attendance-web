from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


db = SQLAlchemy()


# =========================================================
# STUDENT
# =========================================================

class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    gender = db.Column(
        db.String(20)
    )

    phone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(100)
    )

    attendance_records = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan"
    )


# =========================================================
# ATTENDANCE
# =========================================================

class Attendance(db.Model):

    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    check_in_time = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    check_out_time = db.Column(
        db.DateTime,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Present"
    )

    student = relationship(
        "Student",
        back_populates="attendance_records"
    )