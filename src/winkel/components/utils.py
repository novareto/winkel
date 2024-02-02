import inspect
import orjson
import typing as t
from pathlib import Path
from horseman.types import HTTPMethod
from horseman.meta import APIView, WSGICallable
from winkel.items import Item


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


def get_schemas(path: Path):
    for f in path.iterdir():
        if f.suffix == '.json':
            with f.open('r') as fd:
                metaschema = orjson.loads(fd.read())
                namespace = metaschema.get("name", f.name)
                version = metaschema.get("$version", 1.0)
                permissions = metaschema.get('permissions', {})
                if version is not None:
                    version = float(version)

                yield Item(metaschema['schema'], version,
                           name=namespace,
                           title=metaschema.get('title', namespace),
                           metadata={
                               'ns': f"{namespace}.{version}",
                               'permissions': permissions
                           })
