from winkel.traversing import Application
from winkel.traversing.traverser import Traversed
from winkel.routing.router import expand_url_params


def url_for(scope, context):
    def resolve_url(target, name, **params):
        root = scope.get(Application)
        route_stub = root.views.route_for(target, name, **params)
        if type(context) is Traversed:
            root_stub = context.__path__
        else:
            root_stub = ''

        if context.__class__ is target.__class__:
            return scope.environ.application_uri + root_stub + route_stub

        path = expand_url_params(
            *root.factories.reverse(
                target.__class__, context.__class__
            ),
            params
        )
        return scope.environ.application_uri + root_stub + path + route_stub

    return resolve_url
