from sqlmodel import Session as SQLSession, select
from winkel.traversing import Application
from winkel.scope import Scope
from winkel.routing import Extra
from winkel.traversing import Traverser
from models import Folder, Document


registry = Traverser()


@registry.register(Application, '/folders/{folder_id}')
def folder_factory(
        scope: Scope, parent: Application,  *,
        folder_id: str) -> Folder:

    sqlsession = scope.get(SQLSession)
    folder = sqlsession.get(Folder, folder_id)
    return folder


@registry.register(Folder, '/documents/{document_id}')
def document_factory(
        scope: Scope, parent: Folder, *,
        document_id: str) -> Document:

    sqlsession = scope.get(SQLSession)
    query = select(Document).where(
        Document.id == document_id,
        Document.folder_id == parent.id
    )
    document = sqlsession.exec(query).one_or_none()
    extra = scope.get(Extra)
    extra["type"] = document.type
    return document
