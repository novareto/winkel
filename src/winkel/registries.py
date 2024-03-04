from enum import Enum
from wrapt import ObjectProxy
from typing import Tuple, NamedTuple, Sequence, Literal
from collections import UserList, UserDict
from plum import Signature
from resolver import SignatureResolver
from prejudice.errors import ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints


DEFAULT = ""
Default = Literal[DEFAULT]


class Lookup(str, Enum):
    ALL = 'all'


class ProxyMetadata(NamedTuple):
    name: str = ''
    title: str = ''
    description: str = ''
    classifiers: set[str] = set()
    conditions: Sequence[Predicate] | None = None


class Proxy(ObjectProxy):

    __metadata__: ProxyMetadata

    def __init__(self, wrapped, **kwargs):
        super().__init__(wrapped)
        self.__metadata__ = ProxyMetadata(**kwargs)

    def __call__(self, *args, **kwargs):
        print('entering', self.__wrapped__.__name__)
        try:
            return self.__wrapped__(*args, **kwargs)
        finally:
            print('exiting', self.__wrapped__.__name__)


def base_sorter(result: Tuple[Signature, Proxy]):
    return result[0], proxy.__metadata__.name


class Sequence():
    pass


class Mapping(UserDict[Signature, ObjectProxy]):

    def __init__(self, data=None):
        self.resolver: Resolver = SignatureResolver()
        super().__init__(data)

    def __setitem__(self, signature: Signature, proxy: ObjectProxy):
        self.resolver.register(signature)
        super().__setitem__(signature, proxy)

    def lookup(self, *args, sorter = base_sorter):
        found = []
        for signature, proxy in self.items():
            if signature.match(args):
                found.append((signature, proxy))
        return sorted(found, key=sorter)

    def match(self, *args, name: str | Lookup, sorter = base_sorter):
        return self.lookup(*args, name, sorter=sorter)

    def match_grouped(self, *args, sorter = base_sorter):
        proxies = {}
        for e in self.lookup(*args, Lookup.ALL, sorter=sorter):
            name = e.__metadata__.name
            if name not in proxies:
                proxies[name] = e
        return proxies

    def fetch(self, *args, name: str = DEFAULT) -> Proxy:
        match = self.resolver.resolve((*args, name))
        return self[match]

    def register(self, discriminant, name: str=DEFAULT, **kwargs):
        def register_resolver(func):
            proxy = Proxy(func, **kwargs)
            signature = Signature(
                *discriminant, Literal[name] | Literal[Lookup.ALL])
            self[signature] = proxy
            return func
        return register_resolver



registry1 = Mapping()
registry2 = Mapping()

@registry1.register((int, str))
def my_func():
    print('toto')


@registry2.register((int, str))
def my_func2():
    print('titi')


registry1 |= registry2

found = registry1.fetch(1, 'abc')
found()
