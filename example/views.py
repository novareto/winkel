from winkel.ui.rendering import ui_endpoint, template
from winkel.components.router import RouteStore


routes = RouteStore()


@routes.register('/')
@ui_endpoint
@template('views/index')
def index(request):
    return {
        'message': 'Woop !',
    }
