import colander
import deform
from horseman.parsers import Data
from winkel.response import Response
from winkel.components.view import APIView
from winkel.components.router import RouteStore
from winkel.auth import Authenticator
from winkel.services.flash import SessionMessages
from winkel.ui.rendering import ui_endpoint, template


routes = RouteStore()


class LoginSchema(colander.Schema):

    username = colander.SchemaNode(
        colander.String(),
        title="Name"
    )

    password = colander.SchemaNode(
        colander.String(),
        title="password"
    )


def login_form(request):
    schema = LoginSchema().bind(request=request)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/login')
class Login(APIView):

    def namespace(self, request):
        return {'view': self}

    @ui_endpoint
    @template('form/default')
    def GET(self, request):
        form = login_form(request)
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
            form = login_form(request)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        authenticator = request.get(Authenticator)
        user = authenticator.from_credentials(request, appstruct)

        flash = request.get(SessionMessages)
        if user is not None:
            authenticator.remember(request, user)
            flash.add('Logged in.', type="success")
            return Response.redirect(request.environ.application_uri)

        # Login failed.
        flash.add('Login failed.', type="danger")
        return {
            "rendered_form": form.render()
        }


@routes.register('/logout')
def logout(request):
    authenticator = request.get(Authenticator)
    authenticator.forget(request)
    flash = request.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return Response.redirect(request.environ.application_uri)
