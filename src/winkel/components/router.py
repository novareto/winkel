import autoroutes
import typing as t
from frozendict import frozendict
from http import HTTPStatus
from prejudice.types import Predicate
from horseman.types import WSGICallable, HTTPMethod
from horseman.exceptions import HTTPError
from elementalist.element import Element
from elementalist.collections import ElementMapping
from winkel.components.utils import get_routables
from winkel.request import Scope


class Params(frozendict):
    pass


class Route(Element[str, WSGICallable]):

    method: HTTPMethod = 'GET'

    @property
    def path(self) -> str:
        return self.key


class MatchedRoute(t.NamedTuple):
    path: str
    route: Route
    method: HTTPMethod
    params: Params

    def __call__(self, scope: Scope):
        return self.route.secure_call(scope)


class RouteStore(ElementMapping[t.Tuple[str, HTTPMethod], Route]):

    ElementType: t.Type[Route] = Route
    _names: t.Mapping[str, str]

    def __init__(self, *args, extractor=get_routables, **kwargs):
        self.extractor = extractor
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
            for endpoint, verbs in self.extractor(value, methods):
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
