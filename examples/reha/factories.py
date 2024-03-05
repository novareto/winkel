from sqlmodel import Session as SQLSession, select
from winkel.traversing import Application
from winkel.scope import Scope
from winkel.traversing import Traverser
from models import Folder, Document


registry = Traverser()


@registry.register(Application, '/folders/<folder_id>')
def folder_factory(
        path: str, parent: Application, scope: Scope, *,
        folder_id: str) -> Folder:

    sqlsession = scope.get(SQLSession)
    folder = sqlsession.get(Folder, folder_id)
    return folder


@registry.register(Folder, '/documents/<document_id>')
def document_factory(
        path: str, parent: Folder, scope: Scope, *,
        document_id: str) -> Document:

    sqlsession = scope.get(SQLSession)
    query = select(Document).where(
        Document.id == document_id,
        Document.folder_id == parent.id
    )
    course = sqlsession.exec(query).one_or_none()
    return course
