from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from winkel.app import Root
from winkel.scope import Scope
from winkel.routing import MatchedRoute, Params
from winkel.response import Response
from winkel.traversing.traverser import Traverser, ViewRegistry


@dataclass(kw_only=True, slots=True)
class Application(Root):
    factories: Traverser = field(default_factory=Traverser)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def __post_init__(self):
        self.services.add_instance(self, Application)
        self.services.add_instance(self.views, ViewRegistry)
        self.services.add_scoped(Params)

    def endpoint(self, scope: Scope) -> Response:
        leaf, view_path = self.factories.traverse(
            self, scope.environ.path, scope, partial=True
        )
        if not view_path.startswith('/'):
            view_path = f'/{view_path}'
        view = self.views.match(leaf, view_path, scope.environ.method)
        if view is None:
            raise HTTPError(404)

        params = scope.get(Params)
        params |= view.params

        scope.register(MatchedRoute, view)
        return view.handler(scope, leaf)
