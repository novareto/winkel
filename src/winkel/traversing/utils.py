from autorouting.url import RouteURL
from winkel.traversing import Application
from winkel.traversing.traverser import Traversed


class PathFragment(str):

    def __truediv__(self, other: str):
        if not other or other == '/':
            return self
        if self[-1] != '/':
            return PathFragment('/'.join((self, other.lstrip('/'))))
        return PathFragment('/'.join((self.rstrip('/'), other.lstrip('/'))))


def path_for(scope, context):

    def resolve_path(target, name, **params):
        root = scope.get(Application)

        if type(context) is Traversed:
            root_path = PathFragment(context.__path__)
        else:
            root_path = PathFragment('/')

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
        return root_path / factory_path / view_path

    return resolve_path
