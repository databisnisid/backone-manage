from django.test import TestCase

from licenses.utils import check_license


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
