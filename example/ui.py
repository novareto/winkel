from typing import Any
from elementalist.registries import SignatureMapping
from winkel.ui.rendering import template
from winkel.request import Request
from winkel.auth import User, anonymous
from winkel.services.flash import SessionMessages
from actions import Actions


slots = SignatureMapping()
layouts = SignatureMapping()

@layouts.register((Request,), name="")
@template('layout')
def default_layout(request, **namespace):
    return namespace


@slots.register((Request, Any, Any), name='actions')
@template('slots/actions')
def actions(request, view, context, slots):
    registry = request.get(Actions)
    matching = registry.match_grouped(request, view, context)
    evaluated = []
    for name, action in matching.items():
        result = action.conditional_call(request, view, context)
        if result is not None:
            evaluated.append((action, result))
    return {
        "actions": evaluated
    }


@slots.register((Request, Any, Any), name='above_content')
class AboveContent:

    def namespace(self, request):
        return {'manager': self}

    @template('slots/above')
    def __call__(self, request, view, context, slots):
        items = []
        for slot in slots:
            result = slot.conditional_call(request, self, view, context)
            if result is not None:
                items.append(result)
        return {'items': items}


@slots.register((Request, AboveContent, Any, Any), name='messages')
@template('slots/messages')
def messages(request, manager, view, context):
    flash = request.get(SessionMessages)
    return {'messages': list(flash)}


@slots.register((Request, AboveContent, Any, Any), name='identity')
def identity(request, manager, view, context):
    who_am_i = request.get(User)
    if who_am_i is anonymous:
        return "<div class='container alert alert-secondary'>Not logged in. Please consider creating an account or logging in.</div>"
    return f"<div class='container alert alert-info'>You are logged in as {who_am_i.id}</div>"
