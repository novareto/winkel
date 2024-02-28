from winkel.ui.rendering import html_endpoint, json_endpoint, renderer
from winkel.components.router import RouteStore
from winkel.auth import User
from winkel.app import Application


routes = RouteStore()


@routes.register('/')
@html_endpoint
@renderer(template='views/index')
def index(scope):
    application = scope.get(Application)
    return {
        'user': scope.get(User),
        'url_for': application.router.url_for
    }


@routes.register('/test/bare')
@html_endpoint
@renderer
def bare(scope):
    return "This is my bare view"


@routes.register('/test/json')
@json_endpoint
def json(scope):
    return {"key": "value"}