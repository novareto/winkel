import colander
import deform
from winkel.routing import APIView, Router
from winkel.services.flash import SessionMessages
from winkel.meta import FormData
from winkel.traversing import Application
from winkel import html, renderer, Response, Authenticator
from form import Form, trigger
from winkel.traversing.traverser import ViewRegistry


views = ViewRegistry()


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


@views.register(Application, '/login', name="login")
class Login(Form):

    schema = LoginSchema()

    @trigger('login', 'Authentify')
    def login(self, scope, data, context):
        form = self.get_form(scope, context)
        appstruct = form.validate(data)

        authenticator = scope.get(Authenticator)
        user = authenticator.from_credentials(scope, appstruct)

        flash = scope.get(SessionMessages)
        if user is not None:
            authenticator.remember(scope, user)
            flash.add('Logged in.', type="success")
            return Response.redirect(scope.environ.application_uri)

        # Login failed.
        flash.add('Login failed.', type="danger")
        return {
            "context": context,
            "rendered_form": form.render()
        }


@views.register(Application, '/logout', name="logout")
def logout(scope):
    authenticator = scope.get(Authenticator)
    authenticator.forget(scope)
    flash = scope.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return Response.redirect(scope.environ.application_uri)
