from typing import Any
from elementalist.registries import SignatureMapping
from prejudice.errors import ConstraintError
from winkel.request import Request
from winkel.auth import User, anonymous


class Actions(SignatureMapping):
    ...


actions = Actions()


def is_not_anonymous(action, request, view, context):
    if request.get(User) is anonymous:
        raise ConstraintError('User is anonymous.')


def is_anonymous(action, request, view, context):
    if request.get('user') is not anonymous:
        raise ConstraintError('User is not anonymous.')


@actions.register((Request, Any, Any), name='login', title='Login', description='Login action', conditions=(is_anonymous,))
def login_action(request, view, item):
    return '/login'


@actions.register((Request, Any, Any), name='logout', title='Logout', description='Logout action', conditions=(is_not_anonymous,))
def logout_action(request, view, item):
    return '/logout'
