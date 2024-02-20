import ast
from typing import Callable, Any
from inspect import isclass
from chameleon.codegen import template
from chameleon.astutil import Symbol
from winkel.request import Environ


Slot = Callable[[Environ, str, Any], str]


def query_slot(econtext, name):
    """Compute the result of a slot expression
    """
    ui = econtext.get('ui', None)
    if ui is None:
        return None
    request = econtext.get('request')
    view = econtext.get('view', object())
    context = econtext.get('context', object())
    try:
        manager = ui.slots.get(request, view, context, name=name)
        if isclass(manager.value):
            manager = manager()
        slots = ui.slots.match_all(request, manager, view, context)
        return manager(request, view, context, slots.values())

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
