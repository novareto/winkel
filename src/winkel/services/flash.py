import typing as t
from winkel.request import Request
from winkel.service import Service, factories
from http_session import Session


class Message(t.NamedTuple):
    body: str
    type: str = "info"

    def to_dict(self):
        return self._asdict()


class SessionMessages:

    def __init__(self, session: Session, key: str = "flashmessages"):
        self.key = key
        self.session = session

    def __iter__(self) -> t.Iterable[Message]:
        if self.key in self.session:
            while self.session[self.key]:
                yield Message(**self.session[self.key].pop(0))
                self.session.save()

    def add(self, body: str, type: str = "info"):
        if self.key in self.session:
            messages = self.session[self.key]
        else:
            messages = self.session[self.key] = []
        messages.append({"type": type, "body": body})
        self.session.save()


class Flash(Service):
    key: str = "flashmessages"
    __dependencies__ = [Session]

    @factories.scoped
    def messages_factory(self, request: Request) -> SessionMessages:
        session = request.get(Session)
        return SessionMessages(session, key=self.key)

