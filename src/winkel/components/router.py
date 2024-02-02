import autoroutes
import typing as t
from http import HTTPStatus
from dataclasses import dataclass, field
from prejudice.types import Predicate
from horseman.meta import Overhead, Environ
from horseman.types import WSGICallable, HTTPMethod
from horseman.http import HTTPError
from winkel.items import Item, ItemMapping
from winkel.request import Request
from winkel.components.utils import get_routables


@dataclass
class Route(Item[str, WSGICallable]):

    method: HTTPMethod = 'GET'

    @property
    def path(self) -> str:
        return self.identifier

    def __call__(self, request: Request, **kwargs):
        if self.conditions:
            if errors := self.evaluate(request, **kwargs):
                raise errors
        return self.value(request, **kwargs)


class MatchedRoute(t.NamedTuple):
    path: str
    route: Route
    method: HTTPMethod
    params: t.Mapping[str, t.Any]

    def __call__(self, request: Request):
        return self.route(request, **self.params)


class RouteStore(ItemMapping[t.Tuple[str, HTTPMethod], Route]):

    factory: t.Type[Route] = Route
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
        self[(route.identifier, route.method)] = route

    def spawn(self,
              value: WSGICallable,
              identifier: str,
              method: HTTPMethod,
              name: str = '',
              title: str = '',
              description: str = '',
              conditions: t.Optional[t.Iterable[Predicate]] = None,
              classifiers: t.Optional[t.Iterable[str]] = None,
              **metadata: t.Any
              ):

        if classifiers is None:
            classifiers = ()

        if conditions is None:
            conditions = ()

        return self.factory(
            identifier=identifier,
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
                 identifier: str,
                 methods: t.Optional[t.Iterable[HTTPMethod]] = None,
                 **kwargs):
        def routing(value: WSGICallable):
            for endpoint, verbs in self.extractor(value, methods):
                for method in verbs:
                    self.create(endpoint, identifier, method=method, **kwargs)
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
                params=params
            )

        raise HTTPError(HTTPStatus.METHOD_NOT_ALLOWED)
