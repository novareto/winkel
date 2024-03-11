import http_session_file
import pathlib
import logging.config
from js.jquery import jquery
from winkel.ui import UI
from winkel.traversing import Application
from winkel.templates import Templates
from winkel.services.resources import ResourceManager
from winkel import services
import ui, views, store, factories


here = pathlib.Path(__file__).parent.resolve()

libraries = ResourceManager('/static')
libraries.add_package_static('deform:static').finalize()
libraries.add_static('example', here / 'static').finalize(('*',))



app = Application(
    factories=factories.registry,
    views=views.views
)

app.services.add_instance(store.stores)


app.use(
    libraries,
    services.Transactional(),
    services.PostOffice(
        path='test.mail'
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
        templates=Templates('templates')
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
wsgi_app = app