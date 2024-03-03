import colander
import deform
from horseman.parsers import Data
from models import Person
from winkel.routing import APIView, Router
from winkel.services.flash import SessionMessages
from winkel import Scope, Response, html, renderer
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


def register_form(scope):
    schema = RegistrationSchema().bind(scope=scope)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/register')
class Register(APIView):

    @html
    @renderer(template='form/default')
    def GET(self, scope):
        form = register_form(scope)
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
            form = register_form(scope)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        sqlsession = scope.get(Session)
        sqlsession.add(Person(**appstruct))

        flash = scope.get(SessionMessages)
        flash.add('Account created.', type="info")
        return Response.redirect(scope.environ.application_uri)
