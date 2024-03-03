import pathlib
from fanstatic import Fanstatic
import http_session_file
from js.jquery import jquery
from request import Request
from winkel.services import Flash, HTTPSessions, SQLDatabase
from winkel.traversing import Application
from winkel.ui import UI
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
import factories, views, ui


EXPRESSION_TYPES['slot'] = SlotExpr


app = Application()

app.views |= views.routes
app.factories |= factories.registry

app.use(
    Request(),
    SQLDatabase(
        url="sqlite:///traversing.db"
    ),
    UI(
        templates=Templates('templates'),
        slots=ui.slots,
        layouts=ui.layouts,
        resources={jquery}
    ),
    HTTPSessions(
        store=http_session_file.FileStore(
            pathlib.Path('sessions'), 3000
        ),
        secret="secret",
        salt="salt",
        cookie_name="cookie_name",
        secure=False,
        TTL=3000
    ),
    Flash()
)

app.finalize()
wsgi_app = Fanstatic(app)
