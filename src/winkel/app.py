import typing as t
import logging
from rodi import Container
from dataclasses import dataclass, field
from horseman.datastructures import Cookies, Query
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from horseman.parsers import Data
from horseman.types import Environ, ExceptionInfo
from winkel.components import Router, MatchedRoute, Params
from winkel.request import Scope, Request
from winkel.response import Response
from collections import defaultdict
from functools import partial


Config = t.Mapping[str, t.Any]


class Mounting(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


def get_query(scope) -> Query:
    environ = scope.get(Request)
    return environ.query


def get_params(scope) -> Params:
    route = scope.get(MatchedRoute)
    return route.params


def get_cookies(scope) -> Cookies:
    environ = scope.get(Request)
    return environ.cookies


def get_form_data(scope) -> Data:
    environ = scope.get(Request)
    return environ.extract()


@dataclass(kw_only=True, slots=True)
class Application(RootNode):

    name: str = ''
    request_factory: t.Type[Request] = Request
    services: Container = field(default_factory=Container)
    router: Router = field(default_factory=Router)
    mounts: Mounting = field(default_factory=Mounting)
    hooks: dict = field(default_factory=partial(defaultdict, set))

    def __post_init__(self) -> None:
        self.services.register(Application, instance=self)
        self.services.add_scoped_by_factory(get_query)
        self.services.add_scoped_by_factory(get_cookies)
        self.services.add_scoped_by_factory(get_params)
        self.services.add_scoped_by_factory(get_form_data)

    def use(self, *components):
        for component in components:
            component.install(self.services, self.hooks)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        typ, err, tb = exc_info
        logging.critical(err, exc_info=True)
        return Response(500, str(err))

    def trigger(self, name: str, *args, **kwargs):
        if name in self.hooks:
            for hook in self.hooks[name]:
                response = hook(self, *args, **kwargs)
                if response is not None:
                    return response

    def endpoint(self, scope: Scope) -> Response:
        response = self.trigger('before_route', scope)
        if response is not None:
            return response

        route: MatchedRoute | None = self.router.match(
            scope.request.path,
            scope.request.method
        )
        if route is None:
            raise HTTPError(404)

        scope.register(MatchedRoute, route)
        return route(scope)

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            if (mounted := self.mounts.resolve(path, environ)) is not None:
                return mounted.resolve(path, environ)

        scope = Scope(environ, provider=self.services.provider)
        with scope:
            with scope.stack:
                try:
                    response = self.endpoint(scope)
                except HTTPError as err:
                    response = Response(err.status, err.body)
                scope.register(Response, response)
                self.trigger('response', scope, response)
                return response
