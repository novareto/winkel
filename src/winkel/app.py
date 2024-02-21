import typing as t
from types import MappingProxyType
from rodi import Container
from pydantic import BaseModel, Field, ConfigDict
from horseman.datastructures import Cookies, Query
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from horseman.parsers import Data
from horseman.types import Environ, ExceptionInfo
from winkel.components import Subscribers, Router, MatchedRoute, Params
from winkel.pipeline import Pipeline
from winkel.request import Request, Environ
from winkel.response import Response
from winkel.ui import UI
from collections import defaultdict
from functools import partial
from winkel.datastructures import PriorityChain
import wrapt


Config = t.Mapping[str, t.Any]


class Mounting(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


def get_query(context) -> Query:
    environ = context.get(Environ)
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


@wrapt.decorator
def lifecycle(wrapped, instance, args, kwargs):
    if instance is None:
        raise NotImplementedError('Lifecycle needs to wrap an app method.')

    request = args[0]
    response = instance.trigger('request', *args, **kwargs)
    if response is not None:
        return response
    try:
        response = wrapped(*args, **kwargs)
        instance.trigger('response', request, response)
    except Exception as error:
        response = instance.trigger('error', request, error)
        if response is not None:
            return response
        raise
    else:
        return response


class Application(BaseModel, RootNode):

    model_config = ConfigDict(
        frozen=True,
        extra='allow',
        arbitrary_types_allowed=True
    )

    name: str = ''
    ui: UI = Field(default_factory=UI)
    request_factory: t.Type[Request] = Request
    services: Container = Field(default_factory=Container)
    router: Router = Field(default_factory=Router)
    mounts: Mounting = Field(default_factory=Mounting)
    hooks: dict = Field(default_factory=partial(defaultdict, set))

    def model_post_init(self, __context: t.Any) -> None:
        self.services.register(Application, instance=self)
        self.services.register(UI, instance=self.ui)
        self.services.add_scoped_by_factory(get_query)
        self.services.add_scoped_by_factory(get_cookies)
        self.services.add_scoped_by_factory(get_params)
        self.services.add_scoped_by_factory(get_form_data)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        pass

    def trigger(self, name: str, *args, **kwargs):
        if name in self.hooks:
            for hook in self.hooks[name]:
                response = hook(self, *args, **kwargs)
                if response is not None:
                    return response

    @lifecycle
    def endpoint(self, request: Request):
        route: MatchedRoute | None = self.router.match(
            request.environ.path,
            request.environ.method
        )
        if route is None:
            raise HTTPError(404)

        request.register(MatchedRoute, route)
        return route(request)

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            if (mounted := self.mounts.resolve(path, environ)) is not None:
                return mounted.resolve(path, environ)

        request = self.request_factory(environ, self.services.provider)
        with request:
            response = self.endpoint(request)
        return response
