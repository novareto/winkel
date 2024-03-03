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

    def finalize(self):
        for router in self.values():
            router.finalize()

    def register(self, context: Type, *args, **kwargs):
        router = self.setdefault(context, Router())
        return router.register(*args, **kwargs)

    def route_for(self, context: Any, name: str, **params):
        for router in self.lookup(context.__class__):
            if name in router.name_index:
                return str(router.url_for(name, **params))
        raise LookupError(f'Could not find route {name!r} for {context!r}')

    def match(self, context: Any, path: str, method: str):
        for routes in self.lookup(context.__class__):
            matched: MatchedRoute | None = routes.get(path, method)
            if matched is not None:
                return matched

    def __or__(self, other: 'ViewRegistry'):
        new = ViewRegistry()
        for cls, router in self.items():
            new[cls] = router
        for cls, router in other.items():
            if cls in new:
                new[cls] |= router
            else:
                new[cls] = router
        return new

    def __ior__(self, other: 'ViewRegistry'):
        for cls, router in other.items():
            if cls in self:
                self[cls] |= router
            else:
                self[cls] = router
        return self
