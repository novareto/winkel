import deform
import jsonschema_colander.types
from sqlmodel import Session
from winkel.router import APIView, RouteStore, Params
from winkel.services.flash import SessionMessages
from winkel import Application, User, Response, FormData, html, renderer
from models import Folder


routes = RouteStore()


folder_schema = jsonschema_colander.types.Object.from_json(
    Folder.model_json_schema(), config={
        "": {
            "exclude": ("id", "author_id")
        },
    }
)

def folder_creation_form(scope):
    schema = folder_schema().bind(scope=scope)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/folders/new', name="folder_create")
class CreateFolder(APIView):

    @html
    @renderer(template='form/default')
    def GET(self, scope):
        form = folder_creation_form(scope)
        return {
            "rendered_form": form.render()
        }

    @html
    @renderer(template='form/default')
    def POST(self, scope):
        data = scope.get(FormData)
        if ('process', 'process') not in data.form:
            raise NotImplementedError('No action found.')

        try:
            form = folder_creation_form(scope)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        sqlsession = scope.get(Session)
        user = scope.get(User)
        sqlsession.add(Folder(author_id=user.id, **appstruct))

        flash = scope.get(SessionMessages)
        flash.add('Folder created.', type="info")
        return Response.redirect(scope.environ.application_uri)


@routes.register('/folders/{folder_id}', name="folder_view")
@html
@renderer(template='views/folder')
def folder_view(scope):
    application = scope.get(Application)
    sqlsession = scope.get(Session)
    params = scope.get(Params)
    folder = sqlsession.get(Folder, params['folder_id'])
    return {
        "folder": folder,
        'url_for': application.router.url_for
    }
