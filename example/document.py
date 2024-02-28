import deform
import jsonschema_colander.types
from sqlmodel import Session
from winkel.router import APIView, RouteStore, Params
from winkel.services.flash import SessionMessages
from winkel import Application, User, Response, FormData, html, renderer
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

    @html
    @renderer(template='form/default')
    def GET(self, scope):
        form = document_creation_form(scope)
        return {
            "rendered_form": form.render()
        }

    @html
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
        return Response.redirect(url.environ.application_uri)


@routes.register(
    '/folders/{folder_id}/browse/{document_id}', name="document_view")
@html
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
