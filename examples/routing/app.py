import http_session_file
import pathlib
import vernacular
import logging.config
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel.ui import UI
from winkel.routing import Application
from winkel.templates import Templates
from winkel.policies import NoAnonymous
import register, login, views, actions, ui, folder, document, db
from winkel.services import (
    Transactional, HTTPSessions, Flash, SessionAuthenticator,
    SQLDatabase, TranslationService, PostOffice
)

app = Application()

app.services.register(actions.Actions, instance=actions.actions)
app.router = (
    register.routes | login.routes | views.routes | folder.routes | document.routes
)

vernacular.COMPILE = True
i18Catalog = vernacular.Translations()
for translation in vernacular.translations(pathlib.Path('translations')):
    i18Catalog.add(translation)


app.register_handler('scope.init')(
    NoAnonymous(
        login_url='/login',
        allowed_urls={'/register', '/test'}
    ).check_access
)


app.use(
    Transactional(),
    PostOffice(
        path='/tmp/test.mail'
    ),
    SQLDatabase(
        url="sqlite:///database.db"
    ),
    TranslationService(
        translations=i18Catalog,
        default_domain="routing",
        accepted_languages=["fr", "en", "de"]
    ),
    UI(
        slots=ui.slots,
        subslots=ui.subslots,
        layouts=ui.layouts,
        templates=Templates('templates'),
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
