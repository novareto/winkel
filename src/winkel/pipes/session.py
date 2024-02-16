import itsdangerous
import typing as t
from transaction import TransactionManager
from horseman.datastructures import Cookies
from http_session.meta import Store
from http_session.session import Session
from http_session.cookie import SameSite, HashAlgorithm, SignedCookieManager
from winkel.pipeline import Handler, MiddlewareFactory
from rodi import CannotResolveTypeException


class HTTPSession(MiddlewareFactory):

    id = 'http-session'
    manager: SignedCookieManager

    class Configuration(t.NamedTuple):
        store: Store
        secret: str
        samesite: SameSite = SameSite.lax
        httponly: bool = True
        digest: str = HashAlgorithm.sha1.name
        TTL: int = 300
        cookie_name: str = 'sid'
        secure: bool = True
        save_new_empty: bool = False
        salt: t.Optional[str] = None
        domain: t.Optional[str] = None

    def __post_init__(self):
        self.manager = SignedCookieManager(
            self.config.store,
            self.config.secret,
            salt=self.config.salt,
            digest=self.config.digest,
            TTL=self.config.TTL,
            cookie_name=self.config.cookie_name,
        )

    def factory(self, context) -> Session:
        new = True
        cookies = context.get(Cookies)
        if (sig := cookies.get(self.manager.cookie_name)):
            try:
                sid = str(self.manager.verify_id(sig), 'utf-8')
                new = False
            except itsdangerous.exc.SignatureExpired:
                # Session expired. We generate a new one.
                pass
            except itsdangerous.exc.BadTimeSignature:
                # Discrepancy in time signature.
                # Invalid, generate a new one
                pass

        if new is True:
            sid = self.manager.generate_id()

        return self.manager.session_factory(
            sid, self.manager.store, new=new
        )

    def install(self, app, order: int):
        app.services.add_scoped_by_factory(self.factory)
        app.pipeline.add(self, order)

    def __call__(self,
                 handler: Handler,
                 globalconf: t.Optional[t.Mapping] = None):

        def http_session_middleware(request):

            response = handler(request)

            session = request.get(Session)
            if not session.modified and (
                    session.new and self.config.save_new_empty):
                session.save()

            if session.modified:
                if response.status < 400:
                    try:
                        tm = request.get(TransactionManager)
                        if not tm.isDoomed():
                            session.persist()
                    except CannotResolveTypeException:
                        session.persist()

            elif session.new:
                return response

            domain = self.config.domain or \
                request.environ['HTTP_HOST'].split(':', 1)[0]
            cookie = self.manager.cookie(
                session.sid,
                request.environ.script_name or '/',
                domain,
                secure=self.config.secure,
                samesite=self.config.samesite,
                httponly=self.config.httponly
            )
            response.cookies[self.manager.cookie_name] = cookie
            return response

        return http_session_middleware
