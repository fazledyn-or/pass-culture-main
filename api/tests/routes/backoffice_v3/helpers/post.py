from base64 import b64encode
from urllib.parse import unquote_plus

from flask import g
from flask import url_for

from pcapi.core.users import factories as users_factories

from . import base
from . import unauthorized


class PostEndpointWithoutPermissionHelper(base.BaseHelper):
    """
    Can be used when no permission is required
    """

    # Number of queries to fetch csrf token from homepage
    # Same as expected_num_queries in HomePageTest
    fetch_csrf_num_queries = 4

    @property
    def method(self) -> str:
        return "post"

    @property
    def form(self) -> dict:
        return {"csrf_token": g.get("csrf_token", None)}

    def fetch_csrf_token(self, client):
        # will generate a csrf token (for the logout button)
        client.get(url_for("backoffice_v3_web.home"))

    def post_to_endpoint(self, client, form=None, **url_kwargs):
        self.fetch_csrf_token(client)

        url = url_for(self.endpoint, **url_kwargs)

        if form is None:
            form = {}

        form.update(self.form)
        return client.post(url, form=form)

    def test_not_logged_in(self, client):
        self.fetch_csrf_token(client)

        client_method = getattr(client, self.method)
        response = client_method(self.path, form=self.form)

        assert response.status_code in (302, 303)
        if hasattr(self, "custom_redirect"):
            expected_urls = [url_for(self.custom_redirect, _external=True)]
        else:
            expected_urls = [
                url_for(
                    "backoffice_v3_web.home",
                    _external=True,
                    redirect=b64encode(unquote_plus(self.path).encode() + b"?"),
                ),
                url_for(
                    "backoffice_v3_web.home",
                    _external=True,
                    redirect=b64encode(self.path.encode() + b"?"),
                ),
                url_for(
                    "backoffice_v3_web.home",
                    _external=True,
                    redirect=b64encode(unquote_plus(self.path).encode()),
                ),
                url_for(
                    "backoffice_v3_web.home",
                    _external=True,
                    redirect=b64encode(self.path.encode()),
                ),
            ]
        assert response.location in expected_urls

    def test_missing_csrf_token(self, client):
        user = users_factories.UserFactory()

        authenticated_client = client.with_bo_session_auth(user)
        client_method = getattr(authenticated_client, self.method)

        response = client_method(self.path, form=self.form)
        assert response.status_code == 400


class PostEndpointHelper(PostEndpointWithoutPermissionHelper, unauthorized.UnauthorizedHelperBase):
    """
    Provides helper method to post with csrf token and checks required permissions
    """

    def test_missing_permission(self, client):
        user = self.setup_user()

        self.fetch_csrf_token(client)

        authenticated_client = client.with_bo_session_auth(user)
        client_method = getattr(authenticated_client, self.method)

        response = client_method(self.path, form=self.form)
        assert response.status_code == 403

    def test_no_backoffice_profile(self, client):
        user = users_factories.UserFactory()

        self.fetch_csrf_token(client)

        authenticated_client = client.with_bo_session_auth(user)
        client_method = getattr(authenticated_client, self.method)

        response = client_method(self.path, form=self.form)

        assert response.status_code == 403
