from typing import NamedTuple
from pathlib import PurePosixPath, Path
from pkg_resources import resource_filename
from horseman.mapping import Mapping
from horseman.types import Environ, StartResponse
from collections import defaultdict
from winkel.service import Installable, Mountable


class JSResource(NamedTuple):
    path: str | PurePosixPath
    integrity: str | None = None
    crossorigin: str | None = None

    def __str__(self):
        value = f'src="{self.path}"'
        if self.crossorigin:
            value += f'crossorigin="{self.crossorigin}"'
        if self.integrity:
            value += f'integrity="{self.integrity}"'
        return f'''<script {value}></script>'''

    def __bytes__(self):
        return str(self).encode()


class CSSResource(NamedTuple):
    path: str | PurePosixPath
    integrity: str | None = None
    crossorigin: str | None = None

    def __str__(self):
        value = f'href="{self.path}"'
        if self.crossorigin:
            value += f'crossorigin="{self.crossorigin}"'
        if self.integrity:
            value += f'integrity="{self.integrity}"'
        return f'''<link rel="stylesheet" {value} />'''

    def __bytes__(self):
        return str(self).encode()


known_extensions = {
    "js": JSResource,
    "css": CSSResource
}


class NeededResources:
    top: dict
    bottom: dict

    def __init__(self):
        self.top = []
        self.bottom = []

    def add_resource(self, path: str, rtype: str, *,
                     bottom: bool = False,
                     integrity: str | None = None,
                     crossorigin: str | None = None):
        if factory := known_extensions.get(rtype):
            if bottom:
                self.bottom.append(factory(
                    path, integrity=integrity, crossorigin=crossorigin
                ))
            else:
                self.top.append(factory(
                    path, integrity=integrity, crossorigin=crossorigin
                ))

    def apply(self, body: str | bytes):
        if isinstance(body, str):
            body = body.encode()
        if self.top:
            top = b''.join((bytes(r) for r in self.top))
            body = body.replace(b'</head>', top + b'</head>', 1)
        if self.bottom:
            bottom = b''.join((bytes(r) for r in self.bottom))
            body = body.replace(b'</body>', bottom + b'</body>', 1)
        return body


class Library:
    base_path: PurePosixPath
    _resources: set[Path]

    def __init__(self,
                 name: str,
                 base_path: str | PurePosixPath):
        self.name = name
        base_path = Path(base_path)
        if not base_path.is_absolute():
            raise ValueError('Base path needs to be absolute.')
        self.base_path = base_path
        self._resources = set()

    def finalize(self, restrict=('*.js', '*.css')):
        self._resources = set()
        if not restrict:
            restrict = ('*',)
        for matcher in restrict:
            for path in self.base_path.rglob(matcher):
                self._resources.add(path)

    def __call__(self, environ: Environ, start_response: StartResponse):
        path_info = environ.get(
            'PATH_INFO', '').encode('latin-1').decode('utf-8') or '/'
        filepath = self.base_path / PurePosixPath(path_info.lstrip('/'))

        if filepath not in self._resources:
            start_response('404 Not Found', [])
            return []

        filelike = filepath.open('rb')
        block_size = 4096
        status = '200 OK'
        response_headers = [('Content-type', 'octet/stream')]
        start_response(status, response_headers)
        if 'wsgi.file_wrapper' in environ:
            return environ['wsgi.file_wrapper'](filelike, block_size)
        else:
            return iter(lambda: filelike.read(block_size), '')


class StaticAccessor(Mapping):
    by_path: dict

    def __init__(self, *args, **kwargs):
        self.by_path = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, name, library):
        self.by_path[library.base_path] = library
        super().__setitem__(name, library)

    def add_static(self, name: str, base_path: str | PurePosixPath) -> Library:
        resource = Path(base_path)
        name = name.lstrip('/')
        if not resource.exists():
            raise OSError(f'{resource} does not exist.')
        if not resource.is_dir():
            raise TypeError(f'Library base path must be a directory.')
        library = Library(name, base_path=resource)
        self[name] = library
        return library

    def add_package_static(self, package_static: str):
        # package_static of form:  package_name:path
        pkg, resource_name = package_static.split(":")
        resource = Path(resource_filename(pkg, resource_name))
        return self.add_static(package_static, resource)


class ResourceManager(StaticAccessor, Installable, Mountable):

    def __init__(self, name: str, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def install(self, services):
        services.add_instance(self, ResourceManager)
        services.add_scoped(NeededResources)

    def get_package_static_uri(self, package_path: str):
        environ = {'SCRIPT_NAME': '', 'PATH_INFO': ''}
        library = self.resolve('/'+package_path, environ)
        uri = PurePosixPath(self.name) / environ['SCRIPT_NAME'].lstrip('/') / environ['PATH_INFO'].lstrip('/')
        return uri

    def get_static_uri(self, name: str, path: str):
        environ = {'SCRIPT_NAME': '', 'PATH_INFO': ''}
        library = self.resolve(f'/{name}/{path}', environ)
        uri = PurePosixPath(self.name) / environ['SCRIPT_NAME'].lstrip('/') / environ['PATH_INFO'].lstrip('/')
        return uri