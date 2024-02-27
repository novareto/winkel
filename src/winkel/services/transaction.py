from typing import Callable
from contextlib import contextmanager
from transaction import TransactionManager
from winkel.response import Response
from winkel.service import Service, factories


class Transactional(Service):
    factory: Callable[[], TransactionManager] = TransactionManager

    @factories.scoped
    def transaction_factory(self, context) -> TransactionManager:
        return context.stack.enter_context(self.transactional(context))

    @contextmanager
    def transactional(self, context):
        manager = self.factory()
        with manager as txn:
            yield manager
            response = context.get(Response)
            if txn.isDoomed() or response.status >= 400:
                txn.abort()
