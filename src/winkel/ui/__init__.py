import typing as t
from plum import Signature
from horseman.meta import Overhead
from chameleon.zpt import template
from winkel.items import ItemResolver
from winkel.templates import Templates
from winkel.components.actions import Actions


DEFAULT = ""
Default = t.Literal[DEFAULT]


class NamedComponent:

    store: ItemResolver

    def __init__(self, store: t.Optional[ItemResolver] = None):
        if store is None:
            store = ItemResolver()
        self.store = store

    def create(self,
               value: t.Any,
               discriminant: t.Iterable[t.Type],
               name: str | Default,
               **kwargs):
        signature = Signature(t.Literal[name], *discriminant)
        return self.store.create(value, signature, name=name, **kwargs)

    def get(self, *args, name=""):
        return self.store.lookup(name, *args)

    def register(self,
                 name: str | Default,
                 discriminant: t.Iterable[t.Type],
                 **kws):
        def register_component(func):
            self.create(func, discriminant, name=name, **kws)
            return func
        return register_component

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(self.store | other.store)


class UI:

    def __init__(self):
        self.slots = Actions()
        self.layouts = NamedComponent()
        self.templates = Templates()
        self.macros = Templates()
        self.resources = set()

    def render(self,
               *,
               content: str | template.PageTemplate,
               request: Overhead,
               layout: t.Optional[str | Default] = DEFAULT,
               **namespace):

        if self.resources:
            for resource in self.resources:
                resource.need()

        namespace.update({
            'request': request,
            'ui': self,
            'macro': self.macros.macro,
        })

        if isinstance(content, template.PageTemplate):
            content = content.render(**namespace)

        if layout is None:
            return content

        layout = self.layouts.get(request, name=layout).value
        return layout.render(content=content, **namespace)
