import wrapt
import deform
from typing import Any
import jsonschema_colander.types
from winkel import Application, TraversingApplication, Scope, sqldb
from request import Request
from models import Company
from winkel.router import Params
from sqlmodel import Session
from winkel import Response, FormData, html, renderer
from winkel.ui import UI, Templates
from winkel.router import APIView


company_schema = jsonschema_colander.types.Object.from_json(
    Company.model_json_schema(), config={
        "": {
            "exclude": ("id",)
        },
    }
)

def company_creation_form(scope):
    schema = company_schema().bind(scope=scope)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


class Traversed(wrapt.ObjectProxy):
    __parent__: Any
    __trail__: str

    def __init__(self, wrapped, *, parent: Any, path: str):
        super().__init__(wrapped)
        self.__parent__ = parent
        self.__trail__ = path


app = TraversingApplication()
app.use(
    Request(),
    sqldb.SQLDatabase(
        url="sqlite:///traversing.db"
    ),
    UI(
        templates=Templates('templates'),
    ),
)


@app.trail.register(Application, '/company/{company_id}')
def company_factory(path: str, parent: Application, scope: Scope, *, company_id: str) -> Company:
    sqlsession = scope.get(Session)
    params = scope.get(Params)
    params['company_id'] = company_id
    company = sqlsession.get(Company, company_id)
    return Traversed(company, parent=parent, path=path)


@app.views.register(Company, '/{whatever}')
@html
def company_index(scope, company):
    params = scope.get(Params)
    return f"Company: {company.name} from {params}"

@app.views.register(Application, '/new_company')
class CreateCompany(APIView):

    @html
    @renderer(template='form/default', layout_name=None)
    def GET(self, scope, app):
        form = company_creation_form(scope)
        return {
            "rendered_form": form.render()
        }

    @html
    @renderer(template='form/default', layout_name=None)
    def POST(self, scope, app):
        data = scope.get(FormData)
        if ('process', 'process') not in data.form:
            raise NotImplementedError('No action found.')

        try:
            form = company_creation_form(scope)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }

        sqlsession = scope.get(Session)
        sqlsession.add(
            Company(
                **appstruct
            )
        )
        return Response.redirect(scope.environ.application_uri)


wsgi_app = app
