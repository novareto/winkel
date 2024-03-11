import os
from http import HTTPStatus
from pathlib import PurePosixPath, Path
from pkg_resources import resource_filename
from horseman.mapping import Mapping
from horseman.types import Environ, StartResponse
from winkel.service import Installable, Mountable
from mimetypes import guess_type


class Library:
    base_path: Path
    _resources: set[Path]

    def __init__(self,
                 name: str,
                 base_path: str | Path):
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
            return [b'Nothing matches the given URI']

        headers = []
        stats = os.stat(filepath)
        size = stats.st_size
        headers.append(("Content-Length", str(size)))

        content_type, encoding = guess_type(filepath)
        if not content_type:
            content_type = 'octet/steam'
        elif content_type.startswith("text/") or \
                content_type == "application/javascript":
            content_type += "; charset=utf-8"

        headers.append(("Content-Type", content_type))
        start_response('200 OK', headers)

        if environ['REQUEST_METHOD'] == "HEAD":
            return []

        filelike = filepath.open('rb')
        block_size = 4096
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

    def add_static(self,
                   name: str,
                   base_path: str | Path) -> Library:
        resource = Path(base_path)
        name = name.lstrip('/')
        if not resource.exists():
            raise OSError(f'{resource} does not exist.')
        if not resource.is_dir():
            raise TypeError('Library base path must be a directory.')
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

    def get_package_static_uri(self, package_path: str):
        library, name, path = self.match('/' + package_path)
        return (
            PurePosixPath(self.name) / name.lstrip('/') / path.lstrip('/'))

    def get_static_uri(self, name: str, path: str):
        library, name, path = self.resolve(f'/{name}/{path}')
        return (
            PurePosixPath(self.name) / name.lstrip('/') / path.lstrip('/'))
