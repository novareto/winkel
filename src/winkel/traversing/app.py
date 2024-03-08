from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from winkel.app import Root
from winkel.scope import Scope
from winkel.routing import MatchedRoute, Params, Extra
from winkel.response import Response
from winkel.traversing.traverser import Traverser, ViewRegistry


@dataclass(kw_only=True)
class Application(Root):
    factories: Traverser = field(default_factory=Traverser)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def __post_init__(self):
        super().__post_init__()
        self.services.add_instance(self.views, ViewRegistry)
        self.services.add_scoped(Params)
        self.services.add_scoped(Extra)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.services.build_provider()
        self.factories.finalize()
        self.views.finalize()

    def endpoint(self, scope: Scope) -> Response:
        leaf, view_path = self.factories.traverse(
            self,
            scope.environ.path,
            'GET',
            scope,
            partial=True
        )
        if not view_path.startswith('/'):
            view_path = f'/{view_path}'

        extra = scope.get(Extra)
        view = self.views.match(
            leaf,
            view_path,
            scope.environ.method,
            extra=extra
        )
        if view is None:
            raise HTTPError(404)

        params = scope.get(Params)
        params |= view.params

        scope.register(MatchedRoute, view)
        return view.routed(scope, leaf)
