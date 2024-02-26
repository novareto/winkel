import http_session_file
import pathlib
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel.auth import Authenticator
from winkel.app import Application
from winkel.response import Response
from winkel.ui import UI
from winkel.ui.layout import Layout
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.request import Request
from winkel.services import Transactional, HTTPSession, NoAnonymous, Flash
import register, login, views, actions, db, ui, models


app = Application()


templates = Templates('./templates')
EXPRESSION_TYPES['slot'] = SlotExpr

ui = UI(
    slots=ui.slots,
    templates=templates
)

ui.layouts.create(Layout(templates['layout']), (Request,), "")
ui.resources.add(jquery)

app.services.register(actions.Actions, instance=actions.actions)

routes = register.routes | login.routes | views.routes


app.router |= routes


class Whatever:
    pass


from contextlib import contextmanager

@contextmanager
def mywhatever():
    whatever = Whatever()
    try:
        yield whatever
    except:
        print('oops')
    finally:
        print('closing my whatever')

def whatever_factory(scope) -> Whatever:
    whatever = scope.stack.enter_context(mywhatever())
    return whatever

app.services.add_scoped_by_factory(whatever_factory)

@app.router.register('/test/ok')
def test(request):
    print(request.get(Whatever))
    return Response(200, body=b'whatever')


@app.router.register('/test/ko')
def test2(request):
    print(request.get(Whatever))
    raise NotImplementedError("Damn")


app.use(
    Transactional(),
    db.SQLDatabase(url="sqlite:///database.db"),
    ui,
    Authenticator(
        sources=[db.DBSource()],
        user_key="user"
    ),
    HTTPSession(
        store=http_session_file.FileStore(
            pathlib.Path('./sessions'), 300),
        secret="secret",
        salt="salt",
        cookie_name="cookie_name",
        secure=False,
        TTL=300
    ),
    NoAnonymous(
        login_url='/login',
        allowed_urls={'/register', '/test'}
    ),
    Flash()
)

wsgi_app = Fanstatic(app)
