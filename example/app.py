import http_session_file
import pathlib
from pony import orm
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel.auth import Authenticator
from winkel.app import Application
from winkel.ui import UI
from winkel.ui.layout import Layout
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.request import Request
from winkel.middlewares import Transactional, HTTPSession, NoAnonymous
from winkel.services.flash import Flash
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


models.db.bind(provider='sqlite', filename='test.sqlite', create_db=True)
models.db.generate_mapping(create_tables=True)
app.services.register(orm.Database, instance=models.db)

app.services.register(actions.Actions, instance=actions.actions)

routes = register.routes | login.routes | views.routes


app.router |= routes


app.use(
    Transactional(),
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
        allowed_urls={'/register'}
    ),
    Flash()
)


if __name__ == "__main__":
    import bjoern

    wsgi_app = Fanstatic(app)
    bjoern.run(wsgi_app, "127.0.0.1", 8000)
