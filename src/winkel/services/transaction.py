from transaction import TransactionManager
from winkel.service import Service, handlers, factories


class Transactional(Service):

    @factories.scoped
    def transaction_factory(self, context) -> TransactionManager:
        manager = TransactionManager()
        manager.begin()
        return manager

    @handlers.on_response
    def abort_or_commit(self, app, request, response) -> None:
        if TransactionManager in request:
            txn = request.get(TransactionManager)
            if txn.isDoomed() or response.status >= 400:
                txn.abort()
            else:
                txn.commit()

    @handlers.on_error
    def handle_error(self, app, request, error):
        if TransactionManager in request:
            txn = request.get(TransactionManager)
            txn.abort()
