from dataclasses import dataclass, field
from typing import Literal, Set
from plum import Signature
from fanstatic import Group, Resource
from chameleon.zpt import template
from winkel.items import ItemResolver
from winkel.templates import Templates
from winkel.components.named import Components, NamedComponents


@dataclass(kw_only=True, slots=True)
class UI:

    slots: Components = field(default_factory=Components)
    layouts: NamedComponents = field(default_factory=NamedComponents)
    templates: Templates = field(default_factory=Templates)
    macros: Templates = field(default_factory=Templates)
    resources: Set[Group | Resource] = field(default_factory=set)

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
