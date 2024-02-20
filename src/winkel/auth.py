import abc
import typing as t
from http_session.session import Session
from .markers import Marker
from .request import Request


class User(abc.ABC):
    id: t.Union[str, int]


class AnonymousUser(User):
    id: int = -1


anonymous = AnonymousUser()


class Source(abc.ABC):

    @abc.abstractmethod
    def find(self,
             credentials: t.Dict, request: Request) -> t.Optional[User]:
        pass

    @abc.abstractmethod
    def fetch(self, uid: t.Any, request: Request) -> t.Optional[User]:
        pass


class DictSource(Source):

    def __init__(self, users: t.Mapping[str, str]):
        self.users = users

    def find(self, credentials: t.Dict, request: Request) -> t.Optional[User]:
        username = credentials.get('username')
        password = credentials.get('password')
        if username is not None and username in self.users:
            if self.users[username] == password:
                user = User()
                user.id = username
                return user

    def fetch(self, uid, request) -> t.Optional[User]:
        if uid in self.users:
            user = User()
            user.id = uid
            return user


class Authenticator:

    user_key: str
    sources: t.Iterable[Source]

    def __init__(self, user_key: str, sources: t.Iterable[Source]):
        self.sources = sources
        self.user_key = user_key

    def from_credentials(self,
                         request, credentials: dict) -> User | None:
        for source in self.sources:
            user = source.find(credentials, request)
            if user is not None:
                return user

    def identify(self, request) -> User:
        if (session := request.get(Session)) is not Marker.missing:
            if (userid := session.get(self.user_key, None)) is not None:
                for source in self.sources:
                    user = source.fetch(userid, request)
                    if user is not None:
                        return user
        return anonymous

    def forget(self, request) -> t.NoReturn:
        if (session := request.get(Session)) is not Marker.missing:
            session.clear()

    def remember(self, request, user: User) -> t.NoReturn:
        if (session := request.get(Session)) is not Marker.missing:
            session[self.user_key] = user.id
