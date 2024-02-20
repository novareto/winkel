from dataclasses import dataclass, field
from typing import Literal, Set, Any
from fanstatic import Group, Resource
from chameleon.zpt import template
from plum import Signature
from functools import partial
from winkel.templates import Templates
from winkel.request import Request
from elementalist.registries import (
    Registry, NamedElementRegistry, SpecificElementRegistry
)


View = Any
Context = Any
Manager = Any

SlotSignatures = {
    Signature(Request, View, Context, Literal),
    Signature(Request, Manager, View, Context, Literal)
}

LayoutSignatures = {
    Signature(str, Request),
}


@dataclass(kw_only=True, slots=True)
class UI:

    slots: Registry = field(default_factory=NamedElementRegistry)
    layouts: Registry = field(default_factory=SpecificElementRegistry)
    templates: Templates = field(default_factory=Templates)
    macros: Templates = field(default_factory=Templates)
    resources: Set[Group | Resource] = field(default_factory=set)

    def __post_init__(self):
        self.slots.restrict |= set(SlotSignatures)
        self.layouts.restrict |= set(LayoutSignatures)

    def inject_resources(self):
        if self.resources:
            for resource in self.resources:
                resource.need()

    def __or__(self, other: 'UI'):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(
            slots=self.slots | other.slots,
            layouts=self.layouts | other.layouts,
            templates=self.templates | other.templates,
            macros=self.macros | other.macros,
            resources=self.resources | other.resources
        )
