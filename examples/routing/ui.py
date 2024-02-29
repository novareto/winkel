from typing import Any
from elementalist.registries import SignatureMapping
from winkel.ui.rendering import renderer
from winkel.scope import Scope
from winkel.auth import User, anonymous
from winkel.services.flash import SessionMessages
from actions import Actions
from login import Login


slots = SignatureMapping()
layouts = SignatureMapping()


@layouts.register((Scope, Any, Any), name="")
@renderer(template='layout', layout_name=None)
def default_layout(scope: Scope, view: Any, context: Any, name: str, content: str):
    return {'content': content, 'view': view, 'context': context}


@slots.register((Scope, Any, Any), name='actions')
@renderer(template='slots/actions', layout_name=None)
def actions(scope: Scope, view: Any, context: Any, *, slots):
    registry = scope.get(Actions)
    matching = registry.match_grouped(scope, view, context)
    evaluated = []
    for name, action in matching.items():
        result = action.conditional_call(scope, view, context)
        if result is not None:
            evaluated.append((action, result))
    return {
        "actions": evaluated,
        'view': view,
        'context': context,
        'manager': actions
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
        return {'items': items, 'view': view, 'context': context, 'manager': self}


@slots.register((Scope, AboveContent, Any, Any), name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(scope: Scope, manager: AboveContent, view: Any, context: Any):
    flash = scope.get(SessionMessages)
    return {'messages': list(flash), 'view': view, 'context': context, 'manager': manager}


@slots.register((Scope, AboveContent, Any, Any), name='identity')
def identity(scope: Scope, manager: AboveContent, view: Any, context: Any):
    who_am_i = scope.get(User)
    if who_am_i is anonymous:
        return "<div class='container alert alert-secondary'>Not logged in.</div>"
    return f"<div class='container alert alert-info'>You are logged in as {who_am_i.id}</div>"


@slots.register((Scope, Login, Any), name='subslot')
def sub_slot(scope: Scope, view: Login, context: Any, *, slots):
    return "I show up only on the Login page."