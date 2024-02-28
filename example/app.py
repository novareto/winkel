import http_session_file
import pathlib
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel import Application, Response, UI
from winkel.auth import SessionAuthenticator
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.policies import NoAnonymous
from winkel.services import Transactional, Session, Flash
import register, login, views, actions, db, ui, folder, document, request
import logging.config


app = Application()
EXPRESSION_TYPES['slot'] = SlotExpr

app.services.register(actions.Actions, instance=actions.actions)
app.router |= (
    register.routes | login.routes | views.routes | folder.routes | document.routes
)


@app.router.register('/test/error')
def test2(scope):
    raise NotImplementedError("Damn")


app.register_handler('scope.init')(
    NoAnonymous(
        login_url='/login',
        allowed_urls={'/register', '/test'}
    ).check_access
)


app.use(
    request.Request(),
    Transactional(),
    db.SQLDatabase(
        url="sqlite:///database.db"
    ),
    UI(
        slots=ui.slots,
        layouts=ui.layouts,
        templates=Templates('./templates'),
        resources={jquery}
    ),
    Session(
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
    Flash()
)

# Run once at startup:
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'winkel': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
})



wsgi_app = Fanstatic(app)

if __name__ == "__main__":
    import bjoern
    bjoern.run(wsgi_app, "127.0.0.1", 8000)
