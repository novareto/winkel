import http_session_file
import pathlib
import asyncio
import vernacular
import logging.config
import websockets
from threading import Thread
from winkel.ui import UI
from winkel.routing import Application
from winkel.templates import Templates
from winkel.policies import NoAnonymous
from winkel.resources import JSResource, CSSResource
import register, login, views, actions, ui, folder, document, db
from winkel.services.resources import ResourceManager
from winkel.services import (
    Transactional, HTTPSessions, Flash, SessionAuthenticator,
    SQLDatabase, TranslationService, PostOffice
)

app = Application(middlewares=[
    NoAnonymous(
        login_url='/login',
        allowed_urls={'/register', '/test'}
    )
])


here = pathlib.Path(__file__).parent.resolve()

libraries = ResourceManager('/static')
libraries.add_package_static('deform:static')
libraries.add_static('example', here / 'static', restrict=('*.jpg',))
libraries.finalize()


app.services.register(actions.Actions, instance=actions.actions)
app.router = (
    register.routes | login.routes | views.routes | folder.routes | document.routes
)

vernacular.COMPILE = True
i18Catalog = vernacular.Translations()
for translation in vernacular.translations(pathlib.Path('translations')):
    i18Catalog.add(translation)


app.use(
    libraries,
    Transactional(),
    PostOffice(
        path='test.mail'
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


async def websocket_handler(websocket):
    async for message in websocket:
        print(message)


async def websocket_server(app: Application):
    async with websockets.serve(websocket_handler, host="127.0.0.1", port=7000):
        await asyncio.Future()  # run forever


def background_loop(loop: asyncio.AbstractEventLoop, app: Application) -> None:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_server(app))


loop = asyncio.new_event_loop()
t = Thread(target=background_loop, args=(loop, app), daemon=True)
t.start()

wsgi_app = app
