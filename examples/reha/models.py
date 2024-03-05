import typing as t
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import JSON, Column
from pydantic import computed_field


class Folder(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    documents: t.List["Document"] = Relationship(back_populates="folder")

    @computed_field
    @property
    def document_count(self) -> int:
        return len(self.documents)


class Document(SQLModel, table=True):

    class Config:
        arbitrary_types_allowed = True

    id: int | None = Field(default=None, primary_key=True)
    title: str
    type: str
    content: dict = Field(default_factory=dict, sa_column=Column(JSON))
    folder_id: int = Field(foreign_key="folder.id")

    folder: Folder = Relationship(back_populates="documents")
