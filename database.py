import os
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
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

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

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

    attendances = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan"
    )


# =========================================================
# ATTENDANCE MODEL
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
# INITIALIZE DATABASE
# =========================================================

def init_db():

    Base.metadata.create_all(
        bind=engine
    )


if __name__ == "__main__":

    init_db()

    print(
        "Database initialized successfully."
    )