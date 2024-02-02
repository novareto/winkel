import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from prejudice.errors import ConstraintError, ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints
from plum import Signature
from collections import UserList, UserDict
from winkel.signature import SignatureResolver


T = t.TypeVar('T')
K = t.TypeVar('K', bound=t.Hashable)


@dataclass
class Item(t.Generic[K, T]):
    value: T
    identifier: K
    name: str = ''
    title: str = ''
    description: str = ''
    conditions: t.Tuple[Predicate] = field(default_factory=tuple)
    classifiers: t.FrozenSet[str] = field(default_factory=frozenset)
    metadata: t.Mapping[str, t.Any] = field(default_factory=dict)

    def __name__(self):
        return self.name

    def evaluate(self, *args, **kwargs) -> t.Optional[ConstraintsErrors]:
        return resolve_constraints(self.conditions, self, *args, **kwargs)

    def __call__(self, *args, silence_errors=True, **kwargs):
        if not isinstance(self.value, t.Callable):
            raise ValueError(f'{self.value} is not callable.')
        if errors := self.evaluate(*args, **kwargs):
            if not silence_errors:
                raise errors
        else:
            return self.value(*args, **kwargs)


I = t.TypeVar('I', bound=Item)


class Items(t.Generic[I], ABC):

    factory: t.Type[I] = Item

    @abstractmethod
    def add(self, item: I):
        pass

    def spawn(self,
              value: T,
              identifier: K,
              name: str = '',
              title: str = '',
              description: str = '',
              conditions: t.Optional[t.Iterable[Predicate]] = None,
              classifiers: t.Optional[t.Iterable[str]] = None,
              **metadata: t.Any
              ):

        if classifiers is None:
            classifiers = ()

        if conditions is None:
            conditions = ()

        return self.factory(
            identifier=identifier,
            name=name,
            title=title,
            value=value,
            classifiers=frozenset(classifiers),
            conditions=tuple(conditions),
            metadata=metadata
        )

    def create(self, value, *args, **kwargs):
        item = self.spawn(value, *args, **kwargs)
        self.add(item)
        return item

    def register(self, *args, **kwargs):
        def register_resolver(func):
            self.create(func, *args, **kwargs)
            return func
        return register_resolver


class ItemCollection(t.Generic[I], Items[I], UserList):

    def add(self, item: I):
        self.append(item)

    def __or__(self, other):
        return self.__class__([*self, *other])


class ItemMapping(t.Generic[K, I], Items[I], UserDict[K, I]):

    def add(self, item: I):
        self[item.identifier] = item


class ItemResolver(ItemMapping[Signature, I]):

    resolver: SignatureResolver

    def __init__(self, *args, **kwargs):
        self.resolver = SignatureResolver()
        super().__init__(*args, **kwargs)

    def __setitem__(self, signature: Signature, item: Item):
        self.resolver.register(item.identifier)
        super().__setitem__(signature, item)

    def match_all(self, *args):
        found = []
        for signature, item in self.items():
            if signature.match(args):
                found.append(item)
        return sorted(found, key=lambda item: item.identifier)

    def lookup(self, *args):
        match = self.resolver.resolve(args)
        return self[match]

    def cast(self, *args, **kwargs):
        item = self.lookup(*args)
        return item(*args, **kwargs)


class TypeRegistry(UserDict[t.Type, Items]):

    _factory: t.Type[Items] = ItemMapping

    @staticmethod
    def lineage(cls):
        for parent in cls.__mro__:
            if parent is object:
                break
            yield parent

    def spawn(self, key):
        if key not in self:
            return self.setdefault(key, self._factory())
        return self[key]

    def add(self, key: t.Type, *args, **kwargs) -> Item:
        store = self.spawn(key)
        item = store.spawn(*args, **kwargs)
        return store.add(item)

    def register(self,
                 discriminant: t.Type,
                 *args, **kwargs) -> t.NoReturn:

        def register_add(value):
            self.add(discriminant, value, *args, **kwargs)
            return value

        return register_add

    def values(self, target, direct=True):
        keys = (target,) if direct else self.lineage(target)
        for cls in keys:
            if cls in self:
                yield from self[cls].values()

    def get(self, target, name: str, direct=True):
        keys = (target,) if direct else self.lineage(target)
        for cls in keys:
            if cls in self and name in self[cls]:
                return self[cls][name]

    def __or__(self, other):
        result = self.__class__(**self)
        for k, v in other.items():
            if k in result and isinstance(v, (t.Mapping, ItemCollection)):
                result[k] = result[k] | other[k]
            else:
                result[k] = other[k]
        return result


class ItemsContainer:
    store: Items

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(self.store | other.store)


def one_of(items: t.Iterable[I], *classifiers: str) -> t.Iterator[I]:
    if not classifiers:
        raise KeyError('`one_of` takes at least one classifier.')
    classifiers = set(classifiers)
    for item in items:
        if item.classifiers & classifiers:
            yield item


def exact(items: t.Iterable[I], *classifiers: str) -> t.Iterator[I]:
    if not classifiers:
        raise KeyError('`exact` takes at least one classifier.')
    classifiers = set(classifiers)
    for item in items:
        if classifiers == item.classifiers:
            yield item


def partial(items: t.Iterable[I], *classifiers: str) -> t.Iterator[I]:
    if not classifiers:
        raise KeyError('`partial` takes at least one classifier.')
    classifiers = set(classifiers)
    for item in items:
        if item.classifiers >= classifiers:
            yield item
