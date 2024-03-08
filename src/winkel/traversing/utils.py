from autorouting.url import RouteURL
from winkel.traversing import Application
from winkel.traversing.traverser import Traversed


def url_for(scope, context):
    def resolve_url(target, name, **params):
        root = scope.get(Application)

        if type(context) is Traversed:
            root_path = context.__path__
        else:
            root_path = ''

        if context.__class__ is not target.__class__:
            traversal_path = root.factories.reverse(
                target.__class__,
                context.__class__
            )
            factory_path, unmatched = RouteURL.from_path(
                traversal_path
            ).resolve(params, qstring=False)
        else:
            factory_path = ''
            unmatched = {}

        view_path = root.views.route_for(target, name, **unmatched)
        return scope.environ.application_uri + root_path + factory_path + view_path

    return resolve_url
