from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from winkel.app import Root
from winkel.scope import Scope
from winkel.response import Response
from winkel.routing.router import Router, MatchedRoute, Params


@dataclass(kw_only=True, slots=True)
class Application(Root):
    router: Router = field(default_factory=Router)

    def __post_init__(self):
        self.services.add_instance(self, Application)
        self.services.add_instance(self.router, Router)

    def endpoint(self, scope: Scope) -> Response:
        route: MatchedRoute | None = self.router.match(
            scope.environ.path,
            scope.environ.method
        )
        if route is None:
            raise HTTPError(404)

        scope.register(MatchedRoute, route)
        scope.register(Params, route.params)
        self.notify('route.found', scope, route)
        return route(scope)
