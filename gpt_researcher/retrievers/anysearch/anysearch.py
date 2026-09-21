"""AnySearch API search retriever for GPT Researcher.

This module provides the AnySearch class for performing web searches using
the AnySearch API (https://anysearch.com).

The API allows anonymous access with lower rate limits; set
``ANYSEARCH_API_KEY`` for higher limits. ``ANYSEARCH_API_BASE_URL`` can
override the default endpoint (https://api.anysearch.com).
"""

import logging
import os

import requests


class AnySearch:
    """
    AnySearch API Retriever
    """

    # The API returns links plus a snippet, so results still need scraping.
    requires_scraping = True

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        """
        Initializes the AnySearch object.

        Args:
            query: The search query string.
            headers: Optional headers (unused; kept for constructor parity
                with the other retrievers).
            topic: Unused by this API; kept for constructor parity.
            query_domains: Domain restrictions are not supported by the
                API, so this is ignored (like the BoCha retriever).
        """
        self.query = query
        self.api_key = os.environ.get("ANYSEARCH_API_KEY", "")
        self.base_url = os.environ.get(
            "ANYSEARCH_API_BASE_URL", "https://api.anysearch.com"
        ).rstrip("/")

    def search(self, max_results=10) -> list[dict]:
        """
        Searches the query and returns results normalized to the
        ``title``/``href``/``body`` contract used by the other retrievers.

        Returns:
            A list of search result dicts; empty on any request, payload,
            or API-level error (the research run continues without sources).
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "query": self.query,
            # The API accepts 1-10 results per request.
            "max_results": max(1, min(max_results, 10)),
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/search",
                headers=headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            envelope = response.json()
        except (requests.RequestException, ValueError) as e:
            logging.getLogger(__name__).warning(
                f"Error: {e}. Failed fetching sources. Resulting in empty response."
            )
            return []

        # The API signals errors with a non-zero `code` even on HTTP 200.
        if not isinstance(envelope, dict) or envelope.get("code", 0) != 0:
            logging.getLogger(__name__).warning(
                f"AnySearch API error: {envelope.get('message', 'unknown') if isinstance(envelope, dict) else 'invalid response'}. "
                "Returning empty results."
            )
            return []

        results = ((envelope.get("data") or {}).get("results")) or []
        if not isinstance(results, list):
            return []

        search_results = []
        # Normalize to the shared contract; skip non-dict rows / empty URLs.
        for result in results:
            if not isinstance(result, dict):
                continue
            href = result.get("url") or ""
            if not href:
                continue
            search_results.append(
                {
                    "title": result.get("title") or "",
                    "href": href,
                    "body": result.get("snippet") or result.get("content") or "",
                }
            )

        return search_results
