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
        # Always simplify the search query first — IK doesn't accept raw citations
        simplified = self._simplify_search(query)
        search_query = simplified if simplified else query

        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/search/",
                    data={"formInput": search_query},
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()

                # Check for API errors
                if "errmsg" in data:
                    logger.warning(f"IK search error: {data['errmsg']} for query '{search_query}'")
                    return data

                return data

            except requests.RequestException as e:
                logger.warning(f"IK search attempt {attempt + 1} failed for '{search_query}': {e}")
                if attempt == max_retries:
                    logger.error(f"IK search failed after {max_retries + 1} attempts: {e}")
                    return None

        return None

    @staticmethod
    def _simplify_search(citation: str) -> str:
        """
        Convert a citation format to IK-friendly search terms.
        "(2021) 10 SCC 1" → "10 SCC 1 doctypes:supremecourt"
        "AIR 2024 SC 123" → "SC 123 doctypes:supremecourt"
        "MANU/SC/0123/2024" → "MANU SC 2024 doctypes:supremecourt"
        
        IK API notes:
        - form-encoded, NOT JSON
        - doctypes: filter works (supremecourt, delhi, etc.)
        - year: filter causes 400 errors — DO NOT USE
        - Parentheses cause 400 errors — strip them
        """
        import re
        c = citation.strip()

        # Determine court from citation
        court_filter = ""
        # SCC, SCR are Supreme Court reporters
        if " SCC " in c or " SCR " in c or " SC " in c or c.startswith("AIR") or "MANU/SC/" in c:
            court_filter = "doctypes:supremecourt"
        elif " Del " in c or " Delhi " in c or "MANU/DE/" in c:
            court_filter = "doctypes:delhi"
        elif " Bom " in c or " Bombay " in c or "MANU/MH/" in c:
            court_filter = "doctypes:bombay"
        elif " Cal " in c or " Calcutta " in c:
            court_filter = "doctypes:calcutta"
        elif " Mad " in c or " Madras " in c:
            court_filter = "doctypes:madras"
        elif " Kar " in c or " Karnataka " in c or "MANU/KA/" in c:
            court_filter = "doctypes:karnataka"
        elif " Ker " in c or " Kerala " in c or "MANU/KE/" in c:
            court_filter = "doctypes:kerala"

        # Build search query — strip parens, clean special chars
        search = c.replace("(", " ").replace(")", " ")
        search = search.replace("AIR", "").strip()
        search = search.replace("SCC OnLine", "SCC").replace("SCC Online", "SCC")
        search = search.replace("/", " ")
        search = re.sub(r"[^\w\s]", " ", search)
        search = re.sub(r"\s+", " ", search).strip()

        # Add court filter for precision
        if court_filter:
            search += f" {court_filter}"

        return search if search else None

    def docmeta(self, docid: int) -> Optional[Dict]:
        """
        Get document metadata (cheapest API call for verification).

        Args:
            docid: Indian Kanoon document ID

        Returns:
            Dict with 'title', 'citation', 'court', 'date', etc.
        """
        try:
            response = self.session.post(
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
            response = self.session.post(
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
                data={"formInput": "test"},
                timeout=10,
            )
            return response.status_code in (200, 400, 403)
        except requests.RequestException:
            return False