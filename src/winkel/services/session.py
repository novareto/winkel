import itsdangerous
import logging
from contextlib import contextmanager
from functools import cached_property
from horseman.datastructures import Cookies
from http_session.cookie import SameSite, HashAlgorithm, SignedCookieManager
from http_session.meta import Store
from transaction import TransactionManager
from winkel.response import Response
from winkel.request import URLUtils
from winkel.scope import Scope
from winkel.service import Service, factories, computed_field
from winkel.meta import HTTPSession


logger = logging.getLogger(__name__)


class Session(Service):
    store: Store
    secret: str
    samesite: SameSite = SameSite.lax
    httponly: bool = True
    digest: str = HashAlgorithm.sha1.name
    TTL: int = 3600
    cookie_name: str = 'sid'
    secure: bool = True
    save_new_empty: bool = False
    salt: str | None = None
    domain: str | None = None

    @computed_field
    @cached_property
    def manager(self) -> SignedCookieManager:
        return SignedCookieManager(
            self.store,
            self.secret,
            salt=self.salt,
            digest=self.digest,
            TTL=self.TTL,
            cookie_name=self.cookie_name,
        )

    @factories.scoped
    def http_session_factory(self, scope: Scope) -> HTTPSession:
        return scope.stack.enter_context(self.http_session(scope))

    @contextmanager
    def http_session(self, scope: Scope):
        new = True
        cookies = scope.get(Cookies)
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

        session: Session = self.manager.session_factory(
            sid, self.manager.store, new=new
        )

        try:
            yield session
        except Exception:
            # Maybe log.
            raise
        else:
            response = scope.get(Response)
            if not session.modified and (
                    session.new and self.save_new_empty):
                session.save()

            if session.modified:
                if response.status < 400:
                    if TransactionManager in scope:
                        tm = scope.get(TransactionManager)
                        if not tm.isDoomed():
                            session.persist()
                    else:
                        session.persist()

            elif session.new:
                return

            url = scope.get(URLUtils)
            domain = self.domain or url.domain
            cookie = self.manager.cookie(
                session.sid,
                url.script_name or '/',
                domain,
                secure=self.secure,
                samesite=self.samesite,
                httponly=self.httponly
            )
            response.cookies[self.manager.cookie_name] = cookie
