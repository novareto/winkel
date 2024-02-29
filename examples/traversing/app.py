from typing import Literal
from winkel.response import Response
from winkel import Application, TraversingApplication, Scope
from request import Request
from models import User, Folder, Document, Invoice
from winkel.router import Params


app = TraversingApplication()
app.use(Request())


@app.trail.register(Application, '/users/{id}')
def user_factory(parent: Application, scope: Scope, *, id: str) -> User:
    params = scope.get(Params)
    params['user_id'] = id
    return User(parent, id)


@app.trail.register(User, '/folders/{name}')
def folder_factory(parent: User, scope: Scope, *, name: str) -> Folder:
    params = scope.get(Params)
    params['folder_name'] = name
    return Folder(parent, name)


@app.trail.register(Folder, '/docs/{id}')
def folder_factory(parent: User, scope: Scope, *, id: str) -> Document:
    params = scope.get(Params)
    params['document_id'] = id
    return Document(parent, id)


@app.trail.register(Folder, '/invoices/{id}')
def invoice_factory(parent: User, scope: Scope, *, id: str) -> Invoice:
    params = scope.get(Params)
    params['invoice_id'] = id
    return Invoice(parent, id)


@app.views.register((Scope, User, Literal['GET']), name='')
def user_index(scope, user, method):
    params = scope.get(Params)
    return Response(200, body=f"I am a user : {params}")


@app.views.register((Scope, Folder, Literal['GET']), name='')
def folder_index(scope, folder, method):
    params = scope.get(Params)
    return Response(200, body=f"I am a folder : {params}")



wsgi_app = app
