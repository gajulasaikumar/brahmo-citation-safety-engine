"""
Citation Annotator — Badge insertion + verification report generation.

Takes the raw AI output and verification results, and produces:
1. Annotated text with ✅ VERIFIED / ⚠️ CORRECTED / ⚠️ UNVERIFIED / ❌ REMOVED badges
2. A verification report with counts, accuracy %, cost, and cost savings
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from engines.citation_extractor import ExtractedCitation
from engines.citation_verifier import VerificationResult


@dataclass
class AnnotationReport:
    """Summary report for a citation verification run."""
    total_citations: int
    verified: int
    corrected: int
    unverified: int
    removed: int  # includes hallucinated
    hallucinated: int  # subset of removed that were caught by pre-filter
    accuracy_pct: float
    ik_api_calls: int
    ik_cost_inr: float
    pre_filtered: int  # citations caught without API call
    cost_saved_inr: float  # money saved by pre-filtering

    def to_dict(self) -> dict:
        return {
            "total_citations": self.total_citations,
            "verified": self.verified,
            "corrected": self.corrected,
            "unverified": self.unverified,
            "removed": self.removed,
            "hallucinated": self.hallucinated,
            "accuracy_pct": round(self.accuracy_pct, 1),
            "ik_api_calls": self.ik_api_calls,
            "ik_cost_inr": round(self.ik_cost_inr, 2),
            "pre_filtered": self.pre_filtered,
            "cost_saved_inr": round(self.cost_saved_inr, 2),
        }


class CitationAnnotator:
    """
    Annotates AI output with citation verification badges and
    generates a summary verification report.
    """

    # Badge templates for each status
    BADGES = {
        "VERIFIED": "✅",
        "CORRECTED": "⚠️",
        "UNVERIFIED": "⚠️",
        "HALLUCINATED": "❌",
        "NOT_FOUND": "❌",
    }

    STATUS_LABELS = {
        "VERIFIED": "VERIFIED — case exists in Indian Kanoon",
        "CORRECTED": "CORRECTED — citation format corrected",
        "UNVERIFIED": "UNVERIFIED — not found in Indian Kanoon (may be real but unindexed)",
        "HALLUCINATED": "REMOVED — hallucinated citation",
        "NOT_FOUND": "REMOVED — case not found in Indian Kanoon",
    }

    def annotate(self, text: str, citations: List[ExtractedCitation],
                 verifications: List[VerificationResult]) -> Dict:
        """
        Annotate the AI output with verification badges.

        Args:
            text: Original AI-generated text
            citations: List of extracted citations (positioned in text)
            verifications: Corresponding verification results

        Returns:
            Dict with 'annotated_html', 'report', and 'citations' keys
        """
        # Build citation details list
        citation_details = []
        for cit, ver in zip(citations, verifications):
            status = ver.status
            badge = self.BADGES.get(status, "⚠️")
            label = self.STATUS_LABELS.get(status, status)

            # Build detail text
            detail_parts = [f"{badge} {cit.text}"]
            if ver.case_name:
                detail_parts.append(f"   Case: {ver.case_name}")
            detail_parts.append(f"   [{label}]")
            if ver.corrected_citation:
                detail_parts.append(f"   Corrected to: {ver.corrected_citation}")
            if ver.reason:
                detail_parts.append(f"   {ver.reason}")

            citation_details.append({
                "original": cit.text,
                "normalized": cit.normalized,
                "status": status,
                "badge": badge,
                "label": label,
                "case_name": ver.case_name,
                "reason": ver.reason,
                "source": ver.source,
                "cost": ver.cost,
                "corrected_citation": ver.corrected_citation,
                "detail": "\n".join(detail_parts),
            })

        # Build annotated HTML — replace citations inline with badges
        annotated_html = self._build_annotated_html(text, citations, verifications)

        # Build report
        report = self._build_report(verifications)

        return {
            "annotated_html": annotated_html,
            "report": report,
            "citations": citation_details,
        }

    def _build_annotated_html(self, text: str,
                              citations: List[ExtractedCitation],
                              verifications: List[VerificationResult]) -> str:
        """Build HTML with inline citation badges."""
        if not citations:
            return self._escape_html(text)

        # Process citations in reverse order to preserve positions
        html = text
        for cit, ver in reversed(list(zip(citations, verifications))):
            status = ver.status
            badge = self.BADGES.get(status, "⚠️")
            label = self.STATUS_LABELS.get(status, status)

            if status in ("HALLUCINATED", "NOT_FOUND"):
                # Strikethrough for removed citations
                replacement = (
                    f'<span class="citation-badge citation-removed">'
                    f'<del>{self._escape_html(cit.text)}</del>'
                    f' <span class="badge-icon">{badge}</span>'
                    f' <span class="badge-label">{label}</span>'
                    f'</span>'
                )
            elif status == "CORRECTED":
                replacement = (
                    f'<span class="citation-badge citation-corrected">'
                    f'{self._escape_html(cit.text)}'
                    f' <span class="badge-icon">{badge}</span>'
                    f' <span class="badge-label">{label}'
                    f'{" — → " + self._escape_html(ver.corrected_citation) if ver.corrected_citation else ""}</span>'
                    f'</span>'
                )
            elif status == "UNVERIFIED":
                replacement = (
                    f'<span class="citation-badge citation-unverified">'
                    f'{self._escape_html(cit.text)}'
                    f' <span class="badge-icon">{badge}</span>'
                    f' <span class="badge-label">{label}</span>'
                    f'</span>'
                )
            else:  # VERIFIED
                replacement = (
                    f'<span class="citation-badge citation-verified">'
                    f'{self._escape_html(cit.text)}'
                    f' <span class="badge-icon">{badge}</span>'
                    f' <span class="badge-label">{label}</span>'
                    f'</span>'
                )

            # Replace at exact position
            html = html[:cit.start] + replacement + html[cit.end:]

        # Convert newlines to <br>, escape the rest
        html = html.replace("\n", "<br>\n")
        return html

    def _build_report(self, verifications: List[VerificationResult]) -> AnnotationReport:
        """Build the verification report summary."""
        total = len(verifications)
        verified = sum(1 for v in verifications if v.status == "VERIFIED")
        corrected = sum(1 for v in verifications if v.status == "CORRECTED")
        unverified = sum(1 for v in verifications if v.status == "UNVERIFIED")
        removed = sum(1 for v in verifications if v.status in ("HALLUCINATED", "NOT_FOUND"))
        hallucinated = sum(1 for v in verifications if v.status == "HALLUCINATED")

        ik_calls = sum(1 for v in verifications if v.source in ("ik_api", "cache"))
        ik_cost = sum(v.cost for v in verifications)
        pre_filtered = sum(1 for v in verifications if v.source == "pre_filter")
        cost_saved = pre_filtered * (0.5 + 0.3)  # search + docmeta we didn't have to call

        # Accuracy = (verified + corrected) / total
        safe = verified + corrected
        accuracy = (safe / total * 100) if total > 0 else 100.0

        return AnnotationReport(
            total_citations=total,
            verified=verified,
            corrected=corrected,
            unverified=unverified,
            removed=removed,
            hallucinated=hallucinated,
            accuracy_pct=accuracy,
            ik_api_calls=ik_calls,
            ik_cost_inr=ik_cost,
            pre_filtered=pre_filtered,
            cost_saved_inr=cost_saved,
        )

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))