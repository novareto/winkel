import colander
import deform
from horseman.parsers import Data
from winkel.response import Response
from winkel.components.view import APIView
from winkel.components.router import RouteStore
from winkel.auth import Authenticator
from winkel.services.flash import SessionMessages
from winkel.ui.rendering import html_endpoint, renderer


routes = RouteStore()


class LoginSchema(colander.Schema):

    username = colander.SchemaNode(
        colander.String(),
        title="Name"
    )

    password = colander.SchemaNode(
        colander.String(),
        title="password",
        widget=deform.widget.PasswordWidget()
    )


def login_form(scope):
    schema = LoginSchema().bind(scope=scope)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/login')
class Login(APIView):

    @html_endpoint
    @renderer(template='form/default')
    def GET(self, scope):
        form = login_form(scope)
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
            form = login_form(scope)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        authenticator = scope.get(Authenticator)
        user = authenticator.from_credentials(scope, appstruct)

        flash = scope.get(SessionMessages)
        if user is not None:
            authenticator.remember(scope, user)
            flash.add('Logged in.', type="success")
            return Response.redirect(scope.request.application_uri)

        # Login failed.
        flash.add('Login failed.', type="danger")
        return {
            "rendered_form": form.render()
        }


@routes.register('/logout')
def logout(scope):
    authenticator = scope.get(Authenticator)
    authenticator.forget(scope)
    flash = scope.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return Response.redirect(scope.request.application_uri)
