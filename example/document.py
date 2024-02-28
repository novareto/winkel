import deform
import jsonschema_colander.types
from sqlmodel import Session
from horseman.parsers import Data
from winkel.response import Response
from winkel.auth import User
from winkel.components.view import APIView
from winkel.components.router import RouteStore
from winkel.services.flash import SessionMessages
from winkel.ui.rendering import html_endpoint, renderer
from winkel.meta import URLTools
from winkel.components import Params
from winkel.app import Application
from models import Document


routes = RouteStore()


document_schema = jsonschema_colander.types.Object.from_json(
    Document.model_json_schema(), config={
        "": {
            "exclude": ("id", "author_id", "folder_id")
        },

    }
)

def document_creation_form(scope):
    schema = document_schema().bind(scope=scope)
    schema['text'].widget = deform.widget.TextAreaWidget()
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/folders/{folder_id}/new', name="document_create")
class CreateDocument(APIView):

    @html_endpoint
    @renderer(template='form/default')
    def GET(self, scope):
        form = document_creation_form(scope)
        return {
            "rendered_form": form.render()
        }

    @html_endpoint
    @renderer(template='form/default')
    def POST(self, scope):
        data = scope.get(Data)
        if ('process', 'process') not in data.form:
            raise NotImplementedError('No action found.')

        try:
            form = document_creation_form(scope)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        sqlsession = scope.get(Session)
        params = scope.get(Params)
        user = scope.get(User)
        sqlsession.add(
            Document(
                author_id=user.id,
                folder_id=params['folder_id'],
                **appstruct
            )
        )
        flash = scope.get(SessionMessages)
        flash.add('Folder created.', type="info")
        url = scope.get(URLTools)
        return Response.redirect(url.application_uri)


@routes.register(
    '/folders/{folder_id}/browse/{document_id}', name="document_view")
@html_endpoint
@renderer(template='views/document')
def document_view(scope):
    application = scope.get(Application)
    sqlsession = scope.get(Session)
    params = scope.get(Params)
    document = sqlsession.get(Document, params['document_id'])
    return {
        "document": document,
        'url_for': application.router.url_for
    }
