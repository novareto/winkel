import itsdangerous
import typing as t
from pydantic import computed_field
from transaction import TransactionManager
from horseman.datastructures import Cookies
from http_session.meta import Store
from http_session.session import Session
from http_session.cookie import SameSite, HashAlgorithm, SignedCookieManager
from winkel.pipeline import Handler, Configuration
from rodi import CannotResolveTypeException
from functools import wraps, cached_property


def http_session_factory(context) -> Session:
    new = True
    cookies = context.get(Cookies)
    manager = context.get(SignedCookieManager)
    if (sig := cookies.get(manager.cookie_name)):
        try:
            sid = str(manager.verify_id(sig), 'utf-8')
            new = False
        except itsdangerous.exc.SignatureExpired:
            # Session expired. We generate a new one.
            pass
        except itsdangerous.exc.BadTimeSignature:
            # Discrepancy in time signature.
            # Invalid, generate a new one
            pass

    if new is True:
        sid = manager.generate_id()

    return manager.session_factory(
        sid, manager.store, new=new
    )


class HTTPSession(Configuration):
    store: Store
    secret: str
    samesite: SameSite = SameSite.lax
    httponly: bool = True
    digest: str = HashAlgorithm.sha1.name
    TTL: int = 300
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

    def on_response(self, app, request, response):
        session = request.get(Session)
        if not session.modified and (
                session.new and self.save_new_empty):
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

        domain = self.domain or \
            request.environ['HTTP_HOST'].split(':', 1)[0]
        cookie = self.manager.cookie(
            session.sid,
            request.environ.script_name or '/',
            domain,
            secure=self.secure,
            samesite=self.samesite,
            httponly=self.httponly
        )
        response.cookies[self.manager.cookie_name] = cookie
        return response

    def install(self, app, order: int = 99):
        app.services.register(SignedCookieManager, instance=self.manager)
        app.services.add_scoped_by_factory(http_session_factory)
        app.hooks['response'].add(self.on_response)