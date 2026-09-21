"""AnySearchExtract must tolerate malformed extract API payloads.

The scraper converts request errors, non-dict envelopes, non-zero API
``code`` values, and empty ``content`` into the empty
``("", [], "")`` triple instead of raising, so one bad page cannot
crash a scrape batch (mirrors the TavilyExtract/BoCha malformed tests).
"""
from unittest.mock import MagicMock, patch

from gpt_researcher.scraper.anysearch_extract.anysearch_extract import (
    AnySearchExtract,
)


def _extract(payload):
    scraper = AnySearchExtract("https://example.com")
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    with patch(
        "gpt_researcher.scraper.anysearch_extract.anysearch_extract.requests.post",
        return_value=resp,
    ):
        return scraper.scrape()


def test_extract_success_returns_content_and_title():
    content, images, title = _extract(
        {"code": 0, "data": {"url": "https://example.com", "title": "T", "content": "C" * 200}}
    )
    assert content == "C" * 200
    assert title == "T"
    assert images == []


def test_extract_non_zero_code_returns_empty():
    assert _extract({"code": -1, "message": "daily_free_quota_exhausted"}) == ("", [], "")


def test_extract_non_dict_data_returns_empty():
    assert _extract({"code": 0, "data": "oops"}) == ("", [], "")


def test_extract_missing_content_returns_empty():
    assert _extract({"code": 0, "data": {"title": "T"}}) == ("", [], "")


def test_extract_http_error_returns_empty():
    import requests

    scraper = AnySearchExtract("https://example.com")
    with patch(
        "gpt_researcher.scraper.anysearch_extract.anysearch_extract.requests.post",
        side_effect=requests.RequestException("402"),
    ):
        assert scraper.scrape() == ("", [], "")
