from typing import Any
from elementalist.registries import SignatureMapping
from winkel.ui.rendering import renderer
from winkel.traversing.traverser import Traversed
from winkel.scope import Scope
from winkel.services.flash import SessionMessages
from collections import deque


slots = SignatureMapping()
layouts = SignatureMapping()


@layouts.register((Scope, Any, Any), name="")
@renderer(template='layout', layout_name=None)
def default_layout(scope: Scope, view: Any, context: Any, name: str, content: str):
    return {
        'content': content,
        'view': view,
        'context': context
    }


@slots.register((Scope, Any, Any), name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(self, scope: Scope, view: Any, context: Any, *, slots):
        items = []
        for slot in slots:
            result = slot.conditional_call(scope, self, view, context)
            if result is not None:
                items.append(result)
        return {
            'items': items,
            'view': view,
            'context': context,
            'manager': self
        }


@slots.register((Scope, AboveContent, Any, Any), name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(scope: Scope, manager: AboveContent, view: Any, context: Any):
    flash = scope.get(SessionMessages)
    return {
        'messages': list(flash),
        'view': view,
        'context': context,
        'manager': manager
    }

@slots.register((Scope, AboveContent, Any, Any), name='crumbs')
@renderer(template='slots/breadcrumbs', layout_name=None)
def breadcumbs(scope: Scope, manager: AboveContent, view: Any, context: Any):
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
