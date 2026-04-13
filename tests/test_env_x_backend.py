"""Tests for X backend resolution with xcom_rs support."""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib import bird_x, env


class TestXBackendResolution(unittest.TestCase):
    """X backend resolution including xcom_rs precedence."""

    def setUp(self):
        self._saved_credentials = dict(bird_x._credentials)

    def tearDown(self):
        bird_x._credentials.clear()
        bird_x._credentials.update(self._saved_credentials)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    def test_xcom_rs_explicit_preferred(self, _):
        source = env.get_x_source({"LAST30DAYS_X_BACKEND": "xcom_rs"})
        self.assertEqual("xcom_rs", source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=False)
    def test_xcom_rs_explicit_but_unavailable(self, _):
        source = env.get_x_source({"LAST30DAYS_X_BACKEND": "xcom_rs"})
        self.assertIsNone(source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    def test_xcom_rs_auto_preferred_over_xai(self, _):
        source = env.get_x_source({"XAI_API_KEY": "test"})
        self.assertEqual("xcom_rs", source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    @mock.patch("lib.bird_x.is_bird_installed", return_value=True)
    def test_xcom_rs_auto_preferred_over_bird(self, _bird, _xcom):
        source = env.get_x_source({"AUTH_TOKEN": "a", "CT0": "b"})
        self.assertEqual("xcom_rs", source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=False)
    def test_xai_when_xcom_rs_unavailable(self, _):
        source = env.get_x_source({"XAI_API_KEY": "test"})
        self.assertEqual("xai", source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=False)
    @mock.patch("lib.bird_x.is_bird_installed", return_value=True)
    def test_bird_when_xcom_rs_and_xai_unavailable(self, _bird, _xcom):
        source = env.get_x_source({"AUTH_TOKEN": "a", "CT0": "b"})
        self.assertEqual("bird", source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=False)
    @mock.patch("lib.bird_x.is_bird_installed", return_value=False)
    def test_none_when_nothing_available(self, _bird, _xcom):
        source = env.get_x_source({})
        self.assertIsNone(source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    def test_explicit_xai_overrides_xcom_rs_auto(self, _):
        """Explicit LAST30DAYS_X_BACKEND=xai should use xai, not xcom_rs."""
        source = env.get_x_source({"LAST30DAYS_X_BACKEND": "xai", "XAI_API_KEY": "key"})
        self.assertEqual("xai", source)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    @mock.patch("lib.bird_x.is_bird_installed", return_value=True)
    def test_explicit_bird_overrides_xcom_rs_auto(self, _bird, _xcom):
        """Explicit LAST30DAYS_X_BACKEND=bird should use bird, not xcom_rs."""
        source = env.get_x_source({"LAST30DAYS_X_BACKEND": "bird", "AUTH_TOKEN": "a", "CT0": "b"})
        self.assertEqual("bird", source)


class TestXSourceStatus(unittest.TestCase):
    """get_x_source_status includes xcom_rs metadata."""

    def setUp(self):
        self._saved_credentials = dict(bird_x._credentials)

    def tearDown(self):
        bird_x._credentials.clear()
        bird_x._credentials.update(self._saved_credentials)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    @mock.patch("lib.xcom_rs_x.get_status", return_value={"available": True, "missing": []})
    @mock.patch("lib.bird_x.get_bird_status", return_value={"installed": False, "authenticated": False, "username": None, "can_install": True})
    def test_status_includes_xcom_rs(self, _bird, _xcom_status, _xcom_avail):
        status = env.get_x_source_status({})
        self.assertEqual("xcom_rs", status["source"])
        self.assertIn("xcom_rs_status", status)
        self.assertTrue(status["xcom_rs_status"]["available"])

    @mock.patch("lib.xcom_rs_x.is_available", return_value=False)
    @mock.patch("lib.xcom_rs_x.get_status", return_value={"available": False, "missing": ["xcom-rs not installed"]})
    @mock.patch("lib.bird_x.get_bird_status", return_value={"installed": False, "authenticated": False, "username": None, "can_install": True})
    def test_status_xcom_rs_missing(self, _bird, _xcom_status, _xcom_avail):
        status = env.get_x_source_status({})
        self.assertIsNone(status["source"])
        self.assertFalse(status["xcom_rs_status"]["available"])


class TestXSourceWithMethod(unittest.TestCase):
    """get_x_source_with_method includes xcom_rs."""

    @mock.patch("lib.xcom_rs_x.is_available", return_value=True)
    def test_xcom_rs_method(self, _):
        source, method = env.get_x_source_with_method({})
        self.assertEqual("xcom_rs", source)
        self.assertEqual("xcom_rs", method)

    @mock.patch("lib.xcom_rs_x.is_available", return_value=False)
    def test_fallback_to_xai(self, _):
        source, method = env.get_x_source_with_method({"XAI_API_KEY": "key"})
        self.assertEqual("xai", source)
        self.assertEqual("xai", method)


if __name__ == "__main__":
    unittest.main()
