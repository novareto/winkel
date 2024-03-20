import colander
import deform
import jsonschema_colander.types
from hamcrest import equal_to
from sqlmodel import Session as SQLSession, select
from winkel.traversing import Application
from winkel.traversing.utils import path_for
from winkel import Response, html, renderer
from winkel.traversing.traverser import ViewRegistry
from winkel import matchers
from winkel.form import Form, trigger

from models import Folder, Document
from store import Stores, SchemaKey
from resources import somejs


views = ViewRegistry()


@views.register(Application, '/', name="view")
@html(resources=[somejs])
@renderer(template='views/index')
def root_index(scope, *, context: Application):
    sqlsession = scope.get(SQLSession)
    query = select(Folder)
    folders = sqlsession.exec(query).all()
    return {
        'context': context,
        'folders': folders,
        'path_for': path_for(scope, context)
    }


@views.register(Folder, '/', name="view")
@html
@renderer(template='views/folder')
def folder_index(scope, *, context: Folder):
    sqlsession = scope.get(SQLSession)
    query = select(Document).filter(Document.folder_id == context.id)
    documents = sqlsession.exec(query).all()
    return {
        'context': context,
        'documents': documents,
        'path_for': path_for(scope, context)
    }


@views.register(Application, '/create_folder', name='create_folder')
class CreateFolder(Form):

    def get_schema(self, scope, *, context):
        return Folder.get_schema(exclude=("id",))

    @trigger('save', 'Create new folder')
    def save(self, scope, data, *, context: Application):
        form = self.get_form(scope, context=context)
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

    def get_schema(self, scope, *, context):
        schema = Document.get_schema(
            exclude=("id", "folder_id", "content")
        )
        schema['type'].widget = deferred_choices_widget
        return schema

    @trigger('save', 'Create new document')
    def save(self, scope, data, *, context):
        form = self.get_form(scope, context=context)
        appstruct = form.validate(data)
        sqlsession = scope.get(SQLSession)
        sqlsession.add(
            Document(
                **appstruct,
                folder_id=context.id
            )
        )
        return Response.redirect(scope.environ.application_uri)


@views.register(Document, '/edit', name="edit")
class EditDocument(Form):

    def get_schema(self, scope, *, context):
        stores = scope.get(Stores)
        key = SchemaKey.from_string(context.type)
        schema = stores[key.store].get((key.schema, key.version))
        return jsonschema_colander.types.Object.from_json(schema)()

    def get_initial_data(self, scope, *, context):
        return context.content

    @trigger('save', 'Update document')
    def save(self, scope, data, *, context):
        form = self.get_form(scope, context=context)
        appstruct = form.validate(data)
        context.content = appstruct
        resolver = path_for(scope, context)
        return Response.redirect(resolver(context, 'view'))


@views.register(
    Document, '/', name="view",
    requirements={"type": matchers.match_wildcards('schema2.1.2*')})
@html
@renderer
def schema2_document_index(scope, *, context: Document):
    return f"I use a schema2: {context.type}"


@views.register(
    Document, '/', name="view",
    requirements={"type": equal_to('schema1.1.0@reha')})
@html
@renderer
def schema1_document_index(scope, context: Document):
    return f"I use a schema1: {context.type}"
