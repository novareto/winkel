from typing import Any
from winkel.app import Application
from winkel.ui.rendering import ui_endpoint, template
from winkel.ui.layout import Layout
from winkel.ui.slot import SlotExpr
from winkel.templates import Templates, EXPRESSION_TYPES
from winkel.request import Request
from horseman.response import Response
from fanstatic import Fanstatic
from js.jquery import jquery
from winkel.pipes import Transactional, HTTPSession
from http_session.session import Session
from transaction import TransactionManager
import http_session_file
import pathlib


app = Application()
templates = Templates('./templates')
EXPRESSION_TYPES['slot'] = SlotExpr


app.ui.layouts.create(Layout(templates['layout']), (Request,), "")
app.ui.templates |= templates
app.ui.resources.add(jquery)

Transactional().install(app, 10)
HTTPSession(
    store=http_session_file.FileStore(
        pathlib.Path('./sessions'), 300),
    secret="secret",
    salt="salt",
    cookie_name="cookie_name",
    secure=False,
    TTL=300
).install(app, 20)


@app.router.register('/')
@ui_endpoint
@template(templates['views/index'])
def index(request):
    return {
        'message': 'Woop !'
    }


@app.router.register('/person/{uid}')
@ui_endpoint
def person(request):
    params = request.get('params')
    data = request.get('data')
    transaction = request.get(TransactionManager)
    session = request.get(Session)
    session['test'] = session.get('test', 0) + 1
    return str(params) + str(data) + str(transaction) + str(session)



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
