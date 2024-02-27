import itsdangerous
from contextlib import contextmanager
from functools import cached_property
from horseman.datastructures import Cookies
from http_session.cookie import SameSite, HashAlgorithm, SignedCookieManager
from http_session.meta import Store
from http_session.session import Session
from pydantic import computed_field
from transaction import TransactionManager
from winkel.response import Response
from winkel.service import Service, factories


class HTTPSession(Service):
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
    def http_session_factory(self, context) -> Session:
        return context.stack.enter_context(self.http_session(context))

    @contextmanager
    def http_session(self, context):
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

        session: Session = self.manager.session_factory(
            sid, self.manager.store, new=new
        )

        try:
            yield session
        except:
            print('An error occured, we do not touch the session')
        else:
            response = context.get(Response)
            if not session.modified and (
                    session.new and self.save_new_empty):
                session.save()

            if session.modified:
                if response.status < 400:
                    if TransactionManager in context:
                        tm = context.get(TransactionManager)
                        if not tm.isDoomed():
                            session.persist()
                    else:
                        session.persist()

            elif session.new:
                return

            domain = self.domain or \
                context.environ['HTTP_HOST'].split(':', 1)[0]
            cookie = self.manager.cookie(
                session.sid,
                context.environ.script_name or '/',
                domain,
                secure=self.secure,
                samesite=self.samesite,
                httponly=self.httponly
            )
            response.cookies[self.manager.cookie_name] = cookie
