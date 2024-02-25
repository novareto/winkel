import typing as t
from transaction import TransactionManager
from winkel.pipeline import Configuration


class Transactional(Configuration):

    def install(self, services, hooks):
        services.add_scoped_by_factory(self.transaction_factory)
        hooks['error'].add(self.on_error)
        hooks['response'].add(self.on_response)

    def transaction_factory(self, context) -> TransactionManager:
        manager = TransactionManager(explicit=True)
        manager.begin()
        return manager

    def on_response(self, app, request, response):
        if TransactionManager in request:
            txn = request.get(TransactionManager)
            if txn.isDoomed() or response.status >= 400:
                txn.abort()
            else:
                txn.commit()
        return response

    def on_error(self, app, request, error):
        if TransactionManager in request:
            txn = request.get(TransactionManager)
            txn.abort()
