import datetime
import typing as t
import jsonschema_colander.types
from sqlmodel import SQLModel, Field, Relationship


class Model(SQLModel):

    @classmethod
    def get_schema(cls,
                   exclude: t.Iterable[str] | None = None,
                   include: t.Iterable[str] | None = None):
        return jsonschema_colander.types.Object.from_json(
            cls.model_json_schema(), config={
                "": {
                    "exclude": exclude,
                    "include": include
                },
            }
        )()


class Company(Model, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    courses: t.List["Course"] = Relationship(back_populates="company")


class Course(Model, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    company_id: int = Field(foreign_key="company.id")

    sessions: t.List["Session"] = Relationship(back_populates="course")
    company: Company = Relationship(back_populates="courses")


class Session(Model, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    scheduled_for: datetime.datetime
    course_id: int = Field(foreign_key="course.id")

    course: Course = Relationship(back_populates="sessions")
