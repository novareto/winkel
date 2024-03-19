import inspect
import types
from typing import Sequence, Any, Type, get_args
from horseman.types import HTTPMethod
from plum import dispatch
from autorouting import Router as BaseRouter
from winkel.pipeline import HandlerWrapper, wrapper


METHODS = frozenset(get_args(HTTPMethod))
HTTPMethods = Sequence[HTTPMethod]


class Extra(dict):
    pass


class Params(dict):
    pass


class APIView:
    pass


@dispatch
def get_routables(
        view: types.FunctionType | types.CoroutineType,
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


class Router(BaseRouter):

    def register(self,
                 path: str,
                 methods: HTTPMethods = None,
                 pipeline: Sequence[HandlerWrapper] | None = None,
                 name: str | None = None,
                 requirements: dict | None = None,
                 priority: int = 0):
        def routing(value: Any):
            for endpoint, verbs in get_routables(value, methods):
                if pipeline:
                    endpoint = wrapper(pipeline, endpoint)
                for verb in verbs:
                    self.add(path, verb, endpoint,
                             name=name, requirements=requirements, priority=priority)
            return value
        return routing

    def path_for(self, name: str, **params):
        route_url = self.get_by_name(name)
        if route_url is not None:
            path, _ = route_url.resolve(params)
            return path
