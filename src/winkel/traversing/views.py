from typing import Type, Iterator, Any
from winkel.routing.router import Router, MatchedRoute


class ViewRegistry(dict):

    @staticmethod
    def lineage(cls: Type):
        yield from cls.__mro__

    def lookup(self, cls: Type) -> Iterator[Router]:
        for parent in self.lineage(cls):
            if parent in self:
                yield self[parent]

    def register(self, root: Type, *args, **kwargs):
        router = self.setdefault(root, Router())
        return router.register(*args, **kwargs)

    def match(self, root: Any, path: str, method: str):
        for routes in self.lookup(root.__class__):
            matched: MatchedRoute | None = routes.match(path, method)
            if matched is not None:
                return matched
