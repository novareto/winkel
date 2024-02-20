import typing as t
from http_session.session import Session
from winkel.request import Request


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


def flash_service(request: Request) -> SessionMessages:
    session = request.get(Session)
    return SessionMessages(session)
