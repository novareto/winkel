import abc
import uuid
import typing as t
from winkel.scope import Scope


UserID = str | int | uuid.UUID


class User(abc.ABC):
    id: UserID


class AnonymousUser(User):
    id: int = -1


anonymous = AnonymousUser()


class Source(abc.ABC):

    @abc.abstractmethod
    def find(self,
             credentials: t.Any, scope: Scope) -> User | None:
        pass

    @abc.abstractmethod
    def fetch(self, uid: UserID, scope: Scope) -> User | None:
        pass


class DictSource(Source):

    def __init__(self, users: dict[str, str]):
        self.users = users

    def find(self, credentials: dict, scope: Scope) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        if username is not None and username in self.users:
            if self.users[username] == password:
                user = User()
                user.id = username
                return user

    def fetch(self, uid: UserID, scope: Scope) -> User | None:
        if uid in self.users:
            user = User()
            user.id = uid
            return user


class Authenticator(abc.ABC):
    @abc.abstractmethod
    def from_credentials(self, scope: Scope, credentials: dict) -> User | None:
        ...

    @abc.abstractmethod
    def identify(self, scope: Scope) -> User:
        ...

    @abc.abstractmethod
    def forget(self, scope: Scope) -> None:
        ...

    @abc.abstractmethod
    def remember(self, scope: Scope, user: User) -> None:
        ...
