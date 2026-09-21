"""AnySearch must skip non-dict / href-less hits and tolerate API errors."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.anysearch.anysearch import AnySearch


def _search(payload):
    r = AnySearch("q")
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    with patch(
        "gpt_researcher.retrievers.anysearch.anysearch.requests.post",
        return_value=resp,
    ):
        return r.search(max_results=5)


def test_anysearch_normalizes_results():
    out = _search(
        {
            "code": 0,
            "data": {
                "results": [
                    {
                        "title": "Good",
                        "url": "https://ok.example",
                        "snippet": "s",
                        "content": "longer content",
                    }
                ]
            },
        }
    )
    assert out == [{"title": "Good", "href": "https://ok.example", "body": "s"}]


def test_anysearch_skips_non_dict_and_missing_url():
    out = _search(
        {
            "code": 0,
            "data": {"results": [{"title": "Good", "url": "https://ok.example"}, "x", {"title": "NoURL"}]},
        }
    )
    assert out == [{"title": "Good", "href": "https://ok.example", "body": ""}]


def test_anysearch_non_zero_code_returns_empty():
    assert _search({"code": 1001, "message": "rate limited"}) == []


def test_anysearch_non_list_results_returns_empty():
    assert _search({"code": 0, "data": {"results": {"not": "list"}}}) == []


def test_anysearch_request_error_returns_empty():
    import requests

    r = AnySearch("q")
    with patch(
        "gpt_researcher.retrievers.anysearch.anysearch.requests.post",
        side_effect=requests.RequestException("boom"),
    ):
        assert r.search(max_results=5) == []
