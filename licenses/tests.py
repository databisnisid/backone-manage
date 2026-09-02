from django.test import TestCase

from accounts.models import User
from licenses.models import Licenses
from licenses.utils import check_license, is_license_valid


class ModuleCheckLicenseGuardTests(TestCase):
    """V8 / V6: module-level licenses.utils.check_license must never raise on
    malformed input — returns {'status','msg'} dict."""

    def test_missing_keys_returns_invalid(self):
        lic_json = {"node_id": "abc"}  # missing uuid/token/etc
        result = check_license(lic_json)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], 0)

    def test_non_dict_input_returns_invalid(self):
        result = check_license(None)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], 0)

    def test_bad_base64_token_returns_invalid(self):
        lic_json = {
            "node_id": "abc",
            "uuid": "u",
            "token": "!!not-base64!!",
            "license_code": "code",
            "is_block_rule": False,
            "features": {},
        }
        result = check_license(lic_json)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], 0)

    def test_valid_shape_does_not_raise(self):
        # Valid b64 token + all keys present: must not raise (may be invalid
        # because no matching controller, but must not blow up).
        import base64

        lic_json = {
            "node_id": "abc",
            "uuid": "u",
            "token": base64.b64encode(b"tok").decode(),
            "license_code": "code",
            "is_block_rule": False,
            "features": {},
        }
        result = check_license(lic_json)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)


class ModelCheckLicenseTests(TestCase):
    """V8: model method Licenses.check_license() returns (bool, valid_until, msg) tuple."""

    def test_empty_license_string_returns_tuple(self):
        lic = Licenses(license_string="")
        status, valid_until, msg = lic.check_license()
        self.assertIs(status, False)
        self.assertIsNone(valid_until)
        self.assertIn("EC1100", msg)

    def test_bad_b64_license_string_does_not_raise(self):
        lic = Licenses(license_string="!!!not-base64!!!")
        status, valid_until, msg = lic.check_license()
        self.assertIs(status, False)
        self.assertIn("EC1105", msg)


class IsLicenseValidTests(TestCase):
    """V6: is_license_valid returns bool, never raises."""

    def test_no_org_user_is_false(self):
        user = User.objects.create_user(username="u", password="x")
        self.assertIs(is_license_valid(user), False)
