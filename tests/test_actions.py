from winkel.app import Application
from winkel.components import Actions
from winkel.request import Request


class Context:
    pass


class SubContext(Context):
    pass


class SpecializedRequest(Request):
    pass


actions1 = Actions()
actions2 = Actions()

actions1.create(3, (SubContext, SpecializedRequest), name="action")
actions1.create(1, (Context, Request), name="action")
actions2.create(4, (Context, SpecializedRequest), name="action")
actions2.create(2, (SubContext, Request), name="actions2")


app = Application(actions=actions1|actions2)
print(
    app.actions.match_all(
        SubContext(), SpecializedRequest(app, environ={}))
)
print(
    app.actions.get(
        Context(), SpecializedRequest(app, environ={}), name="action")
)


