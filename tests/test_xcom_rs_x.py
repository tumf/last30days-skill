"""Tests for the xcom-rs X search adapter."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib import xcom_rs_x


class TestXcomRsPrerequisites(unittest.TestCase):
    """Prerequisite detection with mocked shutil.which / os.path.isfile."""

    @mock.patch("lib.xcom_rs_x.shutil.which", side_effect=lambda cmd: "/usr/bin/" + cmd if cmd in ("xcom-rs", "dotenvx") else None)
    @mock.patch("lib.xcom_rs_x.os.path.isfile", return_value=True)
    def test_is_available_when_all_present(self, _isfile, _which):
        self.assertTrue(xcom_rs_x.is_available())

    @mock.patch("lib.xcom_rs_x.shutil.which", return_value=None)
    @mock.patch("lib.xcom_rs_x.os.path.isfile", return_value=True)
    def test_not_available_without_cli(self, _isfile, _which):
        self.assertFalse(xcom_rs_x.is_available())

    @mock.patch("lib.xcom_rs_x.shutil.which", side_effect=lambda cmd: "/usr/bin/" + cmd)
    @mock.patch("lib.xcom_rs_x.os.path.isfile", return_value=False)
    def test_not_available_without_auth(self, _isfile, _which):
        self.assertFalse(xcom_rs_x.is_available())

    @mock.patch("lib.xcom_rs_x.shutil.which", return_value=None)
    @mock.patch("lib.xcom_rs_x.os.path.isfile", return_value=False)
    def test_get_status_all_missing(self, _isfile, _which):
        status = xcom_rs_x.get_status()
        self.assertFalse(status["available"])
        self.assertEqual(3, len(status["missing"]))

    @mock.patch("lib.xcom_rs_x.shutil.which", side_effect=lambda cmd: "/usr/bin/" + cmd)
    @mock.patch("lib.xcom_rs_x.os.path.isfile", return_value=True)
    def test_get_status_all_ok(self, _isfile, _which):
        status = xcom_rs_x.get_status()
        self.assertTrue(status["available"])
        self.assertEqual(0, len(status["missing"]))


class TestParseResponse(unittest.TestCase):
    """JSON parsing and normalization for xcom-rs output."""

    def test_parse_list_response(self):
        tweets = [
            {
                "id": "100",
                "text": "Hello world test tweet",
                "permanent_url": "https://x.com/user/status/100",
                "author": {"username": "testuser"},
                "createdAt": "2026-03-15T10:30:00Z",
                "likeCount": 42,
                "retweetCount": 5,
                "replyCount": 3,
                "quoteCount": 1,
            }
        ]
        items = xcom_rs_x.parse_response(tweets, query="hello world")
        self.assertEqual(1, len(items))
        self.assertEqual("X1", items[0]["id"])
        self.assertEqual("https://x.com/user/status/100", items[0]["url"])
        self.assertEqual("testuser", items[0]["author_handle"])
        self.assertEqual("2026-03-15", items[0]["date"])
        self.assertEqual(42, items[0]["engagement"]["likes"])
        self.assertEqual(5, items[0]["engagement"]["reposts"])
        self.assertGreater(items[0]["relevance"], 0)

    def test_parse_dict_with_items_key(self):
        response = {
            "items": [
                {
                    "id": "200",
                    "text": "Another tweet",
                    "url": "https://x.com/u/status/200",
                    "author": {"username": "other"},
                    "likeCount": 10,
                }
            ]
        }
        items = xcom_rs_x.parse_response(response, query="tweet")
        self.assertEqual(1, len(items))
        self.assertEqual("other", items[0]["author_handle"])

    def test_parse_dict_with_data_key(self):
        response = {
            "data": [
                {
                    "id": "300",
                    "text": "Data key tweet",
                    "permanent_url": "https://x.com/u/status/300",
                    "author": {"username": "datauser"},
                }
            ]
        }
        items = xcom_rs_x.parse_response(response, query="data")
        self.assertEqual(1, len(items))

    def test_parse_empty_response(self):
        self.assertEqual([], xcom_rs_x.parse_response({"items": []}, query="q"))

    def test_parse_error_response(self):
        self.assertEqual([], xcom_rs_x.parse_response({"error": "something broke", "items": []}, query="q"))

    def test_url_construction_from_id(self):
        tweets = [
            {
                "id": "999",
                "text": "No URL provided",
                "author": {"username": "bob"},
            }
        ]
        items = xcom_rs_x.parse_response(tweets, query="test")
        self.assertEqual(1, len(items))
        self.assertEqual("https://x.com/bob/status/999", items[0]["url"])

    def test_twitter_date_format(self):
        tweets = [
            {
                "id": "400",
                "text": "Old format date",
                "permanent_url": "https://x.com/u/status/400",
                "created_at": "Wed Mar 15 10:30:00 +0000 2026",
                "author": {"username": "user"},
            }
        ]
        items = xcom_rs_x.parse_response(tweets, query="test")
        self.assertEqual("2026-03-15", items[0]["date"])

    def test_zero_engagement_preserved(self):
        tweets = [
            {
                "id": "500",
                "text": "Zero likes tweet",
                "permanent_url": "https://x.com/u/status/500",
                "likeCount": 0,
                "retweetCount": 0,
            }
        ]
        items = xcom_rs_x.parse_response(tweets, query="test")
        self.assertEqual(0, items[0]["engagement"]["likes"])
        self.assertEqual(0, items[0]["engagement"]["reposts"])

    def test_text_truncation(self):
        tweets = [
            {
                "id": "600",
                "text": "A" * 1000,
                "permanent_url": "https://x.com/u/status/600",
            }
        ]
        items = xcom_rs_x.parse_response(tweets, query="test")
        self.assertLessEqual(len(items[0]["text"]), 500)


class TestSearchX(unittest.TestCase):
    """search_x with mocked subprocess execution."""

    @mock.patch("lib.xcom_rs_x._run_xcom_rs")
    def test_search_returns_raw_response(self, mock_run):
        mock_run.return_value = {
            "items": [
                {
                    "id": "1",
                    "text": "match",
                    "permanent_url": "https://x.com/u/status/1",
                    "likeCount": 5,
                }
            ]
        }
        result = xcom_rs_x.search_x("test topic", "2026-03-01", "2026-03-30", depth="quick")
        self.assertIn("items", result)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn("since:2026-03-01", call_args[0][0])
        self.assertIn("until:2026-03-30", call_args[0][0])

    @mock.patch("lib.xcom_rs_x._run_xcom_rs")
    def test_search_retries_on_empty(self, mock_run):
        # First call returns empty, second returns results
        mock_run.side_effect = [
            {"items": []},  # primary
            {"items": [{"id": "1", "text": "retry match", "permanent_url": "https://x.com/u/status/1"}]},  # OR group
        ]
        result = xcom_rs_x.search_x("multi word query topic", "2026-03-01", "2026-03-30")
        self.assertGreaterEqual(mock_run.call_count, 2)


class TestSearchHandles(unittest.TestCase):
    """search_handles with mocked subprocess."""

    @mock.patch("lib.xcom_rs_x._run_xcom_rs")
    def test_search_handles_constructs_from_query(self, mock_run):
        mock_run.return_value = {
            "items": [
                {
                    "id": "1",
                    "text": "handle tweet",
                    "permanent_url": "https://x.com/alice/status/1",
                    "author": {"username": "alice"},
                }
            ]
        }
        items = xcom_rs_x.search_handles(["alice", "@bob"], "test topic", "2026-03-01", count_per=3)
        self.assertEqual(2, mock_run.call_count)
        # Check that from: prefix was used
        first_call_query = mock_run.call_args_list[0][0][0]
        self.assertTrue(
            any("from:" in call[0][0] for call in mock_run.call_args_list)
        )


class TestRunXcomRs(unittest.TestCase):
    """Low-level _run_xcom_rs with mocked subprocess.Popen."""

    @mock.patch("lib.xcom_rs_x.subprocess.Popen")
    def test_successful_json_response(self, mock_popen):
        proc = mock.MagicMock()
        proc.communicate.return_value = (json.dumps({"items": [{"id": "1"}]}), "")
        proc.returncode = 0
        mock_popen.return_value = proc

        result = xcom_rs_x._run_xcom_rs("test query", 10, 30)
        self.assertEqual([{"id": "1"}], result["items"])

    @mock.patch("lib.xcom_rs_x.subprocess.Popen")
    def test_nonzero_exit(self, mock_popen):
        proc = mock.MagicMock()
        proc.communicate.return_value = ("", "auth failed")
        proc.returncode = 1
        mock_popen.return_value = proc

        result = xcom_rs_x._run_xcom_rs("test", 10, 30)
        self.assertIn("error", result)
        self.assertEqual([], result["items"])

    @mock.patch("lib.xcom_rs_x.subprocess.Popen")
    def test_timeout_handling(self, mock_popen):
        import subprocess as sp
        proc = mock.MagicMock()
        proc.communicate.side_effect = sp.TimeoutExpired(cmd="xcom-rs", timeout=30)
        proc.pid = 12345
        mock_popen.return_value = proc

        with mock.patch("os.killpg"):
            result = xcom_rs_x._run_xcom_rs("test", 10, 30)
        self.assertIn("timed out", result["error"])

    @mock.patch("lib.xcom_rs_x.subprocess.Popen")
    def test_empty_stdout(self, mock_popen):
        proc = mock.MagicMock()
        proc.communicate.return_value = ("", "")
        proc.returncode = 0
        mock_popen.return_value = proc

        result = xcom_rs_x._run_xcom_rs("test", 10, 30)
        self.assertEqual([], result["items"])


if __name__ == "__main__":
    unittest.main()
