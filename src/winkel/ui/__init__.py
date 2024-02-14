from typing import Literal
from plum import Signature
from horseman.meta import Overhead
from chameleon.zpt import template
from winkel.items import ItemResolver
from winkel.templates import Templates
from winkel.components.named import Components, NamedComponents


class UI:

    def __init__(self):
        self.slots = Components(default_name="")
        self.layouts = NamedComponents()
        self.templates = Templates()
        self.macros = Templates()
        self.resources = set()
