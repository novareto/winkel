import deform
import jsonschema_colander.types
from sqlmodel import Session
from horseman.parsers import Data
from winkel.response import Response
from winkel.auth import User
from winkel.components.view import APIView
from winkel.components.router import RouteStore
from winkel.services.flash import SessionMessages
from winkel.ui.rendering import ui_endpoint, template
from winkel.components import Params
from winkel.app import Application
from models import Folder


routes = RouteStore()


folder_schema = jsonschema_colander.types.Object.from_json(
    Folder.model_json_schema(), config={
        "": {
            "exclude": ("id", "author_id")
        },
    }
)

def folder_creation_form(request):
    schema = folder_schema().bind(request=request)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/folders/new', name="folder_create")
class CreateFolder(APIView):

    def namespace(self, request):
        return {'view': self}

    @ui_endpoint
    @template('form/default')
    def GET(self, request):
        form = folder_creation_form(request)
        return {
            "rendered_form": form.render()
        }

    @ui_endpoint
    @template('form/default')
    def POST(self, request):
        data = request.get(Data)
        if ('process', 'process') not in data.form:
            raise NotImplementedError('No action found.')

        try:
            form = folder_creation_form(request)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        sqlsession = request.get(Session)
        user = request.get(User)
        sqlsession.add(Folder(author_id=user.id, **appstruct))

        flash = request.get(SessionMessages)
        flash.add('Folder created.', type="info")
        return Response.redirect(request.environ.application_uri)


@routes.register('/folders/{folder_id}', name="folder_view")
@ui_endpoint
@template('views/folder')
def folder_view(request):
    application = request.get(Application)
    sqlsession = request.get(Session)
    params = request.get(Params)
    folder = sqlsession.get(Folder, params['folder_id'])
    return {
        "folder": folder,
        'url_for': application.router.url_for
    }
