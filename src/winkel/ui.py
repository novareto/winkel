import ast
import typing
from inspect import isclass
from dataclasses import dataclass, field
from typing import Set, Any, NamedTuple, Type
from fanstatic import Group, Resource
from chameleon.codegen import template
from chameleon.astutil import Symbol
from winkel.registry import ComponentRegistry
from winkel.scope import Scope
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.service import Installable
from beartype import beartype


class SlotRegistry(ComponentRegistry):

    @beartype
    class Types(NamedTuple):
        scope: Type[Scope] = Scope
        view: Type = Any
        context: Type = Any


class SubSlotRegistry(ComponentRegistry):

    @beartype
    class Types(NamedTuple):
        scope: Type[Scope] = Scope
        manager: Type = Any
        view: Type = Any
        context: Type = Any


class LayoutRegistry(ComponentRegistry):

    @beartype
    class Types(NamedTuple):
        scope: Type[Scope] = Scope
        view: Type = Any
        context: Type = Any


def query_slot(econtext, name):
    """Compute the result of a slot expression
    """
    scope = econtext.get('scope')  # mandatory.
    context = econtext.get('context', object())
    view = econtext.get('view', object())
    ui = econtext.get('ui', scope.get(UI))

    try:
        manager = ui.slots.lookup(scope, view, context, name=name)
        if manager.evaluate(view, context, scope=scope):
            return None

        if isclass(manager.value):
            manager = manager.value()
        else:
            manager = manager.value

        slots = ui.subslots.match_grouped(scope, manager, view, context)
        return manager(
            scope, view, context, slots=slots.values()
        )

    except LookupError:
        # No slot found. We don't render anything.
        return None


class SlotExpr:
    """
    This is the interpreter of a slot: expression
    """
    def __init__(self, expression):
        self.expression = expression

    def __call__(self, target, engine):
        slot_name = self.expression.strip()
        value = template(
            "query_slot(econtext, name)",
            query_slot=Symbol(query_slot),  # ast of query_slot
            name=ast.Str(s=slot_name),  # our name parameter to query_slot
            mode="eval"
        )
        return [ast.Assign(targets=[target], value=value)]


@dataclass(kw_only=True, slots=True)
class UI(Installable):

    __provides__ = ['UI']

    slots: ComponentRegistry = field(default_factory=SlotRegistry)
    subslots: ComponentRegistry = field(default_factory=SubSlotRegistry)
    layouts: ComponentRegistry = field(default_factory=LayoutRegistry)
    templates: Templates = field(default_factory=Templates)
    macros: Templates = field(default_factory=Templates)
    resources: Set[Group | Resource] = field(default_factory=set)

    def inject_resources(self):
        if self.resources:
            for resource in self.resources:
                resource.need()

    def install(self, services):
        services.register(UI, instance=self)
        if 'slot' not in EXPRESSION_TYPES:
            EXPRESSION_TYPES['slot'] = SlotExpr

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
