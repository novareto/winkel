from typing import Any
from winkel.ui import SlotRegistry, LayoutRegistry, SubSlotRegistry
from winkel.rendering import renderer
from winkel.scope import Scope
from winkel.auth import User, anonymous
from winkel.services.flash import SessionMessages
from actions import Actions
from login import Login
from winkel.utils import ondemand


slots = SlotRegistry()
layouts = LayoutRegistry()
subslots = SubSlotRegistry()


@layouts.register(..., name="")
@renderer(template='layout', layout_name=None)
def default_layout(scope: Scope, view: Any, context: Any, name: str, content: str):
    return {'content': content, 'view': view, 'context': context}


@slots.register(..., name='actions')
@renderer(template='slots/actions', layout_name=None)
def actions(scope: Scope, view: Any, context: Any, *, items):
    registry = scope.get(Actions)
    matching = registry.match_grouped(scope, view, context)
    evaluated = []
    for name, action in matching.items():
        if not action.__evaluate__(scope, view, context):
            result = action(scope, view, context)
            evaluated.append((action.__metadata__, result))
    return {
        "actions": evaluated,
        'view': view,
        'context': context,
        'manager': actions
    }


@slots.register(..., name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(self, scope: Scope, view: Any, context: Any, *, items):
        return {
            'items': [item(scope, self, view, context) for item in items],
            'view': view, 'context': context, 'manager': self
        }


@subslots.register({"manager": AboveContent}, name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(scope: Scope, manager: AboveContent, view: Any, context: Any):
    flash = scope.get(SessionMessages)
    return {'messages': list(flash), 'view': view, 'context': context, 'manager': manager}


@subslots.register({"manager": AboveContent}, name='identity')
@ondemand
def identity(who_am_i: User):
    if who_am_i is anonymous:
        return "<div class='container alert alert-secondary'>Not logged in.</div>"
    return f"<div class='container alert alert-info'>You are logged in as {who_am_i.id}</div>"


@slots.register({"view": Login}, name='sneaky')
def sneaky(scope: Scope, view: Login, context: Any, *, items) -> str:
    return "I show up only on the Login page."
