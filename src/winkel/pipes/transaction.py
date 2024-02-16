import typing as t
from transaction import TransactionManager
from winkel.pipeline import Handler, MiddlewareFactory
from horseman.response import Response


class Transactional(MiddlewareFactory):

    class Configuration(t.NamedTuple):
        factory: t.Callable[[], TransactionManager] = (
            lambda: TransactionManager(explicit=True)
        )

    def factory(self, context) -> TransactionManager:
        manager = self.config.factory()
        manager.begin()
        return manager

    def install(self, app, order: int):
        app.services.add_scoped_by_factory(self.factory)
        app.pipeline.add(self, order)

    def __call__(self, handler: Handler, globalconf: t.Mapping | None = None):

        def transaction_middleware(request):
            try:
                response = handler(request)
                txn = request.get(TransactionManager)
                if txn.isDoomed() or (
                        isinstance(response, Response)
                        and response.status >= 400):
                    txn.abort()
                else:
                    txn.commit()
                return response
            except Exception:
                txn = request.get(TransactionManager)
                txn.abort()
                raise

        return transaction_middleware
