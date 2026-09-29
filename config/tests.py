"""V13: "Remember me" session-expiry control on the white-label login.

Checked -> 30-day session (REMEMBER_ME_COOKIE_AGE); unchecked/absent -> expires
at browser close (set_expiry(0)). Overrides Wagtail's form_valid which uses
SESSION_COOKIE_AGE (1d).

These tests POST directly to the LoginView (no external service deps).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from config.customviews import REMEMBER_ME_COOKIE_AGE

User = get_user_model()


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
)
class RememberMeLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="remember",
            email="remember@example.com",
            password="secret",
        )

    def _login(self, remember=None, follow=False):
        """POST to the login endpoint. Returns the response (redirect by default)."""
        login_url = reverse("custom_login_view")
        data = {"username": "remember", "password": "secret"}
        if remember is not None:
            data["remember"] = remember
        return self.client.post(login_url, data, follow=follow)

    # --- V13: observable behaviour is the Set-Cookie Max-Age ---

    def test_remember_me_true_sets_30_day_cookie(self):
        """Checked: sessionid cookie Max-Age ≈ 30 days (2592000)."""
        response = self._login(remember="on")
        # POST redirects to wagtail admin home (302), follow=True gets the page
        self.assertIn(response.status_code, (200, 302))
        cookie = self.client.cookies.get("sessionid")
        self.assertIsNotNone(cookie)
        # Max-Age is present and matches 30 days
        self.assertEqual(cookie.get("max-age"), REMEMBER_ME_COOKIE_AGE)

    def test_remember_me_false_sets_session_cookie(self):
        """Unchecked: sessionid cookie has NO Max-Age (browser-close session cookie)."""
        self._login()
        cookie = self.client.cookies.get("sessionid")
        self.assertIsNotNone(cookie)
        # No Max-Age → session cookie → expires when browser closes
        self.assertEqual(cookie.get("max-age"), "")

    def test_remember_me_true_stores_logged_in_user(self):
        """Checked: session stores the user ID — a real authenticated session."""
        self._login(remember="on")
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.user.pk),
        )
