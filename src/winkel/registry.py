import typing as t
from types import EllipsisType
from elementalist.registries import SignatureMapping, DEFAULT


class ComponentRegistry(SignatureMapping):
    Types: t.ClassVar[t.Type[t.NamedTuple]]

    def create(self,
               value: t.Any,
               discriminant: t.Sequence[t.Type] | t.Mapping[str, t.Type] | EllipsisType,
               name: str = DEFAULT,
               **kwargs):
        if discriminant is ...:
            discriminant = self.Types()
        elif isinstance(discriminant, t.Mapping):
            discriminant = self.Types(**discriminant)
        elif isinstance(discriminant, t.Sequence):
            discriminant = self.Types(*discriminant)
        else:
            raise TypeError(f"Don't know how to handle {discriminant!r}.")
        return super().create(value, discriminant, name=name, **kwargs)

