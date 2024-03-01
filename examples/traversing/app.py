import pathlib
from fanstatic import Fanstatic
import http_session_file
from js.jquery import jquery
from request import Request
from winkel.services import Session, Flash
from winkel.services.sqldb import SQLDatabase
from winkel.traversing import Application
from winkel.ui import UI
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
import factories, views, ui


EXPRESSION_TYPES['slot'] = SlotExpr


app = Application(
    trail=factories.trail,
)

app.views |= views.routes

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
    Session(
        store=http_session_file.FileStore(
            pathlib.Path('sessions'), 300
        ),
        secret="secret",
        salt="salt",
        cookie_name="cookie_name",
        secure=False,
        TTL=300
    ),
    Flash()
)


wsgi_app = Fanstatic(app)
