from winkel import Application, TraversingApplication, Scope
from request import Request
from models import User, Folder, Document, Invoice


app = TraversingApplication()
app.use(Request())


@app.trail.register(Application, '/users/{id}')
def user_factory(parent: Application, scope: Scope, *, id: str) -> User:
    return User(parent, id)


@app.trail.register(User, '/folders/{name}')
def folder_factory(parent: User, scope: Scope, *, name: str) -> Folder:
    return Folder(parent, name)


@app.trail.register(Folder, '/docs/{id}')
def folder_factory(parent: User, scope: Scope, *, id: str) -> Document:
    return Document(parent, id)


@app.trail.register(Folder, '/invoices/{id}')
def folder_factory(parent: User, scope: Scope, *, id: str) -> Invoice:
    return Invoice(parent, id)


import pdb
pdb.set_trace()