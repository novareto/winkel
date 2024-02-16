import typing as t
from types import MappingProxyType
from dataclasses import dataclass, field
from horseman.datastructures import Cookies
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from horseman.parsers import Data
from horseman.response import Response
from horseman.types import Environ, ExceptionInfo
from rodi import Container, ActivationScope
from winkel.components import Subscribers, Router, MatchedRoute, Params
from winkel.pipeline import Pipeline
from winkel.request import Query, Request, User, Environ
from winkel.ui import UI


Config = t.Mapping[str, t.Any]


class Mounting(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


def get_query(context) -> Query:
    request = context.get(Environ)
    return environ.query


def get_params(context) -> Params:
    route = context.get(MatchedRoute)
    return route.params


def get_cookies(context) -> Cookies:
    environ = context.get(Environ)
    return environ.cookies


def get_form_data(context) -> Data:
    environ = context.get(Environ)
    return environ.extract()


@dataclass(kw_only=True)
class Application(RootNode):

    name: str = ''
    ui: UI = field(default_factory=UI)
    request_factory: t.Type[Request] = Request
    services: Container = field(default_factory=Container)
    config: Config = field(default_factory=dict)
    router: Router = field(default_factory=Router)
    mounts: Mounting = field(default_factory=Mounting)
    subscribers: Subscribers = field(default_factory=Subscribers)
    pipeline: Pipeline = field(default_factory=Pipeline)

    def __post_init__(self):
        self.services.register(Application, instance=self)
        self.services.register(UI, instance=self.ui)
        self.services.register(Config, instance=self.config)
        self.services.add_scoped_by_factory(get_query)
        self.services.add_scoped_by_factory(get_cookies)
        self.services.add_scoped_by_factory(get_params)
        self.services.add_scoped_by_factory(get_form_data)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        pass

    def endpoint(self, request) -> Response:
        route = self.router.match(
            request.environ.path,
            request.environ.method
        )
        if route is None:
            raise HTTPError(404)

        request.scoped_services[MatchedRoute] = route
        with request:
            return route(request)

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            if (mounted := self.mounts.resolve(path, environ)) is not None:
                return mounted.resolve(path, environ)

        request = self.request_factory(environ, self.services.provider)
        return self.pipeline.wrap(
            self.endpoint, MappingProxyType(self.config)
        )(request)
