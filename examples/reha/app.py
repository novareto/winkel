import http_session_file
import pathlib
import logging.config
from winkel.ui import UI
from winkel.resources import CSSResource, JSResource
from winkel.traversing import Application
from winkel.templates import Templates
from winkel.services.resources import ResourceManager
from winkel.services.token import JWTService
from winkel import services
import ui, views, store, factories, resources


here = pathlib.Path(__file__).parent.resolve()


libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_library(resources.static)
libraries.add_library(resources.my_super_lib)
libraries.add_library(resources.my_lib)
libraries.finalize()


app = Application(
    factories=factories.registry,
    views=views.views
)

app.services.add_instance(store.stores)


app.use(
    libraries,
    JWTService(
        private_key=here / 'identities' / 'jwt.priv',
        public_key=here / 'identities' / 'jwt.pub'
    ),
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
        templates=Templates('templates'),
        resources={
            CSSResource(
                "/bootstrap@5.0.2/dist/css/bootstrap.min.css",
                root="https://cdn.jsdelivr.net/npm",
                integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC",
                crossorigin="anonymous"
            ),
            CSSResource(
                "/bootstrap-icons@1.11.1/font/bootstrap-icons.css",
                root="https://cdn.jsdelivr.net/npm",
                integrity="sha384-4LISF5TTJX/fLmGSxO53rV4miRxdg84mZsxmO8Rx5jGtp/LbrixFETvWa5a6sESd",
                crossorigin="anonymous"
            ),
            JSResource(
                "/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js",
                root="https://cdn.jsdelivr.net/npm",
                bottom=True,
                integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM",
                crossorigin="anonymous"
            ),
            JSResource(
                "/jquery-3.7.1.min.js",
                root="https://code.jquery.com",
                integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=",
                crossorigin="anonymous"
            )
        }
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
