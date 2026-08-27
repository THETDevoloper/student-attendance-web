import os
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
)


# =========================================================
# DATABASE CONFIG
# =========================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///attendance.db"
)

# Render PostgreSQL URL compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


# SQLite configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False
        }
    )
else:
    engine = create_engine(
        DATABASE_URL
    )


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


# =========================================================
# STUDENT MODEL
# =========================================================

class Student(Base):

    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        String(50),
        unique=True,
        nullable=False
    )

    name = Column(
        String(200),
        nullable=False
    )

    gender = Column(
        String(20),
        nullable=True
    )

    phone = Column(
        String(50),
        nullable=True
    )

    email = Column(
        String(200),
        nullable=True
    )

    # Old Check In / Check Out relationship
    attendances = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    # New Daily Attendance relationship
    daily_attendances = relationship(
        "DailyAttendance",
        back_populates="student",
        cascade="all, delete-orphan"
    )


# =========================================================
# OLD ATTENDANCE MODEL
# =========================================================
# This model is kept unchanged so your existing
# Check In / Check Out system continues to work.
# =========================================================

class Attendance(Base):

    __tablename__ = "attendance"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    check_in_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    check_out_time = Column(
        DateTime,
        nullable=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="Present"
    )

    student = relationship(
        "Student",
        back_populates="attendances"
    )


# =========================================================
# DAILY ATTENDANCE MODEL
# =========================================================
# Used for:
#
# Present
# Absent
# Late
#
# One student can have only ONE daily attendance
# record for the same date.
# =========================================================

class DailyAttendance(Base):

    __tablename__ = "daily_attendance"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    attendance_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="Present"
    )

    note = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    student = relationship(
        "Student",
        back_populates="daily_attendances"
    )

    # Prevent duplicate attendance for the same
    # student on the same date.
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "attendance_date",
            name="uq_student_daily_attendance"
        ),
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    Base.metadata.create_all(
        bind=engine
    )


# =========================================================
# TEST / INITIALIZE
# =========================================================

if __name__ == "__main__":

    init_db()

    print(
        "Database initialized successfully."
    )