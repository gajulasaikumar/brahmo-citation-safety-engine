"""
Hallucination Detector — 4 deterministic pre-filter rules.

Runs BEFORE Indian Kanoon API calls. Catches obviously impossible
citations instantly (free, no API cost). Rules:
1. Future year (year > 2026)
2. Impossible SCC volume (> 25)
3. Impossible page number (> 5000)
4. Pre-1900 date (law reports didn't exist)
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class HallucinationResult:
    """Result of hallucination detection for a single citation."""
    citation: str
    is_hallucinated: bool
    is_suspicious: bool
    rule: Optional[str] = None
    reason: Optional[str] = None
    confidence: str = "high"  # high, medium, low

    def to_dict(self) -> dict:
        return {
            "citation": self.citation,
            "is_hallucinated": self.is_hallucinated,
            "is_suspicious": self.is_suspicious,
            "rule": self.rule,
            "reason": self.reason,
            "confidence": self.confidence,
        }


class HallucinationDetector:
    """
    Pre-filter for obviously impossible citations.

    This catches citations that CANNOT exist based on structural rules,
    saving Indian Kanoon API calls and providing instant feedback.
    """

    def __init__(self, current_year: int = 2026):
        self.current_year = current_year

    def check(self, citation_text: str, pattern_name: str,
              groups: Dict[str, str]) -> HallucinationResult:
        """
        Check a single citation against all 4 hallucination rules.

        Args:
            citation_text: The raw citation string (e.g. "(2028) 3 SCC 45")
            pattern_name: The pattern that matched (e.g. "SCC", "AIR")
            groups: Named/numbered capture groups from regex match

        Returns:
            HallucinationResult with is_hallucinated/is_suspicious flags
        """
        # Extract year from citation
        year = self._extract_year(citation_text, groups)

        # Rule 1: Future year
        if year and year > self.current_year:
            return HallucinationResult(
                citation=citation_text,
                is_hallucinated=True,
                is_suspicious=True,
                rule="future_year",
                reason=f"Year {year} is in the future (> {self.current_year}). Citation cannot exist.",
                confidence="high",
            )

        # Rule 4: Pre-1900 date
        if year and year < 1900:
            return HallucinationResult(
                citation=citation_text,
                is_hallucinated=True,
                is_suspicious=True,
                rule="pre_1900",
                reason=f"Year {year} is before 1900. Indian law reports did not exist.",
                confidence="high",
            )

        # Pattern-specific checks
        if pattern_name == "SCC":
            return self._check_scc(citation_text, groups, year)
        elif pattern_name == "AIR":
            return self._check_air(citation_text, groups, year)
        elif pattern_name == "SCR":
            return self._check_scr(citation_text, groups, year)

        # Other patterns (SCC OnLine, Cri LJ, MANU) — no volume checks
        return HallucinationResult(
            citation=citation_text,
            is_hallucinated=False,
            is_suspicious=False,
        )

    def _check_scc(self, citation_text: str, groups: Dict[str, str],
                   year: Optional[int]) -> HallucinationResult:
        """Check SCC-specific hallucination rules."""
        volume = self._extract_group(groups, "2")  # volume is group 2 in SCC regex
        page = self._extract_group(groups, "3")     # page is group 3

        if volume:
            vol = int(volume)
            # Rule 2: Impossible volume
            if vol > 25:
                return HallucinationResult(
                    citation=citation_text,
                    is_hallucinated=True,
                    is_suspicious=True,
                    rule="impossible_volume",
                    reason=f"SCC volume {vol} is impossible. SCC rarely exceeds 20 volumes per year.",
                    confidence="high",
                )

        if page:
            pg = int(page)
            # Rule 3: Impossible page number
            if pg > 5000:
                return HallucinationResult(
                    citation=citation_text,
                    is_hallucinated=False,
                    is_suspicious=True,
                    rule="impossible_page",
                    reason=f"SCC page {pg} is suspicious. SCC page numbers rarely exceed 2000.",
                    confidence="medium",
                )

        return HallucinationResult(
            citation=citation_text,
            is_hallucinated=False,
            is_suspicious=False,
        )

    def _check_air(self, citation_text: str, groups: Dict[str, str],
                   year: Optional[int]) -> HallucinationResult:
        """Check AIR-specific rules."""
        page = self._extract_group(groups, "3")
        if page:
            pg = int(page)
            if pg > 5000:
                return HallucinationResult(
                    citation=citation_text,
                    is_hallucinated=False,
                    is_suspicious=True,
                    rule="impossible_page",
                    reason=f"AIR page {pg} is suspiciously high.",
                    confidence="medium",
                )
        return HallucinationResult(
            citation=citation_text,
            is_hallucinated=False,
            is_suspicious=False,
        )

    def _check_scr(self, citation_text: str, groups: Dict[str, str],
                   year: Optional[int]) -> HallucinationResult:
        """Check SCR-specific rules."""
        volume = self._extract_group(groups, "2")
        if volume:
            vol = int(volume)
            if vol > 25:
                return HallucinationResult(
                    citation=citation_text,
                    is_hallucinated=True,
                    is_suspicious=True,
                    rule="impossible_volume",
                    reason=f"SCR volume {vol} is impossible.",
                    confidence="high",
                )
        return HallucinationResult(
            citation=citation_text,
            is_hallucinated=False,
            is_suspicious=False,
        )

    def _extract_year(self, text: str, groups: Dict[str, str]) -> Optional[int]:
        """Extract year from citation text or groups."""
        # Try groups first
        for key in ["1", "year"]:
            val = self._extract_group(groups, key)
            if val and len(val) == 4 and val.isdigit():
                return int(val)
        # Fallback: find 4-digit year in text
        match = re.search(r"\b(19|20)\d{2}\b", text)
        if match:
            return int(match.group(0))
        return None

    @staticmethod
    def _extract_group(groups: Dict[str, str], key: str) -> Optional[str]:
        """Safely extract a group value."""
        return groups.get(key)