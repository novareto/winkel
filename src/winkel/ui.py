import ast
from dataclasses import dataclass, field
from typing import Set, Any, NamedTuple
from fanstatic import Group, Resource
from chameleon.codegen import template
from chameleon.astutil import Symbol
from winkel.registries import TypedRegistry, Registry
from winkel.scope import Scope
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.service import Installable
from beartype import beartype


class SlotRegistry(TypedRegistry):

    @beartype
    class Types(NamedTuple):
        scope: type[Scope] = Scope
        view: type = Any
        context: type = Any


class SubSlotRegistry(TypedRegistry):

    @beartype
    class Types(NamedTuple):
        scope: type[Scope] = Scope
        manager: type = Any
        view: type = Any
        context: type = Any


class LayoutRegistry(TypedRegistry):

    @beartype
    class Types(NamedTuple):
        scope: type[Scope] = Scope
        view: type = Any
        context: type = Any


def query_slot(econtext, name):
    """Compute the result of a slot expression
    """
    scope = econtext.get('scope')  # mandatory.
    context = econtext.get('context', object())
    view = econtext.get('view', object())
    ui = econtext.get('ui', scope.get(UI))

    try:
        manager = ui.slots.fetch(scope, view, context, name=name)
        if manager.__evaluate__(scope, view, context):
            return None

        if manager.__metadata__.isclass:
            manager = manager()

        subslots = [
            subslot for subslot in
            ui.subslots.match_grouped(scope, manager, view, context).values()
            if not subslot.__evaluate__(scope, manager, view, context)
        ]
        return manager(scope, view, context, items=subslots)

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

    slots: Registry = field(default_factory=SlotRegistry)
    subslots: Registry = field(default_factory=SubSlotRegistry)
    layouts: Registry = field(default_factory=LayoutRegistry)
    templates: Templates = field(default_factory=Templates)
    macros: Templates = field(default_factory=Templates)

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
