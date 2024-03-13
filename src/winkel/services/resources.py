import os
from pathlib import PurePosixPath, Path
from pkg_resources import resource_filename
from winkel.response import Response, FileWrapperResponse
from winkel.service import Installable, Mountable
from mimetypes import guess_type
from autoroutes import Routes


class Library:
    name: str
    base_path: Path

    def __init__(self, name: str, base_path: str | Path, restrict=('*',)):
        resource = Path(base_path)
        if not resource.exists():
            raise OSError(f'{resource} does not exist.')
        if not resource.is_dir():
            raise TypeError('Library base path must be a directory.')
        if not base_path.is_absolute():
            raise ValueError('Base path needs to be absolute.')
        self.name = name
        self.base_path = base_path
        self.restrictions = restrict

    def resources(self):
        for matcher in self.restrictions:
            for path in self.base_path.rglob(matcher):
                yield self.name / path.relative_to(self.base_path), path


class StaticAccessor:
    name: str
    resources: Routes | None
    libraries: dict[str, Library]

    def __init__(self, name: str):
        self.name = name
        self.resources = None
        self.libraries = dict()

    def finalize(self):
        self.resources = Routes()
        for name, library in self.libraries.items():
            for uri, full_path in library.resources():
                stats = os.stat(full_path)
                content_type, encoding = guess_type(full_path)
                if not content_type:
                    content_type = 'octet/steam'
                elif content_type.startswith("text/") or \
                        content_type == "application/javascript":
                    content_type += "; charset=utf-8"
                info = {
                    "filepath": full_path,
                    "size": stats.st_size,
                    "content_type": content_type
                }
                self.resources.add(str('/' / PurePosixPath(uri)), **info)

    def add_static(self, name: str, base_path: str | Path) -> Library:
        library = self.libraries[name] = Library(name, base_path)
        return library

    def add_package_static(self, package_static: str):
        # package_static of form:  package_name:path
        pkg, resource_name = package_static.split(":")
        resource = Path(resource_filename(pkg, resource_name))
        return self.add_static(package_static, resource)


class ResourceManager(StaticAccessor, Installable, Mountable):

    def install(self, services):
        services.add_instance(self, ResourceManager)

    def get_package_static_uri(self, package_path: str):
        return PurePosixPath(self.name) / package_path

    def get_static_uri(self, name: str, path: str):
        return PurePosixPath(self.name) / name.lstrip('/') / path.lstrip('/')

    def resolve(self, path_info, environ):
        match, _ = self.resources.match(path_info)
        if not match:
            return Response(status=404)

        headers = {
            "Content-Length": str(match["size"]),
            "Content-Type": match["content_type"]
        }
        if environ['REQUEST_METHOD'] == "HEAD":
            return Response(200, headers=headers)

        if 'wsgi.file_wrapper' not in environ:
            return Response.from_file_path(match["filepath"], headers=headers)
        return FileWrapperResponse(match["filepath"], headers=headers)
