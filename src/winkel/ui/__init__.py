from typing import Literal, Set
from plum import Signature
from fanstatic import Group, Resource
from horseman.meta import Overhead
from chameleon.zpt import template
from winkel.items import ItemResolver
from winkel.templates import Templates
from winkel.components.named import Components, NamedComponents


class UI:

    __slots__ = ('slots', 'layouts', 'templates', 'macros', 'resources')

    def __init__(self):
        self.slots = Components(default_name="")
        self.layouts = NamedComponents()
        self.templates = Templates()
        self.macros = Templates()
        self.resources: Set[Group | Resource] = set()

    def inject_resources(self):
        if self.resources:
            for resource in self.resources:
                resource.need()
