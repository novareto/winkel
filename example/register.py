import colander
import deform
from horseman.parsers import Data
from models import Person
from winkel.response import Response
from winkel.components.router import RouteStore
from winkel.components.view import APIView
from winkel.services.flash import SessionMessages
from winkel.ui.rendering import ui_endpoint, template
from sqlalchemy.sql import exists
from sqlmodel import Session


routes = RouteStore()


def UniqueEmail(node, value):
    request = node.bindings['request']
    sqlsession = request.get(Session)
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


def register_form(request):
    schema = RegistrationSchema().bind(request=request)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


@routes.register('/register')
class Register(APIView):

    def namespace(self, request):
        return {'view': self}

    @ui_endpoint
    @template('form/default')
    def GET(self, request):
        form = register_form(request)
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
            form = register_form(request)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        sqlsession = request.get(Session)
        sqlsession.add(Person(**appstruct))

        flash = request.get(SessionMessages)
        flash.add('Account created.', type="info")
        return Response.redirect(request.environ.application_uri)
