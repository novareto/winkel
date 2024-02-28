from abc import ABC, abstractmethod
from http_session import Session as HTTPSession
from horseman.datastructures import Query, Cookies, ContentType
from horseman.parsers import Data as FormData
from horseman.types import Environ


class URLTools(ABC):
    method: str
    path: str
    script_name: str
    domain: str
    application_uri: str

    @abstractmethod
    def uri(self, include_query: bool = True) -> str:
        ...


__all__ = ['URLTools', 'HTTPSession', 'Query', 'Cookies', 'ContentType', 'FormData', 'Environ']