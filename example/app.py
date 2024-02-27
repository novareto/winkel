import http_session_file
import pathlib
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel.auth import SessionAuthenticator
from winkel.app import Application
from winkel.response import Response
from winkel.ui import UI
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.services import Transactional, HTTPSession, NoAnonymous, Flash
import register, login, views, actions, db, ui, folder, document


app = Application()


templates = Templates('./templates')
EXPRESSION_TYPES['slot'] = SlotExpr

ui = UI(
    slots=ui.slots,
    layouts=ui.layouts,
    templates=templates,
    resources={jquery}
)


app.services.register(actions.Actions, instance=actions.actions)
app.router |= (
    register.routes | login.routes | views.routes |
    folder.routes | document.routes
)

@app.router.register('/test/error')
def test2(scope):
    raise NotImplementedError("Damn")


app.use(
    Transactional(),
    db.SQLDatabase(url="sqlite:///database.db"),
    ui,
    HTTPSession(
        store=http_session_file.FileStore(
            pathlib.Path('./sessions'), 300
        ),
        secret="secret",
        salt="salt",
        cookie_name="cookie_name",
        secure=False,
        TTL=300
    ),
    SessionAuthenticator(
        sources=[db.DBSource()],
        user_key="user"
    ),
    NoAnonymous(
        login_url='/login',
        allowed_urls={'/register', '/test'}
    ),
    Flash()
)


wsgi_app = Fanstatic(app)


if __name__ == "__main__":
    import bjoern
    bjoern.run(wsgi_app, "127.0.0.1", 8000)
