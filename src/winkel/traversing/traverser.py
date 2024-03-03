import typing as t
from wrapt import ObjectProxy
from pathlib import PurePosixPath
from inspect import signature, _empty as empty, isclass
from collections import defaultdict
from winkel.pipeline import wrapper
from winkel.routing.router import Router, Route, HTTPMethods, get_routables
from winkel.datastructures import TypeMapping


class Traversed(ObjectProxy):
    __parent__: t.Any
    __route__: Route
    __path__: str

    def __init__(self, wrapped, *, parent: t.Any, route: Route, path: str):
        super().__init__(wrapped)
        self.__parent__ = parent
        self.__route__ = route
        if type(parent) is Traversed:
            self.__path__ = f"{parent.__path__}/{path}"
        else:
            self.__path__ = path


def paths(path: str) -> t.Tuple[str, str]:
    root = PurePosixPath(path)
    parents = list(root.parents)
    yield str(root), ''
    for parent in parents[:-1]:
        yield str(parent), '/' + str(root.relative_to(parent))


class Node:

    def __init__(self, cls, route):
        self.cls = cls
        self.route = route

    def __hash__(self):
        return hash(self.cls)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.cls == other.cls and self.route == other.route
        elif isclass(other):
            return other == self.cls
        raise TypeError(f"Cannot establish equality between {self!r} and {other!r}")

    def __repr__(self):
        return f'{self.cls} -> {self.route}'


class Traverser:

    __slots__ = ('_reverse', '_routers')

    def __init__(self):
        self._routers: t.Dict[t.Type, Router] = defaultdict(Router)
        self._reverse: TypeMapping[t.Any, Node] = TypeMapping()

    def finalize(self):
        for router in self._routers.values():
            router.finalize()

    @staticmethod
    def lineage(cls):
        yield from cls.__mro__

    def lookup(self, cls) -> t.Optional[Router]:
        for parent in self.lineage(cls):
            if parent in self._routers:
                yield self._routers[parent]

    def add(self, root: t.Type[t.Any], path: str, factory: t.Callable, **kwargs):
        sig = signature(factory)
        if sig.return_annotation is empty:
            raise TypeError('Factories need to specify a return type.')
        route = self._routers[root].add(path, factory, **kwargs)
        self._reverse.add(sig.return_annotation, Node(root, route))
        return route

    def register(self,
                 root: t.Type,
                 path: str,
                 pipeline = None,
                 methods: HTTPMethods | None = None,
                 **kwargs):
        def routing(value: t.Any):
            for endpoint, verbs in get_routables(value, methods):
                if pipeline:
                    endpoint = wrapper(pipeline, endpoint)
                self.add(root, path, endpoint, methods=verbs, **kwargs)
            return value
        return routing

    def resolve(
            self,
            root: t.Any,
            path: str,
            context: t.Optional[t.Mapping] = None,
            partial: bool = None) -> t.Tuple[t.Any, str]:

        explore = tuple(paths(path))
        for matcher in self.lookup(root.__class__):
            for stub, branch in explore:
                found = matcher.get(stub)
                if found:
                    resolved = found.handler(stub, root, context, **found.params)
                    resolved = Traversed(resolved, parent=root, route=found.route, path=stub)
                    if not branch:
                        return resolved, ''
                    else:
                        return self.resolve(resolved, branch, context=context, partial=partial)
        if partial:
            return root, path
        raise LookupError()

    def reverse(self, node1, node2):
        path_list = [[node1]]
        path_index = 0

        # To keep track of previously visited nodes
        previous_nodes = {node1}
        if node1 == node2:
            return path_list[0]

        while path_index < len(path_list):
            current_path = path_list[path_index]
            last_node = current_path[-1]
            next_nodes = self._reverse[last_node]

            # Search goal node
            try:
                found = next_nodes.index(node2)
                current_path.append(next_nodes[found])
                resolved = '/'
                params = []
                for node in reversed(current_path[1:]):
                    resolved += node.route.path
                    params.extend(node.route.params.values())
                return resolved, params
            except ValueError:
                pass

            # Add new paths
            for next_node in next_nodes:
                if not next_node in previous_nodes:
                    new_path = current_path[:]
                    new_path.append(next_node)
                    path_list.append(new_path)
                    # To avoid backtracking
                    previous_nodes.add(next_node)
            # Continue to next path in list
            path_index += 1
        # No path is found
        return []
