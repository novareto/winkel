import typing as t
import horseman.meta
from types import MappingProxyType
from dataclasses import dataclass, field
from horseman.mapping import Mapping
from horseman.response import Response
from horseman.http import HTTPError
from horseman.types import Environ, ExceptionInfo
from winkel.request import Request
from winkel.database import Database
from winkel.pipeline import Pipeline
from winkel.ui import UI
from winkel.components import (
    Actions, Subscribers, Contents, Router, VersionStore
)


class Mounting(Mapping):

    def add(self, app: horseman.meta.Node, path: str):
        self[path] = app


@dataclass
class Application(horseman.meta.SentryNode):

    name: str = ''
    request_factory: t.Type[Request] = Request
    database: t.Optional[Database] = None
    ui: UI = field(default_factory=UI)
    config: t.Mapping = field(default_factory=dict)
    router: Router = field(default_factory=Router)
    mounts: Mounting = field(default_factory=Mounting)
    actions: Actions = field(default_factory=Actions)
    subscribers: Subscribers = field(default_factory=Subscribers)
    schemas: VersionStore = field(default_factory=VersionStore)
    contents: Contents = field(default_factory=Contents)
    pipeline: Pipeline = field(default_factory=Pipeline)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        pass

    def endpoint(self, request) -> Response:
        route = self.router.match(request.path, request.method)
        if route is None:
            raise HTTPError(404)
        request.route = route
        return route(request)

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            if (mounted := self.mounts.resolve(path, environ)) is not None:
                return mounted.resolve(path, environ)
        request = self.request_factory(self, environ)
        return self.pipeline.wrap(
            self.endpoint, MappingProxyType(self.config)
        )(request)
