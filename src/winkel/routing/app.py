from dataclasses import dataclass, field
from autorouting import MatchedRoute
from horseman.exceptions import HTTPError
from winkel.app import Root
from winkel.scope import Scope
from winkel.response import Response
from winkel.routing.router import Router, Params


@dataclass(kw_only=True, repr=False)
class Application(Root):
    router: Router = field(default_factory=Router)

    def __post_init__(self):
        super().__post_init__()
        self.services.add_instance(self.router, Router)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.router.finalize()
        super().finalize()

    def endpoint(self, scope: Scope) -> Response:
        route: MatchedRoute | None = self.router.get(
            scope.environ.path,
            scope.environ.method
        )
        if route is None:
            raise HTTPError(404)

        scope.register(MatchedRoute, route)
        scope.register(Params, route.params)
        return route.routed(scope)
