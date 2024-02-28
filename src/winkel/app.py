import logging
from rodi import Container
from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from horseman.types import Environ, ExceptionInfo
from winkel.components import Router, MatchedRoute, Params
from winkel.scope import Scope
from winkel.response import Response
from winkel.service import Installable
from winkel.datastructures import PriorityChain
from winkel.meta import URLTools
from collections import defaultdict
from functools import partial


logger = logging.getLogger(__name__)


class Mounting(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


@dataclass(kw_only=True, slots=True)
class Application(RootNode):

    name: str = ''
    services: Container = field(default_factory=Container)
    router: Router = field(default_factory=Router)
    mounts: Mounting = field(default_factory=Mounting)
    hooks: dict = field(default_factory=partial(defaultdict, PriorityChain))

    def __post_init__(self):
        self.services.add_instance(self, Application)

    def use(self, *components: Installable):
        for component in components:
            component.install(self.services)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        typ, err, tb = exc_info
        logging.critical(err, exc_info=True)
        return Response(500, str(err))

    def register_handler(self, name: str, order: int = 0):
        def handler_registration(handler):
            self.hooks[name].add(handler, order)
        return handler_registration

    def trigger(self, name: str, *args, **kwargs):
        if name in self.hooks:
            for order, hook in self.hooks[name]:
                response = hook(self, *args, **kwargs)
                if response is not None:
                    logger.debug(f'{name}: handler {hook!r} responded. Breaking early.')
                    return response

    def notify(self, name: str, *args, **kwargs):
        if name in self.hooks:
            for order, hook in self.hooks[name]:
                hook(self, *args, **kwargs)

    def endpoint(self, scope: Scope) -> Response:
        url = scope.get(URLTools)
        route: MatchedRoute | None = self.router.match(
            url.path,
            url.method
        )
        if route is None:
            raise HTTPError(404)

        scope.register(MatchedRoute, route)
        scope.register(Params, route.params)
        self.notify('route.found', scope, route)
        return route(scope)

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            if (mounted := self.mounts.resolve(path, environ)) is not None:
                return mounted.resolve(path, environ)

        scope = Scope(environ, provider=self.services.provider)
        with scope:
            with scope.stack:
                try:
                    response = self.trigger('scope.init', scope)
                    if response is None:
                        response = self.endpoint(scope)
                except HTTPError as err:
                    response = Response(err.status, err.body)
                except Exception as err:
                    raise
                scope.register(Response, response)
                self.notify('scope.response', scope, response)
                return response
