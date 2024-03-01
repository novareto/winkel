import datetime
import typing as t
from sqlmodel import SQLModel, Field, Relationship
from wrapt import ObjectProxy


class Traversed(ObjectProxy):
    __parent__: t.Any
    __trail__: str


class Company(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    courses: t.List["Course"] = Relationship(back_populates="company")


class Course(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    company_id: int = Field(foreign_key="company.id")

    sessions: t.List["Session"] = Relationship(back_populates="course")
    company: Company = Relationship(back_populates="courses")


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    scheduled_for: datetime.datetime
    course_id: int = Field(foreign_key="course.id")

    course: Course = Relationship(back_populates="sessions")

