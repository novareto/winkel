from winkel.components import Subscribers
from winkel.request import Request
from winkel.app import Application

class Context:
    pass


class SubContext(Context):
    pass


class SpecializedRequest(Request):
    pass


app = Application()
subs1 = Subscribers()
subs2 = Subscribers()


@subs1.register((Context, Request))
def context_event(context, request):
    print('I was matched')


@subs1.register((SubContext, Request))
def context_event2(context, request):
    print('I was matched too')


@subs2.register((Context, Request), order=1)
def context_event3(context, request):
    print('I was matched first')


@subs2.register((Context, SpecializedRequest), order=2)
def context_event3(context, request):
    print('I was matched second')


subs1.notify(SubContext(), SpecializedRequest(app, environ={}))

print('---')
subs1.notify(Context(), Request(app, environ={}))

print('---')
subs = subs1 | subs2
subs.notify(Context(), Request(app, environ={}))
print('---')
subs.notify(SubContext(), SpecializedRequest(app, environ={}))
