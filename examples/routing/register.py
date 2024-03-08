import colander
import deform
from models import Person
from winkel.form import Form, trigger
from winkel.routing import Router
from winkel.services.flash import SessionMessages
from winkel import Scope, Response
from sqlalchemy.sql import exists
from sqlmodel import Session


routes = Router()


def UniqueEmail(node, value):
    scope: Scope = node.bindings['scope']
    sqlsession = scope.get(Session)
    if sqlsession.query(exists().where(Person.email == value)).scalar():
        raise colander.Invalid(node, "Email already in use.")


class RegistrationSchema(colander.Schema):

    name = colander.SchemaNode(
        colander.String(),
        title="Name",
        missing=None
    )

    email = colander.SchemaNode(
        colander.String(),
        title="Email",
        validator=colander.All(colander.Email(), UniqueEmail),
        missing=colander.required
    )

    age = colander.SchemaNode(
        colander.Integer(),
        title="Age",
        missing=colander.required,
        validator=colander.Range(
            min=18,
            min_err="You need to be at least 18 years old")
    )

    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5),
        missing=colander.required,
        widget=deform.widget.CheckedPasswordWidget(redisplay=True),
        description="Type your password and confirm it",
    )


@routes.register('/register')
class Register(Form):

    def get_schema(self, scope, *, context):
        return RegistrationSchema()

    @trigger('login', 'Login')
    def save(self, scope, data, *, context):
        form = self.get_form(scope, context=context)
        appstruct = form.validate(data)

        sqlsession = scope.get(Session)
        sqlsession.add(Person(**appstruct))

        flash = scope.get(SessionMessages)
        flash.add('Account created.', type="info")
        return Response.redirect(scope.environ.application_uri)
