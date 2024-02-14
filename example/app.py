from typing import Any
from winkel.app import Application
from winkel.ui.rendering import ui_endpoint, template
from winkel.ui.layout import Layout
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.request import Request
from horseman.meta import APIView
from horseman.response import Response
from fanstatic import Fanstatic
from js.jquery import jquery


app = Application()
templates = Templates('./templates')
EXPRESSION_TYPES['slot'] = SlotExpr


app.ui.layouts.create(Layout(templates['layout']), (Request,), "")
app.ui.templates |= templates
app.ui.resources.add(jquery)


@app.router.register('/')
@ui_endpoint
@template(templates['views/index'])
def index(request):
    return {
        'message': 'Woop !'
    }


@app.router.register('/direct')
@ui_endpoint
def direct(request):
    return "<strong>I am bold</strong>"


@app.router.register('/naked')
@ui_endpoint(layout_name=None)
def naked(request):
    return "<em>I am naked</em>"


@app.ui.slots.register((Request, Any, Any), name='globalmenu')
class GlobalMenu:

    def namespace(self, request):
        return {'manager': self}

    @template(templates['slots/menu'])
    def render(self, request, view, context, slots):
        items = [
            slot(request, self, view, context) for slot in slots
        ]
        return {'items': items}


@app.ui.slots.register((Request, GlobalMenu, Any, Any), name='example')
def example_slot(request, manager, view, context):
    return "This is some slot"


@app.ui.slots.register((Request, GlobalMenu, Any, Any), name='titi')
def example_slot2(request, manager, view, context):
    return "This is some other slot"


wsgi_app = Fanstatic(app)
