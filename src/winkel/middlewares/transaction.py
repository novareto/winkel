import typing as t
from transaction import TransactionManager
from winkel.pipeline import Handler, Configuration
from horseman.response import Response
from functools import wraps


TransactionFactory = t.Callable[[], TransactionManager]


def transaction_factory(context) -> TransactionManager:
    manager = TransactionManager(explicit=True)
    manager.begin()
    return manager


class Transactional(Configuration):

    def install(self, app, order: int):
        app.services.add_scoped_by_factory(transaction_factory)
        app.hooks['error'].add(self.on_error)
        app.hooks['response'].add(self.on_response)

    def on_response(self, app, request, response):
        txn = request.get(TransactionManager)
        if txn.isDoomed() or response.status >= 400:
            txn.abort()
        else:
            txn.commit()
        return response

    def on_error(self, app, request, error):
        txn = request.get(TransactionManager)
        txn.abort()
