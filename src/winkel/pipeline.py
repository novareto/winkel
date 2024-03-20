import typing as t
import logging
from functools import reduce
from winkel.response import Response


logger = logging.getLogger(__name__)


Handler = t.Callable[[...], Response]
HandlerWrapper = t.Callable[[Handler], Handler]


def wrapper(chain: t.Iterable[HandlerWrapper], wrapped: Handler) -> Handler:
    logging.debug(
        f'Wrapping {wrapped!r} into middleware pipeline: {chain!r}.')
    return reduce(
        lambda x, y: y(x),
        (m for m in reversed(chain)),
        wrapped
    )
