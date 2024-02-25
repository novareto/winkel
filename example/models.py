from sqlmodel import Field, Session, SQLModel, create_engine, select


class Person(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    name: str | None = None
    age: int
    password: str
