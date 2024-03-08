import colander
import deform
from winkel.traversing import Application
from sqlmodel import Session as SQLSession, select
from winkel import Response, User, html, json, renderer
from winkel.response import Response
from winkel.traversing.traverser import ViewRegistry
from winkel.traversing.utils import path_for
from winkel import matchers
from form import Form, trigger
from models import Folder, Document
from store import Stores, SchemaKey


views = ViewRegistry()


@views.register(Application, '/', name="view")
@html
@renderer(template='views/index')
def root_index(scope, application):
    sqlsession = scope.get(SQLSession)
    query = select(Folder)
    folders = sqlsession.exec(query).all()
    return {
        'context': application,
        'folders': folders,
        'path_for': path_for(scope, application)
    }


@views.register(Folder, '/', name="view")
@html
@renderer(template='views/folder')
def folder_index(scope, folder):
    sqlsession = scope.get(SQLSession)
    query = select(Document).filter(Document.folder_id == folder.id)
    documents = sqlsession.exec(query).all()
    return {
        'context': folder,
        'documents': documents,
        'path_for': path_for(scope, folder)
    }


@views.register(Application, '/create_folder', name='create_folder')
class CreateFolder(Form):

    schema = Folder.get_schema(exclude=("id",))

    @trigger('save', 'Create new folder')
    def save(self, scope, data, context):
        form = self.get_form(scope, context)
        appstruct = form.validate(data)
        sqlsession = scope.get(SQLSession)
        sqlsession.add(
            Folder(
                **appstruct
            )
        )
        return Response.redirect(scope.environ.application_uri)


@colander.deferred
def deferred_choices_widget(node, kw):
    scope = kw.get("scope")
    stores = scope.get(Stores)
    choices = []
    for key, schema in stores['reha'].items():
        choices.append((SchemaKey("reha", *key), schema['description']))
    return deform.widget.SelectWidget(values=choices)


@views.register(Folder, '/create_document', name='create_document')
class CreateDocument(Form):

    schema = Document.get_schema(exclude=("id", "folder_id", "content"))
    schema['type'].widget = deferred_choices_widget

    @trigger('save', 'Create new document')
    def save(self, scope, data, context):
        form = self.get_form(scope, context)
        appstruct = form.validate(data)
        sqlsession = scope.get(SQLSession)
        sqlsession.add(
            Document(
                **appstruct,
                folder_id=context.id
            )
        )
        return Response.redirect(scope.environ.application_uri)


@views.register(
    Document, '/', name="view",
    requirements={"type": matchers.wildstr('schema2.1.2*')})
@html
def schema2_document_index(scope, document):
    return f"I use a schema2: {document.type}"



@views.register(
    Document, '/', name="view",
    requirements={"type": matchers.value('schema1.1.0@reha')})
@html
def schema1_document_index(scope, document):
    return f"I use a schema1: {document.type}"
