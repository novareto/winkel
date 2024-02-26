from winkel.ui.rendering import ui_endpoint, template
from winkel.components.router import RouteStore
from winkel.auth import User
from winkel.app import Application


routes = RouteStore()


@routes.register('/')
@ui_endpoint
@template('views/index')
def index(request):
    application = request.get(Application)
    return {
        'user': request.get(User),
        'url_for': application.router.url_for
    }
