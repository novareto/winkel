from autoroutes import Routes
from collections import UserDict
from typing import NamedTuple, Any
import fnmatch


class wildstr:

    def __init__(self, pattern):
        self.pattern = pattern

    def match(self, value):
        return fnmatch.fnmatch(value, self.pattern)


routes = Routes()

HTTPMethods = ("GET", "HEAD", "PUT", "DELETE", "PATCH", "POST", "OPTIONS")


class Route(NamedTuple):
    component: Any
    requirements: dict
    name: str | None = None
    priority: int = 0


class RouteGroup(UserDict[str, list[Route]]):

    def __setitem__(self, key, value):
        if key not in HTTPMethods:
            raise ValueError("Unknown method: {key}")
        super().__setitem__(key, value)

    def add(self, method, route, append=True):
        if method in self:
            if not append:
                raise KeyError("Route already populated.")
            if route in self[method]:
                raise ValueError('Route already exists.')
            for existing in self[method]:
                if existing == route:
                    raise ValueError('Equivalent route already exists.')
            self[method].append(route)
        else:
            self[method] = [route]
        self[method].sort(key=lambda r: -r.priority)


class Router(dict[str, RouteGroup]):

    def __init__(self, *args, **kwargs):
        self._routes = Routes()
        super().__init__(*args, **kwargs)

    def add(self, path: str, method: Any, component: Any, requirements: dict | None = None, priority: int = 0):
        route = Route(component, requirements, priority=priority)
        if path not in self:
            group = self[path] = RouteGroup()
            group.add(method, route)
        else:
            self[path].add(method, route)
        return route

    def match(self, path, method, extra: dict | None = None):
        group, params = self._routes.match(path)
        if group and method in group:
            for route in group[method]:
                if not route.requirements:
                    return route, params
                elif extra:
                    if set(route.requirements.keys()) <= set(extra.keys()):
                        for name, requirement in route.requirements.items():
                            if not requirement.match(extra[name]):
                                break
                        else:
                            return route, params

        return None, None

    def finalize(self):
        for path, group in self.items():
            self._routes.add(path, **group)


router = Router()

router.add('/', 'GET', 1, requirements={'user': wildstr('t?t?')}, priority=99)
router.add('/', 'GET', 2, priority=0)

router.finalize()

print(
    router.match('/', 'GET'),
    router.match('/', 'GET', extra={'user': 'titi'}),
    router.match('/', 'POST', extra={'user': 'toto'}),
    router.match('/', 'GET', extra={'user': 'ursula'}),
)