import autoroutes
import typing as t
import types
import inspect
from http import HTTPStatus
from plum import dispatch
from prejudice.types import Predicate
from elementalist.collections import ElementMapping
from elementalist.element import Element
from horseman.exceptions import HTTPError
from horseman.types import HTTPMethod
from horseman.types import WSGICallable, HTTPMethod
from winkel.pipeline import HandlerWrapper, wrapper
from winkel.scope import Scope


METHODS = frozenset(t.get_args(HTTPMethod))
HTTPMethods = t.Iterable[HTTPMethod]


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
        view: t.Type[APIView],
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
        view: t.Type,
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
    yield inst.__call__, methods


class Params(dict):
    pass


class Route(Element[str, WSGICallable]):
    method: HTTPMethod = 'GET'
    pipeline: t.Tuple[HandlerWrapper,...] | None = None

    @property
    def path(self) -> str:
        return self.key


class MatchedRoute(t.NamedTuple):
    path: str
    route: Route
    method: HTTPMethod
    params: Params

    def __call__(self, scope: Scope):
        if self.route.pipeline is not None:
            return wrapper(
                self.route.pipeline, self.route.secure_call)(scope)
        return self.route.secure_call(scope)


class RouteStore(ElementMapping[t.Tuple[str, HTTPMethod], Route]):

    ElementType: t.Type[Route] = Route
    _names: t.Mapping[str, str]

    def __init__(self, *args, **kwargs):
        self._names = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, route):
        if route.name:
            if existing := self._names.get(route.name):
                if existing != route.path:
                    raise NameError('Route already existing')
            else:
                self._names[route.name] = route.path
        super().__setitem__(key, route)

    def add(self, route: Route):
        self[(route.key, route.method)] = route

    def has_route(self, name: str):
        return name in self._names

    def url_for(self, name: str, **params):
        path = self._names.get(name)
        if path is None:
            raise LookupError(f'Unknown route `{name}`.')
        try:
            # Raises a KeyError too if some param misses
            # FIXME : this doesn't handle typed params
            #         such as {param_name:string}
            return path.format(**params)
        except KeyError:
            raise ValueError(
                f"No route found with name {name} and params {params}.")

    def factory(self,
                value: WSGICallable,
                key: str,
                method: HTTPMethod,
                name: str = '',
                title: str = '',
                pipeline: t.Iterable[HandlerWrapper] | None = None,
                description: str = '',
                conditions: t.Optional[t.Iterable[Predicate]] = None,
                classifiers: t.Optional[t.Iterable[str]] = None,
                **metadata: t.Any) -> Route:

        if classifiers is None:
            classifiers = ()

        if conditions is None:
            conditions = ()

        return self.ElementType(
            key=key,
            name=name,
            method=method,
            title=title,
            value=value,
            pipeline=pipeline,
            description=description,
            classifiers=frozenset(classifiers),
            conditions=tuple(conditions),
            metadata=metadata
        )

    def register(self,
                 key: str,
                 methods: t.Optional[t.Iterable[HTTPMethod]] = None,
                 **kwargs):
        def routing(value: WSGICallable):
            for endpoint, verbs in get_routables(value, methods):
                for method in verbs:
                    self.create(endpoint, key, method=method, **kwargs)
            return value
        return routing


class Router(RouteStore):

    routes = autoroutes.Routes

    def __init__(self, *args, **kwargs):
        self.routes = autoroutes.Routes()
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, route):
        super().__setitem__(key, route)
        self.routes.add(route.path, **{route.method: route})

    def __ior__(self, other):
        for key, route in other.items():
            self[key] = route
        return self

    def match(self,
              path: str,
              method: HTTPMethod) -> t.Optional[MatchedRoute]:

        found, params = self.routes.match(path)
        if found is None:
            return None

        if route := found.get(method):
            return MatchedRoute(
                path=path,
                route=route,
                method=method,
                params=Params(params)
            )

        raise HTTPError(HTTPStatus.METHOD_NOT_ALLOWED)
