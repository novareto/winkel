import logging
from typing import Type, Iterator, Any
from rodi import Container
from dataclasses import dataclass, field
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from winkel.router import Router, MatchedRoute, Params
from winkel.scope import Scope
from winkel.response import Response
from winkel.service import Installable
from winkel.datastructures import PriorityChain
from winkel.meta import Environ, ExceptionInfo
from collections import defaultdict
from functools import partial
from elementalist.registries import SignatureMapping
from buckaroo import Registry as Trail, TypeMapping


logger = logging.getLogger(__name__)


class Mounting(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


@dataclass(kw_only=True, slots=True)
class Eventful:
    events: dict = field(default_factory=partial(defaultdict, PriorityChain))

    def register_handler(self, name: str, order: int = 0):
        def handler_registration(handler):
            self.events[name].add(handler, order)
        return handler_registration

    def trigger(self, name: str, *args, **kwargs):
        if name in self.events:
            for order, handler in self.events[name]:
                response = handler(*args, **kwargs)
                if response is not None:
                    logger.debug(f'{name}: handler {handler!r} responded. Breaking early.')
                    return response

    def notify(self, name: str, *args, **kwargs):
        if name in self.events:
            for order, hook in self.events[name]:
                hook(self, *args, **kwargs)


@dataclass(kw_only=True, slots=True)
class Application(Eventful, RootNode):

    name: str = ''
    services: Container = field(default_factory=Container)
    mounts: Mounting = field(default_factory=Mounting)

    def __post_init__(self):
        self.services.add_instance(self, Application)

    def use(self, *components: Installable):
        for component in components:
            component.install(self.services)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        typ, err, tb = exc_info
        logging.critical(err, exc_info=True)
        return Response(500, str(err))

    def endpoint(self, scope: Scope) -> Response:
        raise NotImplementedError('Implement your own.')

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


@dataclass(kw_only=True, slots=True)
class RoutingApplication(Application):
    router: Router = field(default_factory=Router)

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


class ViewRegistry(dict):

    @staticmethod
    def lineage(cls: Type):
        yield from cls.__mro__

    def lookup(self, cls: Type) -> Iterator[Router]:
        for parent in self.lineage(cls):
            if parent in self:
                yield self[parent]

    def register(self, root: Type, *args, **kwargs):
        router = self.setdefault(root, Router())
        return router.register(*args, **kwargs)

    def match(self, root: Any, path: str, method: str):
        for routes in self.lookup(root.__class__):
            matched: MatchedRoute | None = routes.match(path, method)
            if matched is not None:
                return matched


@dataclass(kw_only=True, slots=True)
class TraversingApplication(Application):
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
