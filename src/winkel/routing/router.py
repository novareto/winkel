import re
import inspect
import types
from typing import Sequence, Any, NamedTuple, Type, get_args, Iterator
from sanic_routing import BaseRouter, Route
from sanic_routing.exceptions import RouteExists, NotFound
from horseman.types import HTTPMethod
from winkel.pipeline import HandlerWrapper, Handler, wrapper
from plum import dispatch
from imurl import URL


METHODS = frozenset(get_args(HTTPMethod))
HTTPMethods = Sequence[HTTPMethod]


class Params(dict):
    pass


class APIView:
    pass


@dispatch
def get_routables(
        view: types.FunctionType,
        methods: HTTPMethods | None = None):

    if methods is None:
        methods = {'GET'}
    else:
        unknown = set(methods) - METHODS
        if unknown:
            raise ValueError(
                f"Unknown HTTP method(s): {', '.join(unknown)}")
    yield view, methods


@dispatch
def get_routables(
        view: Type[APIView],
        methods: HTTPMethods | None = None):

    inst = view()
    if methods is not None:
        raise AttributeError(
            'Registration of APIView does not accept methods.')
    members = inspect.getmembers(
        inst, predicate=(lambda x: inspect.ismethod(x)
                         and x.__name__ in METHODS))
    for name, func in members:
        yield func, [name]


@dispatch
def get_routables(
        view: Type,
        methods: HTTPMethods | None = None):

    inst = view()
    if not callable(inst):
        raise AttributeError(
            f'Instance of {view!r} needs to be callable.')

    if methods is None:
        methods = {'GET'}
    else:
        unknown = set(methods) - METHODS
        if unknown:
            raise ValueError(
                f"Unknown HTTP method(s): {', '.join(unknown)}")
    yield inst, methods


class MatchedRoute(NamedTuple):
    route: Route
    handler: Handler
    params: Params


def expand_url_params(path: str, params: Sequence, kwargs):
    for param_info in params:
        try:
            supplied_param = str(kwargs.pop(param_info.name))
        except KeyError:
            raise KeyError(
                f"Required parameter `{param_info.name}` was not "
                "passed to url_for"
            )

        # determine if the parameter supplied by the caller
        # passes the test in the URL
        if param_info.pattern:
            pattern = (
                param_info.pattern[1]
                if isinstance(param_info.pattern, tuple)
                else param_info.pattern
            )
            passes_pattern = pattern.match(supplied_param)
            if not passes_pattern:
                if param_info.cast != str:
                    msg = (
                        f'Value "{supplied_param}" '
                        f"for parameter `{param_info.name}` does "
                        "not match pattern for type "
                        f"`{param_info.cast.__name__}`: "
                        f"{pattern.pattern}"
                    )
                else:
                    msg = (
                        f'Value "{supplied_param}" for parameter '
                        f"`{param_info.name}` does not satisfy "
                        f"pattern {pattern.pattern}"
                    )
                raise TypeError(msg)

            # replace the parameter in the URL with the supplied value
        replacement_regex = f"(<{param_info.name}.*?>)"
        path = re.sub(replacement_regex, supplied_param, path)
    return path

class Router(BaseRouter):
    DEFAULT_METHOD = "GET"
    ALLOWED_METHODS = METHODS

    def get(self, path, method: HTTPMethod | None = None):
        if method is None:
            method = self.DEFAULT_METHOD
        try:
            route, handler, params = self.resolve(path, method=method)
            return MatchedRoute(route, handler, Params(params))
        except NotFound:
            return None

    def register(self,
                 path: str,
                 methods: HTTPMethods = None,
                 pipeline: Sequence[HandlerWrapper] | None = None,
                 **kwargs):
        def routing(value: Any):
            for endpoint, verbs in get_routables(value, methods):
                if pipeline:
                    endpoint = wrapper(pipeline, endpoint)
                self.add(path, endpoint, methods=verbs, **kwargs)
            return value
        return routing

    def all_routes(self) -> Iterator[Route]:
        for group in self.static_routes.values():
            yield from group
        for group in self.dynamic_routes.values():
            yield from group
        for group in self.regex_routes.values():
            yield from group

    def __or__(self, other) -> 'Router':
        router = Router()
        for merger in (self, other):
            for route in merger.all_routes():
                try:
                    router.add(
                        route.path,
                        route.handler,
                        route.methods,
                        name=route.name,
                        requirements=route.requirements,
                        overwrite=False,
                        priority=route.priority,
                        append=False
                    )
                except RouteExists:
                    pass
        return router

    def __ior__(self, other: 'Router') -> 'Router':
        for route in other.all_routes():
            try:
                self.add(
                    route.path,
                    route.handler,
                    route.methods,
                    route.name,
                    requirements=route.requirements,
                    priority=route.priority,
                    overwrite=False,
                    append=False
                )
            except RouteExists:
                pass
        return self

    def url_for(self, view_name: str, **kwargs) -> URL:
        """Build a URI based on a view name and the values provided.
        """
        route = self.name_index.get(view_name)
        if not route:
            raise LookupError(
                f"Endpoint with name `{view_name}` was not found"
            )

        uri = route.path
        if (
            uri != "/"
            and uri.endswith("/")
            and not route.strict
            and not route.raw_path[:-1]
        ):
            uri = uri[:-1]

        if not uri.startswith("/"):
            uri = f"/{uri}"

        out = uri
        if route.static:
            return URL(path=out)

        route.finalize()
        out = expand_url_params(out, route.params.values(), kwargs)
        return URL(path=out, query_dict=kwargs)
