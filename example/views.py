from winkel.ui.rendering import html, json, renderer
from winkel.components.router import RouteStore
from winkel.auth import User
from winkel.app import Application
from winkel.response import Response
from winkel.meta import Query


routes = RouteStore()


@routes.register('/')
@html
@renderer(template='views/index')
def index(scope):
    application = scope.get(Application)
    return {
        'user': scope.get(User),
        'url_for': application.router.url_for
    }


@routes.register('/test/bare')
@html
@renderer
def bare(scope):
    return "This is my bare view"


@routes.register('/test/json')
@json
def json(scope):
    return {"key": "value"}


def some_pipe(handler):
    def some_filter(scope):
        query = scope.get(Query)
        if query.get('die'):
            return Response(200, body='ouch, I died')
        import pdb
        pdb.set_trace()
        return handler(scope)
    return some_filter


@routes.register('/test/filtered', pipeline=(some_pipe,))
@html
@renderer
def filtered(scope):
    return "This is my filtered view"
