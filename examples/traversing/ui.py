from typing import Any
from winkel.rendering import renderer
from winkel.traversing.traverser import Traversed
from winkel.scope import Scope
from winkel.ui import SlotRegistry, LayoutRegistry, SubSlotRegistry
from winkel.services.flash import SessionMessages
from collections import deque


slots = SlotRegistry()
layouts = LayoutRegistry()
subslots = SubSlotRegistry()


@layouts.register(..., name="")
@renderer(template='layout', layout_name=None)
def default_layout(scope: Scope, view: Any, context: Any, name: str, content: str):
    return {
        'content': content,
        'view': view,
        'context': context
    }


@slots.register(..., name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(self, scope: Scope, view: Any, context: Any, *, items):
        return {
            'items': [item(scope, self, view, context) for item in items],
            'view': view,
            'context': context,
            'manager': self
        }


@subslots.register({'manager': AboveContent}, name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(scope: Scope, manager: AboveContent, view: Any, context: Any):
    flash = scope.get(SessionMessages)
    return {
        'messages': list(flash),
        'view': view,
        'context': context,
        'manager': manager
    }


@subslots.register({'manager': AboveContent}, name='crumbs')
@renderer(template='slots/breadcrumbs', layout_name=None)
def breadcrumbs(scope: Scope, manager: AboveContent, view: Any, context: Any):
    node = context
    parents = deque()
    while node is not None:
        if type(node) is Traversed:
            parents.appendleft((node.__path__, node))
            node = node.__parent__
        else:
            node = None

    return {
        'crumbs': parents,
        'view': view,
        'context': context,
        'manager': manager
    }
