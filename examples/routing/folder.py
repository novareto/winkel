import deform
import jsonschema_colander.types
from sqlmodel import Session
from winkel.form import Form, trigger
from winkel.routing import Application, APIView, Router, Params
from winkel.services.flash import SessionMessages
from winkel.meta import FormData
from winkel import User, Response, html, renderer
from models import Folder


routes = Router()


folder_schema = jsonschema_colander.types.Object.from_json(
    Folder.model_json_schema(), config={
        "": {
            "exclude": ("id", "author_id")
        },
    }
)


@routes.register('/folders/new', name="folder_create")
class CreateFolder(Form):

    def get_schema(self, scope, *, context=None):
        return folder_schema()

    @trigger('add', 'Add new folder')
    def add(self, scope, data, *, context):
        form = self.get_form(scope, context=context)
        appstruct = form.validate(data)
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
        'path_for': application.router.path_for
    }
