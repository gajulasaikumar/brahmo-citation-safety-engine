"""
Indian Kanoon API Client — Citation verification against India's largest
case law database.

API Documentation:
- Base URL: https://api.indiankanoon.org
- Auth: Token in Authorization header
- Search: POST /search/ with {"formInput": "citation text"}
- DocMeta: GET /docmeta/{docid}/ (cheapest verification)
- Doc: GET /doc/{docid}/ (full text — expensive, use sparingly)
"""

import logging
import requests
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class IndianKanoonClient:
    """Client for the Indian Kanoon API."""

    def __init__(self, api_key: str, base_url: str = "https://api.indiankanoon.org"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(self, query: str, max_retries: int = 1) -> Optional[Dict]:
        """
        Search Indian Kanoon for cases matching a citation.

        Args:
            query: Citation text to search (e.g. "(2021) 10 SCC 1")
            max_retries: Number of retries on failure

        Returns:
            Dict with 'docs', 'found' keys, or None on error
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/search/",
                    json={"formInput": query},
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()
                return data

            except requests.RequestException as e:
                logger.warning(f"IK search attempt {attempt + 1} failed for '{query}': {e}")
                if attempt == max_retries:
                    logger.error(f"IK search failed after {max_retries + 1} attempts: {e}")
                    return None

        return None

    def docmeta(self, docid: int) -> Optional[Dict]:
        """
        Get document metadata (cheapest API call for verification).

        Args:
            docid: Indian Kanoon document ID

        Returns:
            Dict with 'title', 'citation', 'court', 'date', etc.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/docmeta/{docid}/",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"IK docmeta error for docid {docid}: {e}")
            return None

    def doc(self, docid: int) -> Optional[Dict]:
        """
        Get full document text (EXPENSIVE — use sparingly).

        Args:
            docid: Indian Kanoon document ID

        Returns:
            Dict with 'doc' key containing full text
        """
        try:
            response = self.session.get(
                f"{self.base_url}/doc/{docid}/",
                timeout=20,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"IK doc error for docid {docid}: {e}")
            return None

    def search_and_verify(self, citation: str) -> Dict:
        """
        Convenience: search + verify in one call.
        Returns verification result dict with 'found', 'docid', 'title'.

        Args:
            citation: Citation string to verify

        Returns:
            Dict with verification details
        """
        search_result = self.search(citation)

        if not search_result:
            return {
                "found": False,
                "error": "Search failed",
                "citation": citation,
            }

        if search_result.get("found", 0) > 0:
            doc = search_result["docs"][0]
            docid = doc.get("docid")

            # Get metadata for confirmation
            meta = self.docmeta(docid) if docid else None

            return {
                "found": True,
                "docid": docid,
                "title": doc.get("title", ""),
                "headline": doc.get("headline", ""),
                "citation": meta.get("citation", "") if meta else citation,
                "court": meta.get("court", "") if meta else "",
                "date": meta.get("date", "") if meta else "",
            }

        return {
            "found": False,
            "citation": citation,
        }

    def health_check(self) -> bool:
        """Check if the IK API is reachable."""
        try:
            response = self.session.post(
                f"{self.base_url}/search/",
                json={"formInput": "test"},
                timeout=10,
            )
            return response.status_code in (200, 400, 403)
        except requests.RequestException:
            return False