from winkel.routing import Router
from winkel.meta import Query, Cookies
from winkel import Response, User, html, json, renderer
from winkel.routing import Application
from winkel.utils import ondemand


routes = Router()


@routes.register('/test/ondemand')
@html
@ondemand
def DI(user: User):
    import html
    return html.escape(str(user))



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
        return handler(scope)
    return some_filter


@routes.register('/test/filtered', pipeline=(some_pipe,))
@html
@renderer
def filtered(scope):
    return "This is my filtered view"


@routes.register('/test/error')
def test2(scope):
    raise NotImplementedError("Damn")
