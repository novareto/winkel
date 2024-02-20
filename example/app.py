import http_session_file
import pathlib
import colander
import deform
from pony import orm
from typing import Any
from fanstatic import Fanstatic
from js.jquery import jquery
from horseman.parsers import Data
from prejudice.errors import ConstraintError
from winkel.auth import Authenticator, User, Source, anonymous
from winkel.app import Application
from elementalist.registries import NamedElementRegistry
from winkel.ui.rendering import ui_endpoint, template
from winkel.ui.layout import Layout
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.request import Request
from winkel.response import Response
from winkel.components.view import APIView
from winkel.pipes import Transactional, HTTPSession, Authentication
from winkel.pipes.flash import flash_service, SessionMessages


app = Application()
templates = Templates('./templates')
EXPRESSION_TYPES['slot'] = SlotExpr


app.ui.layouts.create(Layout(templates['layout']), (Request,), "")
app.ui.templates |= templates
app.ui.resources.add(jquery)


db = orm.Database()

class Person(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    email = orm.Required(str, unique=True)
    name = orm.Optional(int)
    age = orm.Required(int)
    password = orm.Required(str)


db.bind(provider='sqlite', filename='test.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


class DBSource(Source):

    def find(self, credentials: dict, request: Request) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        with orm.db_session:
            p = Person.get(email=username)
            if p is not None and p.password == password:
                user = User()
                user.id = p.id
                return user

    def fetch(self, uid, request) -> User | None:
        with orm.db_session:
            p = Person[uid]
            user = User()
            user.id = p.id
            return user


class Actions(NamedElementRegistry):
    ...


actions = Actions()
app.services.register(Actions, instance=actions)
app.services.register(orm.Database, instance=db)
app.services.add_scoped_by_factory(flash_service)


Transactional().install(app, 10)
HTTPSession(
    store=http_session_file.FileStore(
        pathlib.Path('./sessions'), 300),
    secret="secret",
    salt="salt",
    cookie_name="cookie_name",
    secure=False,
    TTL=300
).install(app, 20)
Authentication(sources=[DBSource()]).install(app, 30)


@app.router.register('/')
@ui_endpoint
@template(templates['views/index'])
def index(request):
    return {
        'message': 'Woop !',
    }


@app.router.register('/logout')
def logout(request):
    authenticator = request.get(Authenticator)
    authenticator.forget(request)
    flash = request.get(SessionMessages)
    flash.add('Logged out.', type="warning")
    return Response.redirect(request.environ.application_uri)


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


def UniqueEmail(node, value):
    with orm.db_session:
        if Person.exists(email=value):
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


@app.router.register('/login')
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


@app.router.register('/register')
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

        with orm.db_session:
            Person(**appstruct)

        flash = request.get(SessionMessages)
        flash.add('Account created.', type="info")
        return Response.redirect(request.environ.application_uri)


def is_not_anonymous(action, request, view, context):
    if request.get(User) is anonymous:
        raise ConstraintError('User is anonymous.')


def is_anonymous(action, request, view, context):
    if request.get('user') is not anonymous:
        raise ConstraintError('User is not anonymous.')


@actions.register((Request, Any, Any), name='login', title='Login', description='Login action', conditions=(is_anonymous,))
def login_action(request, view, item):
    return '/login'


@actions.register((Request, Any, Any), name='logout', title='Logout', description='Logout action', conditions=(is_not_anonymous,))
def logout_action(request, view, item):
    return '/logout'


@app.ui.slots.register((Request, Any, Any), name='actions')
@template('slots/actions')
def actions(request, view, context, slots):
    registry = request.get(Actions)
    matching = registry.match(request, view, context)
    evaluated = []
    for name, action in matching.items():
        result = action.conditional_call(request, view, context)
        if result is not None:
            evaluated.append((action, result))
    return {
        "actions": evaluated
    }


@app.ui.slots.register((Request, Any, Any), name='above_content')
class AboveContent:

    def namespace(self, request):
        return {'manager': self}

    @template(templates['slots/above'])
    def __call__(self, request, view, context, slots):
        items = []
        for slot in slots:
            result = slot.conditional_call(request, self, view, context)
            if result is not None:
                items.append(result)
        return {'items': items}


@app.ui.slots.register((Request, AboveContent, Any, Any), name='messages')
@template('slots/messages')
def messages(request, manager, view, context):
    flash = request.get(SessionMessages)
    return {'messages': list(flash)}


@app.ui.slots.register((Request, AboveContent, Any, Any), name='identity')
def identity(request, manager, view, context):
    who_am_i = request.get(User)
    if who_am_i is anonymous:
        return "<div class='container alert alert-secondary'>Not logged in. Please consider creating an account or logging in.</div>"
    return f"<div class='container alert alert-info'>You are logged in as {who_am_i.id}</div>"


if __name__ == "__main__":
    import bjoern

    wsgi_app = Fanstatic(app)
    bjoern.run(wsgi_app, "127.0.0.1", 8000)
