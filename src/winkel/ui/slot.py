import ast
from typing import Callable, Any
from inspect import isclass
from chameleon.codegen import template
from chameleon.astutil import Symbol
from winkel.request import Scope
from winkel.ui import UI
from winkel.components import MatchedRoute


Slot = Callable[[Scope, str, Any], str]


def query_slot(econtext, name):
    """Compute the result of a slot expression
    """
    scope = econtext.get('scope')  # mandatory.
    context = econtext.get('context', object())
    view = econtext.get('view', scope.get(MatchedRoute).route.value)
    ui = econtext.get('ui', scope.get(UI))
    try:
        manager = ui.slots.lookup(scope, view, context, name=name)
        if manager.evaluate(view, context, scope=scope):
            return None

        if isclass(manager.value):
            manager = manager.value()
        else:
            manager = manager.value

        slots = ui.slots.match_grouped(scope, manager, view, context)
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
