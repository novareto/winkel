from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from winkel.app import Root
from winkel.scope import Scope
from winkel.response import Response
from winkel.routing.router import Router, MatchedRoute, Params


@dataclass(kw_only=True)
class Application(Root):
    router: Router = field(default_factory=Router)

    def __post_init__(self):
        super().__post_init__()
        self.services.add_instance(self.router, Router)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.services.build_provider()
        self.router.finalize()

    def endpoint(self, scope: Scope) -> Response:
        route: MatchedRoute | None = self.router.get(
            scope.environ.path,
            scope.environ.method
        )
        if route is None:
            raise HTTPError(404)

        scope.register(MatchedRoute, route)
        scope.register(Params, route.params)
        self.notify('route.found', scope, route)
        return route.handler(scope)
