import typing as t
import horseman.meta
from types import MappingProxyType
from dataclasses import dataclass, field
from horseman.mapping import Mapping
from horseman.response import Response
from horseman.http import HTTPError
from horseman.types import Environ, ExceptionInfo
from winkel.request import Query, Request, User
from winkel.pipeline import Pipeline
from winkel.ui import UI
from winkel.components import Subscribers, Router, MatchedRoute, Params
from horseman.types import Environ
from rodi import Container, ActivationScope
from horseman.http import Cookies
from horseman.parsers import Data


Config = t.Mapping[str, t.Any]


class Mounting(Mapping):

    def add(self, app: horseman.meta.Node, path: str):
        self[path] = app


def get_query(context) -> Query:
    request = context.get(Request)
    return request.query


def get_user(context) -> User:
    request = context.get(Request)
    return request.user


def get_params(context) -> Params:
    route = context.get(MatchedRoute)
    return route.params


def get_cookies(context) -> Cookies:
    request = context.get(Request)
    return request.cookies


def get_form_data(context) -> Data:
    request = context.get(Request)
    return request.extract()


@dataclass(kw_only=True)
class Application(horseman.meta.SentryNode):

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
        self.services.add_scoped_by_factory(get_user)
        self.services.add_scoped_by_factory(get_params)
        self.services.add_scoped_by_factory(get_form_data)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        pass

    def endpoint(self, request) -> Response:
        route = self.router.match(request.path, request.method)
        if route is None:
            raise HTTPError(404)

        scoped_services = {
            MatchedRoute: route,
            Request: request
        }
        with ActivationScope(
                self.services.provider, scoped_services) as context:
            request.cxt = context
            return route(request)

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            if (mounted := self.mounts.resolve(path, environ)) is not None:
                return mounted.resolve(path, environ)

        request = self.request_factory(environ)
        return self.pipeline.wrap(
            self.endpoint, MappingProxyType(self.config)
        )(request)
