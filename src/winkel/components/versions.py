import typing as t
from collections import UserDict
from elementalist.element import Element
from elementalist.collections import ElementMapping, ElementCollection


class Namespace(ElementMapping[float, Element]):

    latest: float = 0.0

    def add(self, item: Element):
        super().add(item)
        if item.identifier > self.latest:
            self.latest = item.identifier

    def spawn(self,
              value: t.Any,
              identifier: t.Optional[float] = None,
              **kwargs):

        if identifier is None:
            version = 1.0
        else:
            version = float(identifier)

        if version <= 0:
            raise ValueError('Version must be positive and non-null.')

        if version in self:
            raise ValueError(f'Version {version} already exists.')

        return super().spawn(value, version, **kwargs)


class Store(UserDict):
    _factory = Namespace

    def add(self, key, *args, **kwargs):
        if key not in self:
            self[key] = self._factory()
        return self[key].add(*args, **kwargs)

    def create(self, key, *args, **kwargs):
        if key not in self:
            self[key] = self._factory()
        return self[key].create(*args, **kwargs)

    def register(self, key: t.Hashable, *args, **kwargs) -> t.NoReturn:
        def register_new(value):
            self.create(key, value, *args, **kwargs)
            return value
        return register_new

    def get(self, key, *trail):
        return self[key].get(*trail)

    def __or__(self, other):
        result = self.__class__(**self)
        for k, v in other.items():
            if k in result and isinstance(v, (t.Mapping, ElementCollection)):
                result[k] = result[k] | other[k]
            else:
                result[k] = other[k]
        return result


class VersionStore(Store):
    _factory = Store
