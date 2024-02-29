import typing as t
from dataclasses import dataclass


@dataclass
class Traversable:
    parent: t.Any


@dataclass
class User(Traversable):
    id: str


@dataclass
class Folder(Traversable):
    name: str


@dataclass
class Document(Traversable):
    id: str


@dataclass
class Invoice(Document):
    pass