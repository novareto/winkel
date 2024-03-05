from typing import Any
from winkel.ui import SlotRegistry, LayoutRegistry, SubSlotRegistry
from winkel.rendering import renderer
from winkel.scope import Scope
from winkel.auth import User, anonymous
from winkel.services.flash import SessionMessages
from winkel.utils import ondemand


slots = SlotRegistry()
layouts = LayoutRegistry()
subslots = SubSlotRegistry()


@layouts.register(..., name="")
@renderer(template='layout', layout_name=None)
def default_layout(scope: Scope, view: Any, context: Any, name: str, content: str):
    return {'content': content, 'view': view, 'context': context}


@slots.register(..., name='above_content')
class AboveContent:

    @renderer(template='slots/above', layout_name=None)
    def __call__(self, scope: Scope, view: Any, context: Any, *, items):
        return {
            'items': [item(scope, self, view, context) for item in items]
        }


@subslots.register({"manager": AboveContent}, name='messages')
@renderer(template='slots/messages', layout_name=None)
def messages(scope: Scope, manager: AboveContent, view: Any, context: Any):
    flash = scope.get(SessionMessages)
    return {
        'messages': list(flash)
    }
