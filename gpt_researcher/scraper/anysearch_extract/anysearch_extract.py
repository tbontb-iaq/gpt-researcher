import os

import requests


class AnySearchExtract:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        # Anonymous access works with lower rate limits; the key is optional.
        self.api_key = os.environ.get("ANYSEARCH_API_KEY", "")
        self.base_url = os.environ.get(
            "ANYSEARCH_API_BASE_URL", "https://api.anysearch.com"
        ).rstrip("/")

    def scrape(self) -> tuple:
        """
        This function extracts the content of a page via the AnySearch
        /v1/extract API, which returns the page as clean Markdown plus its
        title, so no local HTML parsing is needed.

        Returns:
          A tuple (content, image_urls, title). On any error or unusable
          payload an empty result is returned, matching the other scrapers.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                f"{self.base_url}/v1/extract",
                headers=headers,
                json={"url": self.link},
                timeout=30,
            )
            response.raise_for_status()
            envelope = response.json()
        except (requests.RequestException, ValueError) as e:
            print("Error! : " + str(e))
            return "", [], ""

        # The API signals errors with a non-zero `code` even on HTTP 200.
        if not isinstance(envelope, dict) or envelope.get("code", 0) != 0:
            print(
                "Error! : "
                + (envelope.get("message", "invalid response") if isinstance(envelope, dict) else "invalid response")
            )
            return "", [], ""

        data = envelope.get("data") or {}
        if not isinstance(data, dict):
            return "", [], ""

        content = data.get("content") or ""
        title = data.get("title") or ""
        if not content:
            return "", [], ""

        return content, [], title
