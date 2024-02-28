import inspect
import orjson
import typing as t
from pathlib import Path
from horseman.types import HTTPMethod, WSGICallable
from winkel.components.view import APIView
from elementalist.element import Element


METHODS = frozenset(t.get_args(HTTPMethod))
HTTPMethods = t.Iterable[HTTPMethod]


def get_routables(view,
                  methods: t.Optional[HTTPMethods] = None
                  ) -> t.Iterator[t.Tuple[WSGICallable, HTTPMethods]]:

    def instance_members(inst):
        if methods is not None:
            raise AttributeError(
                'Registration of APIView does not accept methods.')
        members = inspect.getmembers(
            inst, predicate=(lambda x: inspect.ismethod(x)
                             and x.__name__ in METHODS))
        for name, func in members:
            yield func, [name]

    if inspect.isclass(view):
        inst = view()
        if isinstance(inst, APIView):
            yield from instance_members(inst)
        else:
            if methods is None:
                methods = {'GET'}

            unknown = set(methods) - METHODS
            if unknown:
                raise ValueError(
                    f"Unknown HTTP method(s): {', '.join(unknown)}")
            yield inst.__call__, methods
    elif isinstance(view, APIView):
        yield from instance_members(view)
    elif inspect.isfunction(view):
        if methods is None:
            methods = {'GET'}
        unknown = set(methods) - METHODS
        if unknown:
            raise ValueError(
                f"Unknown HTTP method(s): {', '.join(unknown)}")
        yield view, methods
    else:
        raise ValueError(f'Unknown type of route: {view}.')
