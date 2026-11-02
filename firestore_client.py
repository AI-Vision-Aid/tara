"""Create Firestore clients with a reliable Cloud Run transport."""

import logging
import os

from google.cloud import firestore
from google.cloud.firestore_v1.services.firestore import FirestoreClient
from google.cloud.firestore_v1.services.firestore.transports import (
    FirestoreRestTransport,
)
from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger("firestore_client")


def _normalize_default_database_url(url):
    return (url.replace("%2528default%2529", "(default)")
            .replace("%28default%29", "(default)"))


def _normalize_default_database_id(database):
    return str(database).replace("%28default%29", "(default)")


class _DefaultDatabaseSession(AuthorizedSession):
    """Keep Firestore's reserved default database ID literal in REST paths."""

    def prepare_request(self, request):
        prepared = super().prepare_request(request)
        prepared.url = _normalize_default_database_url(prepared.url)
        return prepared

    def request(self, method, url, **kwargs):
        url = _normalize_default_database_url(url)
        response = super().request(method, url, **kwargs)
        if response.status_code >= 400:
            logger.error(
                "Firestore REST request failed: method=%s status=%s url=%s body=%s",
                method, response.status_code, response.request.url,
                response.text[:1000])
        return response


class RestFirestoreClient(firestore.Client):
    """High-level Firestore client backed by the generated REST transport."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._database = _normalize_default_database_id(self._database)
        self._database_string_internal = None

    @property
    def _database_string(self):
        if self._database_string_internal is None:
            self._database_string_internal = (
                f"projects/{self.project}/databases/{self._database}")
        return self._database_string_internal

    @property
    def _firestore_api(self):
        if getattr(self, "_firestore_api_internal", None) is None:
            transport = FirestoreRestTransport(
                host=self._target,
                credentials=self._credentials,
                client_info=self._client_info,
            )
            transport._session = _DefaultDatabaseSession(
                transport._credentials, default_host=transport.DEFAULT_HOST)
            transport._prep_wrapped_messages(self._client_info)
            self._firestore_api_internal = FirestoreClient(
                transport=transport,
                client_info=self._client_info,
            )
        return self._firestore_api_internal


def create_firestore_client(**kwargs):
    """Use REST in production and retain the standard emulator client."""
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        return firestore.Client(**kwargs)
    return RestFirestoreClient(**kwargs)
