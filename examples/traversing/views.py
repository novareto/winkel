import deform
from autorouting.url import RouteURL
from sqlmodel import Session as SQLSession, select
from winkel.traversing import Application
from winkel.traversing.traverser import Traversed
from winkel import Response, html, renderer
from winkel.traversing.traverser import ViewRegistry
from winkel.traversing.utils import path_for
from models import Company, Course, Session
from form import Form, trigger


routes = ViewRegistry()


@routes.register(Application, '/', name="view")
@html
@renderer(template='views/index')
def root_index(scope, application):
    sqlsession = scope.get(SQLSession)
    query = select(Company)
    companies = sqlsession.exec(query).all()
    return {
        'context': application,
        'companies': companies,
        'path_for': path_for(scope, application)
    }


@routes.register(Company, '/', name='view')
@html
@renderer(template='views/company')
def company_index(scope, company):
    return {
        'context': company,
        'path_for': path_for(scope, company)
    }


@routes.register(Course, '/', name="view")
@html
@renderer(template='views/course')
def course_index(scope, course):
    return {
        'context': course,
        'path_for': path_for(scope, course)
    }

@routes.register(Session, '/', name="view")
@html
@renderer(template='views/session')
def session_index(scope, session):
    return {'context': session}


@routes.register(Application, '/create_company', name='create_company')
class CreateCompany(Form):

    model = Company

    def get_schema(self, scope, context):
        return self.model.get_schema(exclude=("id",))

    @trigger('save', 'Create new company')
    def save(self, scope, data, context):
        form = self.get_form(scope, context)
        appstruct = form.validate(data)
        sqlsession = scope.get(SQLSession)
        sqlsession.add(
            Company(
                **appstruct
            )
        )
        return Response.redirect(scope.environ.application_uri)


@routes.register(Company, '/create_course', name='create_course')
class CreateCourse(Form):

    model = Course

    def get_schema(self, scope, context):
        return self.model.get_schema(exclude=("id", "company_id"))

    @trigger('save', 'Create new course')
    def save(self, scope, data, context):
        form = self.get_form(scope, context)
        appstruct = form.validate(data)
        sqlsession = scope.get(SQLSession)
        sqlsession.add(
            Course(
                **appstruct,
                company_id=context.id
            )
        )
        return Response.redirect(context.__path__)


@routes.register(Course, '/create_session', name='create_session')
class CreateSession(Form):

    model = Session

    def get_schema(self, scope, context):
        return self.model.get_schema(exclude=("id", "course_id"))

    @trigger('save', 'Create new session')
    def save(self, scope, data, context):
        form = self.get_form(scope, context)
        appstruct = form.validate(data)
        sqlsession = scope.get(SQLSession)
        sqlsession.add(
            Session(
                **appstruct,
                course_id=context.id
            )
        )
        return Response.redirect(context.__path__)
