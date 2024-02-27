from typing import Any
from elementalist.registries import SignatureMapping
from prejudice.errors import ConstraintError
from winkel.request import Scope
from winkel.auth import User, anonymous


class Actions(SignatureMapping):
    ...


actions = Actions()


def is_not_anonymous(action, scope, view, context):
    if scope.get(User) is anonymous:
        raise ConstraintError('User is anonymous.')


def is_anonymous(action, scope, view, context):
    if scope.get('user') is not anonymous:
        raise ConstraintError('User is not anonymous.')


@actions.register((Scope, Any, Any), name='login', title='Login', description='Login action', conditions=(is_anonymous,))
def login_action(scope, view, item):
    return '/login'


@actions.register((Scope, Any, Any), name='logout', title='Logout', description='Logout action', conditions=(is_not_anonymous,))
def logout_action(scope, view, item):
    return '/logout'
