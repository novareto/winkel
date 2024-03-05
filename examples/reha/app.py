import http_session_file
import pathlib
import logging.config
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel.ui import UI
from winkel.traversing import Application
from winkel.templates import Templates
from winkel import services
import ui, views, login


app = Application(
    views=views.views|login.views
)


app.use(
    services.Transactional(),
    services.PostOffice(
        path='/tmp/test.mail'
    ),
    services.SQLDatabase(
        url="sqlite:///database.db"
    ),
    services.HTTPSessions(
        store=http_session_file.FileStore(
            pathlib.Path('sessions'), 3000
        ),
        secret="secret",
        salt="salt",
        cookie_name="cookie_name",
        secure=False,
        TTL=3000
    ),
    services.Flash(),
    UI(
        slots=ui.slots,
        subslots=ui.subslots,
        layouts=ui.layouts,
        templates=Templates('templates'),
        resources={jquery}
    )
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
            'level': 'INFO',
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

app.finalize()
wsgi_app = Fanstatic(app)
