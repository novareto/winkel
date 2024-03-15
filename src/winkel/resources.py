from typing import NamedTuple
from pathlib import PurePosixPath
from collections import deque


class JSResource(NamedTuple):
    path: str | PurePosixPath
    bottom: bool = False
    integrity: str | None = None
    crossorigin: str | None = None

    def __str__(self):
        value = f'src="{self.path}"'
        if self.crossorigin:
            value += f' crossorigin="{self.crossorigin}"'
        if self.integrity:
            value += f' integrity="{self.integrity}"'
        return f'''<script {value}></script>\r\n'''

    def __bytes__(self):
        return str(self).encode()


class CSSResource(NamedTuple):
    path: str | PurePosixPath
    bottom: bool = False
    integrity: str | None = None
    crossorigin: str | None = None

    def __str__(self):
        value = f'href="{self.path}"'
        if self.crossorigin:
            value += f' crossorigin="{self.crossorigin}"'
        if self.integrity:
            value += f' integrity="{self.integrity}"'
        return f'''<link rel="stylesheet" {value} />\r\n'''

    def __bytes__(self):
        return str(self).encode()


known_extensions = {
    "js": JSResource,
    "css": CSSResource
}


class NeededResources(deque[JSResource|CSSResource]):

    def add_resource(self, path: str, rtype: str, *,
                     bottom: bool = False,
                     integrity: str | None = None,
                     crossorigin: str | None = None):
        if factory := known_extensions.get(rtype):
            self.append(factory(
                path,
                bottom=bottom,
                integrity=integrity,
                crossorigin=crossorigin
            ))
        else:
            raise KeyError(f'Unknown resource type: {rtype}.')

    def apply(self, body: str | bytes):
        if not len(self):
            return body

        if isinstance(body, str):
            body = body.encode()
        top = b''
        bottom = b''
        for resource in self:
            if resource.bottom:
                bottom += bytes(resource)
            else:
                top += bytes(resource)
        if top:
            body = body.replace(b'</head>', top + b'</head>', 1)
        if bottom:
            body = body.replace(b'</body>', bottom + b'</body>', 1)
        return body
