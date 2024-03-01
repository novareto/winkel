import deform
from functools import partial
from sqlmodel import Session, select
from horseman.exceptions import HTTPError
from winkel.traversing import Application
from winkel import FormData, Response
from winkel.routing import Params, APIView
from winkel import html, renderer
from winkel.traversing.views import ViewRegistry
from models import Company, Course
from form import Form, trigger
from factories import Traversed


routes = ViewRegistry()


def form(schema, scope):
    schema = schema.bind(scope=scope)
    process_btn = deform.form.Button(name='process', title="Process")
    return deform.form.Form(schema, buttons=(process_btn,))


def url_for(scope, context):
    def resolve_url(target, name, **params):
        root = scope.get(Application)
        stub = root.views.route_for(target, name, **params)
        if target is context:
            if type(context) is Traversed:
                return context.__path__ + stub
            return stub
        else:
            trail = root.trail.reverse(target.__class__, context.__class__)
            path = trail.format(**params)
            return path + stub
    return resolve_url


@routes.register(Application, '/', name="view")
@html
@renderer(template='views/index')
def root_index(scope, application):
    sqlsession = scope.get(Session)
    query = select(Company)
    companies = sqlsession.exec(query).all()
    return {
        'context': application,
        'companies': companies,
        'url_for': url_for(scope, application)
    }


@routes.register(Company, '/', name='view')
@html
@renderer(template='views/company')
def company_index(scope, company):
    params = scope.get(Params)
    views = scope.get(ViewRegistry)
    return {
        'context': company,
        'url_for': url_for(scope, company)
    }


@routes.register(Course, '/', name="view")
@html
@renderer(template='views/course')
def course_index(scope, course):
    params = scope.get(Params)
    return {'context': course}



@routes.register(Application, '/create_company', name='create_company')
class CreateCompany(Form):

    model = Company

    def get_schema(self, scope, context):
        return self.model.get_schema(exclude=("id",))

    @trigger('save', 'Create new company')
    def save(self, scope, data, context):
        try:
            form = self.get_form(scope, app)
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


@routes.register(Company, '/create_course', name='create_course')
class CreateCourse(APIView):

    def get_schema(self, scope, context):
        return Course.get_schema(exclude=("id", "company_id"))

    @trigger('save', 'Create new company')
    def save(self, scope, data, context):
        try:
            form = self.get_form(scope, app)
            appstruct = form.validate(data.form)
        except deform.exception.ValidationFailure as e:
            return {
                "rendered_form": e.render()
            }
        sqlsession = scope.get(Session)
        sqlsession.add(
            Course(
                **appstruct,
                company_id=company.id
            )
        )
        return Response.redirect(scope.environ.application_uri)
