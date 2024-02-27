from typing import Any, List
from elementalist.registries import SignatureMapping
from winkel.ui.rendering import renderer
from winkel.request import Scope
from winkel.auth import User, anonymous
from winkel.services.flash import SessionMessages
from actions import Actions


slots = SignatureMapping()
layouts = SignatureMapping()


@layouts.register((Scope, Any, Any), name="")
@renderer(template='layout', layout_name=None)
def default_layout(scope: Scope, view: Any, context: Any, **namespace):
    return namespace


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
        "actions": evaluated
    }


@slots.register((Scope, Any, Any), name='above_content')
class AboveContent:

    def namespace(self, scope):
        return {'manager': self}

    @renderer(template='slots/above', layout_name=None)
    def __call__(self, scope: Scope, view: Any, context: Any, *, slots):
        items = []
        for slot in slots:
            result = slot.conditional_call(scope, self, view, context)
            if result is not None:
                items.append(result)
        return {'items': items}


@slots.register((Scope, AboveContent, Any, Any), name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(scope: Scope, manager: AboveContent, view: Any, context: Any):
    flash = scope.get(SessionMessages)
    return {'messages': list(flash)}


@slots.register((Scope, AboveContent, Any, Any), name='identity')
def identity(scope: Scope, manager: AboveContent, view: Any, context: Any):
    who_am_i = scope.get(User)
    if who_am_i is anonymous:
        return "<div class='container alert alert-secondary'>Not logged in. Please consider creating an account or logging in.</div>"
    return f"<div class='container alert alert-info'>You are logged in as {who_am_i.id}</div>"
