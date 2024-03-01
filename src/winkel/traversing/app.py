from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from buckaroo import Registry as Trail
from winkel.app import Root
from winkel.scope import Scope
from winkel.routing import MatchedRoute, Params
from winkel.response import Response
from winkel.traversing.views import ViewRegistry


@dataclass(kw_only=True, slots=True)
class Application(Root):
    trail: Trail = field(default_factory=Trail)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def __post_init__(self):
        self.services.add_instance(self, Application)
        self.services.add_scoped(Params)

    def endpoint(self, scope: Scope) -> Response:
        leaf, view_path = self.trail.resolve(
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
        return view(scope, leaf)
