"""
Citation Extractor — 6 regex patterns for Indian legal citations.

Extracts citations from AI-generated legal text using database-driven
regex patterns. Zero false negatives is the primary goal — every citation
in the text must be found.
"""

import re
from typing import List, Dict, Optional


class ExtractedCitation:
    """Represents a single citation extracted from text."""

    def __init__(self, text: str, start: int, end: int,
                 pattern_name: str, groups: Dict[str, str]):
        self.text = text
        self.start = start
        self.end = end
        self.pattern_name = pattern_name
        self.groups = groups
        self.normalized = self._normalize()

    def _normalize(self) -> str:
        """Produce a canonical form for cache lookup and comparison."""
        t = self.text.strip()
        # Remove leading/trailing parentheses for normalization key
        if t.startswith("(") and t.endswith(")"):
            t = t[1:-1]
        # Normalize whitespace
        t = re.sub(r"\s+", " ", t)
        # Fix known format errors
        t = self._fix_common_format_errors(t)
        return t

    @staticmethod
    def _fix_common_format_errors(text: str) -> str:
        """Correct common citation formatting errors."""
        # Fix SCC OnLine capitalization: "Online" → "OnLine"
        text = re.sub(r"SCC\s+Online", "SCC OnLine", text, flags=re.IGNORECASE)
        # Fix "SCC123" → "SCC 123" (missing space before page number)
        text = re.sub(r"(SCC|SCR)(\d)", r"\1 \2", text)
        # Fix court code abbreviations: Delhi → Del, Bombay → Bom, etc.
        court_fixes = {
            "Delhi": "Del",
            "Bombay": "Bom",
            "Calcutta": "Cal",
            "Madras": "Mad",
            "Allahabad": "All",
            "Karnataka": "Kar",
            "Kerala": "Ker",
            "Patna": "Pat",
            "Rajasthan": "Raj",
            "Madhya": "MP",
        }
        for old, new in court_fixes.items():
            text = re.sub(rf"\b{old}\b", new, text)
        return text

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "normalized": self.normalized,
            "start": self.start,
            "end": self.end,
            "pattern_name": self.pattern_name,
            "groups": self.groups,
        }


class CitationExtractor:
    """
    Extracts Indian legal citations from text using database-driven regex patterns.

    Supports 6 citation formats:
    - SCC: (2024) 5 SCC 123
    - SCC OnLine: 2024 SCC OnLine Del 456
    - AIR: AIR 2024 SC 123
    - Cri LJ: 2024 Cri LJ 789
    - SCR: (2024) 5 SCR 123
    - MANU: MANU/SC/0123/2024
    """

    # Built-in patterns (fallback when DB not available)
    # These are intentionally MORE FLEXIBLE than the spec patterns to catch
    # format errors (missing spaces, wrong capitalization, full court names, etc.)
    BUILTIN_PATTERNS = [
        {
            "pattern_name": "SCC",
            # Flexible: handles "(2024) 5 SCC 123" and "(2023) 5 SCC123" (missing space)
            "regex": r"\((\d{4})\)\s+(\d{1,2})\s+SCC\s*(\d{1,5})",
        },
        {
            "pattern_name": "SCC_OnLine",
            # Flexible: handles "SCC OnLine" and "SCC Online" (capitalization errors)
            # Also handles full court names: "Delhi", "Bombay", etc.
            "regex": r"(\d{4})\s+SCC\s+On(?:line|Line)\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj|Delhi|Bombay|Calcutta|Madras|Allahabad|Karnataka|Kerala|Patna|Rajasthan)\s+(\d{1,6})",
        },
        {
            "pattern_name": "AIR",
            # Flexible: handles "AIR 2024 SC 123" and "AIR 2024 Delhi 234" (full court name)
            "regex": r"AIR\s+(\d{4})\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj|NOC|Delhi|Bombay|Calcutta|Madras|Allahabad|Karnataka|Kerala|Patna|Rajasthan)\s+(\d{1,5})",
        },
        {
            "pattern_name": "Cri_LJ",
            "regex": r"[\(]?(\d{4})[\)]?\s+Cri\s+LJ\s+(\d{1,5})",
        },
        {
            "pattern_name": "SCR",
            "regex": r"\((\d{4})\)\s+(\d{1,2})\s+SCR\s+(\d{1,5})",
        },
        {
            "pattern_name": "MANU",
            "regex": r"MANU/(SC|DE|MH|KA|KE|WB|TN|AP|GJ|RJ|MP|UP)/\d{4}/\d{4,6}",
        },
    ]

    def __init__(self, db_patterns: Optional[List[Dict]] = None):
        """
        Initialize extractor with patterns from database or built-in defaults.

        Args:
            db_patterns: List of dicts with 'pattern_name' and 'regex' keys.
                        If None, uses built-in patterns.
        """
        patterns = db_patterns if db_patterns else self.BUILTIN_PATTERNS
        self._compiled = []
        for p in patterns:
            try:
                compiled = re.compile(p["regex"])
                self._compiled.append((p["pattern_name"], compiled))
            except re.error:
                # Skip invalid patterns
                continue

    def extract(self, text: str) -> List[ExtractedCitation]:
        """
        Extract all citations from text. Zero false negatives is the goal.

        Args:
            text: AI-generated legal text to scan for citations.

        Returns:
            List of ExtractedCitation objects, sorted by position in text.
        """
        found: List[ExtractedCitation] = []

        for pattern_name, compiled in self._compiled:
            for match in compiled.finditer(text):
                citation_text = match.group(0)
                start = match.start()
                end = match.end()
                groups = {k: v for k, v in match.groupdict().items() if v is not None}
                # If no named groups, use numbered groups
                if not groups:
                    groups = {str(i): g for i, g in enumerate(match.groups(), 1) if g}

                cit = ExtractedCitation(citation_text, start, end, pattern_name, groups)

                # De-duplicate overlapping matches (keep the longer one)
                is_overlap = False
                for existing in found:
                    if (cit.start < existing.end and cit.end > existing.start):
                        # Overlap — keep the longer match
                        if len(citation_text) > len(existing.text):
                            found.remove(existing)
                        else:
                            is_overlap = True
                        break

                if not is_overlap:
                    found.append(cit)

        # Sort by position in text
        found.sort(key=lambda c: c.start)
        return found

    def extract_texts(self, text: str) -> List[str]:
        """Convenience: return just the citation strings."""
        return [c.text for c in self.extract(text)]