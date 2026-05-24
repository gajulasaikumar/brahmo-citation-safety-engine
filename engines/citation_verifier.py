"""
Citation Verifier — Indian Kanoon API lookup with parallel verification + caching.

Verifies extracted citations against Indian Kanoon's database.
Results are cached in MySQL to avoid redundant API calls.
Parallel verification via concurrent.futures for speed.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from engines.citation_extractor import ExtractedCitation
from engines.hallucination_detector import HallucinationResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of verifying a single citation."""
    citation: str
    normalized: str
    status: str  # VERIFIED, NOT_FOUND, UNVERIFIED, HALLUCINATED
    source: str  # ik_api, cache, pre_filter
    case_name: Optional[str] = None
    ik_doc_id: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    reason: Optional[str] = None
    cost: float = 0.0  # INR
    corrected_citation: Optional[str] = None  # If format was corrected

    def to_dict(self) -> dict:
        return {
            "citation": self.citation,
            "normalized": self.normalized,
            "status": self.status,
            "source": self.source,
            "case_name": self.case_name,
            "ik_doc_id": self.ik_doc_id,
            "court": self.court,
            "date": self.date,
            "reason": self.reason,
            "cost": self.cost,
            "corrected_citation": self.corrected_citation,
        }


class CitationVerifier:
    """
    Verifies citations against Indian Kanoon API with MySQL-backed caching.

    Flow:
    1. Check cache first (free, instant)
    2. If not cached, call IK search API
    3. If found, call IK docmeta API for confirmation
    4. Cache the result with 7-day TTL
    5. Return VerificationResult with status
    """

    # IK API costs (approximate, in INR)
    SEARCH_COST = 0.5
    DOCMETA_COST = 0.3

    def __init__(self, ik_client, db, cache_ttl_days: int = 7):
        """
        Args:
            ik_client: Indian Kanoon API client instance
            db: SQLAlchemy db instance
            cache_ttl_days: Days before cached results expire
        """
        self.ik_client = ik_client
        self.db = db
        self.cache_ttl_days = cache_ttl_days

    def verify_citation(self, citation: ExtractedCitation,
                        hallucination: HallucinationResult) -> VerificationResult:
        """
        Verify a single citation.

        Args:
            citation: Extracted citation from the text
            hallucination: Pre-filter result from hallucination detector

        Returns:
            VerificationResult with status and metadata
        """
        # If hallucination detector already caught it, skip API call
        if hallucination.is_hallucinated:
            return VerificationResult(
                citation=citation.text,
                normalized=citation.normalized,
                status="HALLUCINATED",
                source="pre_filter",
                reason=hallucination.reason,
            )

        # Check cache first
        cached = self._check_cache(citation.normalized)
        if cached:
            return cached

        # Call Indian Kanoon API
        try:
            result = self.ik_client.search(citation.normalized)
            cost = self.SEARCH_COST

            if result and result.get("found", 0) > 0:
                # Found — get docmeta for confirmation
                doc = result["docs"][0]
                docid = doc.get("docid")

                # Get metadata
                meta = self.ik_client.docmeta(docid) if docid else None
                cost += self.DOCMETA_COST if meta else 0

                case_name = doc.get("title", "")
                if meta:
                    case_name = meta.get("title", case_name)

                # Check if format correction is needed
                corrected = None
                ik_citation = meta.get("citation", "") if meta else ""
                if ik_citation and ik_citation != citation.text:
                    # Citation format differs — possible correction
                    corrected = ik_citation

                status = "VERIFIED"
                if corrected and self._is_minor_correction(citation.text, corrected):
                    status = "CORRECTED"

                ver_result = VerificationResult(
                    citation=citation.text,
                    normalized=citation.normalized,
                    status=status,
                    source="ik_api",
                    case_name=case_name,
                    ik_doc_id=str(docid) if docid else None,
                    court=meta.get("court") if meta else None,
                    date=meta.get("date") if meta else None,
                    cost=cost,
                    corrected_citation=corrected,
                )

                # Cache the result
                self._cache_result(ver_result)
                return ver_result
            else:
                # Not found in IK
                if hallucination.is_suspicious:
                    status = "HALLUCINATED"
                    reason = hallucination.reason or "Flagged by pre-filter + not found in Indian Kanoon"
                else:
                    status = "UNVERIFIED"
                    reason = "Not found in Indian Kanoon. May be a real but obscure case not yet indexed."

                ver_result = VerificationResult(
                    citation=citation.text,
                    normalized=citation.normalized,
                    status=status,
                    source="ik_api",
                    reason=reason,
                    cost=cost,
                )
                self._cache_result(ver_result)
                return ver_result

        except Exception as e:
            logger.error(f"IK API error for {citation.text}: {e}")
            return VerificationResult(
                citation=citation.text,
                normalized=citation.normalized,
                status="UNVERIFIED",
                source="ik_api_error",
                reason=f"Indian Kanoon API error: {str(e)}",
            )

    def verify_batch(self, citations: List[ExtractedCitation],
                     hallucinations: List[HallucinationResult],
                     max_workers: int = 5) -> List[VerificationResult]:
        """
        Verify multiple citations in parallel.

        Args:
            citations: List of extracted citations
            hallucinations: Corresponding pre-filter results
            max_workers: Max concurrent API calls

        Returns:
            List of VerificationResults (same order as input)
        """
        results = [None] * len(citations)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {}
            for i, (cit, hal) in enumerate(zip(citations, hallucinations)):
                # Pre-filtered hallucinations don't need API calls — handle immediately
                if hal.is_hallucinated:
                    results[i] = self.verify_citation(cit, hal)
                else:
                    future = executor.submit(self.verify_citation, cit, hal)
                    future_to_idx[future] = i

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logger.error(f"Verification error for index {idx}: {e}")
                    results[idx] = VerificationResult(
                        citation=citations[idx].text,
                        normalized=citations[idx].normalized,
                        status="UNVERIFIED",
                        source="error",
                        reason=f"Verification failed: {str(e)}",
                    )

        # Fill any remaining None with UNVERIFIED
        for i in range(len(results)):
            if results[i] is None:
                results[i] = VerificationResult(
                    citation=citations[i].text,
                    normalized=citations[i].normalized,
                    status="UNVERIFIED",
                    source="error",
                    reason="Verification did not complete",
                )

        return results

    def _check_cache(self, normalized: str) -> Optional[VerificationResult]:
        """Check MySQL cache for a previously verified citation."""
        try:
            from models import VerificationCache
            cached = VerificationCache.query.filter_by(
                citation_text=normalized
            ).first()

            if cached:
                # Check if cache has expired
                if cached.expires_at and cached.expires_at < datetime.utcnow():
                    # Expired — will re-verify
                    return None

                return VerificationResult(
                    citation=normalized,
                    normalized=normalized,
                    status=cached.status,
                    source="cache",
                    case_name=cached.case_name,
                    ik_doc_id=cached.ik_doc_id,
                    cost=0.0,  # Cache hit is free
                )
        except Exception:
            # If DB query fails (e.g. during testing), just skip cache
            pass
        return None

    def _cache_result(self, result: VerificationResult):
        """Cache a verification result in MySQL."""
        try:
            from models import VerificationCache
            existing = VerificationCache.query.filter_by(
                citation_text=result.normalized
            ).first()

            if existing:
                existing.status = result.status
                existing.ik_doc_id = result.ik_doc_id
                existing.case_name = result.case_name
                existing.verified_at = datetime.utcnow()
                existing.expires_at = datetime.utcnow() + timedelta(days=self.cache_ttl_days)
            else:
                entry = VerificationCache(
                    citation_text=result.normalized,
                    status=result.status,
                    ik_doc_id=result.ik_doc_id,
                    case_name=result.case_name,
                    verified_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=self.cache_ttl_days),
                )
                self.db.session.add(entry)

            self.db.session.commit()
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
            try:
                self.db.session.rollback()
            except Exception:
                pass

    @staticmethod
    def _is_minor_correction(original: str, corrected: str) -> bool:
        """Check if the difference is a minor format correction (spacing, capitalization)."""
        # Normalize both for comparison
        import re
        orig_norm = re.sub(r"\s+", " ", original.strip().lower())
        corr_norm = re.sub(r"\s+", " ", corrected.strip().lower())
        # If they're very similar, it's a minor correction
        if orig_norm == corr_norm:
            return True
        # Check if one is a substring or differs by just a digit or two
        # (e.g., page number correction: SCC 12 → SCC 1)
        return False  # Default: not minor if text differs