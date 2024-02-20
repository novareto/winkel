import typing as t
import orjson
from pathlib import Path
from http import HTTPStatus
from horseman.types import HTTPCode
from horseman.response import Headers, Response as BaseResponse


REDIRECT = frozenset((
    HTTPStatus.MULTIPLE_CHOICES,
    HTTPStatus.MOVED_PERMANENTLY,
    HTTPStatus.FOUND,
    HTTPStatus.SEE_OTHER,
    HTTPStatus.NOT_MODIFIED,
    HTTPStatus.USE_PROXY,
    HTTPStatus.TEMPORARY_REDIRECT,
    HTTPStatus.PERMANENT_REDIRECT
))


def file_iterator(path: Path, chunk: int = 4096) -> t.Iterator[bytes]:
    with path.open('rb') as reader:
        while True:
            data = reader.read(chunk)
            if not data:
                break
            yield data


class Response(BaseResponse):

    @classmethod
    def redirect(cls, location, code: HTTPCode = 303,
                 body: t.Optional[t.Iterable] = None,
                 headers: t.Optional[Headers] = None) -> 'Response':
        if code not in REDIRECT:
            raise ValueError(f"{code}: unknown redirection code.")
        if not headers:
            headers = {'Location': location}
        else:
            headers['Location'] = location
        return cls(code, body, headers)

    @classmethod
    def from_file_iterator(cls, filename: str, body: t.Iterable[bytes],
                           headers: t.Optional[Headers] = None):
        if headers is None:
            headers = {
                "Content-Disposition": f"attachment;filename={filename}"}
        elif "Content-Disposition" not in headers:
            headers["Content-Disposition"] = (
                f"attachment;filename={filename}")
        return cls(200, body, headers)

    @classmethod
    def from_file_path(cls, path: Path):
        return cls.from_file_iterator(file_iterator(path))

    @classmethod
    def to_json(cls, code: HTTPCode = 200, body: t.Optional[t.Any] = None,
                headers: t.Optional[Headers] = None):
        data = orjson.dumps(body)
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        else:
            headers['Content-Type'] = 'application/json'
        return cls(code, data, headers)

    @classmethod
    def from_json(cls, code: HTTPCode = 200, body: t.AnyStr = '',
                  headers: t.Optional[Headers] = None):
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        else:
            headers['Content-Type'] = 'application/json'
        return cls(code, body, headers)

    @classmethod
    def html(cls, code: HTTPCode = 200, body: t.AnyStr = '',
             headers: t.Optional[Headers] = None):
        if headers is None:
            headers = {'Content-Type': 'text/html; charset=utf-8'}
        else:
            headers['Content-Type'] = 'text/html; charset=utf-8'
        return cls(code, body, headers)


__all__ = ('Response',)
