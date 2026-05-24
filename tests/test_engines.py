"""
Unit tests for BRAHMO Citation Safety Engine.

Tests:
- Citation extractor: all 6 patterns + edge cases
- Hallucination detector: all 4 rules
- Section normalizer: all 30 mappings
- Citation annotator: badge insertion + report
"""

import pytest
import sys
import os

# Add workspace to path
sys.path.insert(0, "/workspace")

from engines.citation_extractor import CitationExtractor, ExtractedCitation
from engines.hallucination_detector import HallucinationDetector
from engines.section_normalizer import SectionNormalizer
from engines.citation_annotator import CitationAnnotator
from engines.citation_verifier import VerificationResult


# ─── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def extractor():
    return CitationExtractor()  # Uses built-in patterns

@pytest.fixture
def detector():
    return HallucinationDetector(current_year=2026)

@pytest.fixture
def normalizer():
    return SectionNormalizer()  # Uses built-in mappings

@pytest.fixture
def annotator():
    return CitationAnnotator()


# ─── Citation Extractor Tests ──────────────────────────────────────────

class TestCitationExtractor:
    """Test all 6 citation patterns."""

    def test_scc_pattern(self, extractor):
        text = "In Siddharth v. State of UP (2021) 10 SCC 1, the Court held..."
        citations = extractor.extract(text)
        assert len(citations) >= 1
        assert any(c.text == "(2021) 10 SCC 1" for c in citations)
        matched = [c for c in citations if c.text == "(2021) 10 SCC 1"][0]
        assert matched.pattern_name == "SCC"

    def test_scc_online_pattern(self, extractor):
        text = "The Delhi High Court in 2024 SCC OnLine Del 3456 granted bail."
        citations = extractor.extract(text)
        assert len(citations) >= 1
        assert any("SCC OnLine Del 3456" in c.text or "SCC Online Del 3456" in c.text for c in citations)

    def test_scc_online_capitalization_error(self, extractor):
        """Should catch 'Online' even though correct form is 'OnLine'."""
        text = "In 2024 SCC Online Del 3456, the Court held..."
        citations = extractor.extract(text)
        assert len(citations) >= 1

    def test_air_pattern(self, extractor):
        text = "In Amit Kumar v. Union of India AIR 2024 SC 567, the Court..."
        citations = extractor.extract(text)
        assert len(citations) >= 1
        assert any("AIR 2024 SC 567" in c.text for c in citations)

    def test_air_full_court_name(self, extractor):
        """Should catch 'AIR 2024 Delhi 234' even though short form is 'Del'."""
        text = "In AIR 2024 Delhi 234, the Court clarified..."
        citations = extractor.extract(text)
        assert len(citations) >= 1
        assert any("AIR 2024 Delhi 234" in c.text for c in citations)

    def test_cri_lj_pattern(self, extractor):
        text = "See 2024 Cri LJ 789 for detailed analysis."
        citations = extractor.extract(text)
        assert len(citations) >= 1

    def test_cri_lj_with_parens(self, extractor):
        text = "In (2024) Cri LJ 789, the Court..."
        citations = extractor.extract(text)
        assert len(citations) >= 1

    def test_scr_pattern(self, extractor):
        text = "In (2024) 5 SCR 123, the Supreme Court..."
        citations = extractor.extract(text)
        assert len(citations) >= 1

    def test_manu_pattern(self, extractor):
        text = "In MANU/SC/0123/2024, the Court..."
        citations = extractor.extract(text)
        assert len(citations) >= 1
        assert any("MANU/SC/0123/2024" in c.text for c in citations)

    def test_scc_missing_space(self, extractor):
        """Should catch '(2023) 5 SCC123' despite missing space before page."""
        text = "In (2023) 5 SCC123, the Court held..."
        citations = extractor.extract(text)
        assert len(citations) >= 1

    def test_multiple_citations(self, extractor):
        """Sample output 1: should find 5 SCC citations."""
        text = """In Siddharth v. State of UP (2021) 10 SCC 1, the Court laid down guidelines.
In Satender Kumar Antil v. CBI (2022) 10 SCC 51, the Court classified offences.
In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, the Court issued guidelines.
In Sushila Aggarwal v. State (2020) 5 SCC 1, the Court clarified bail.
The Delhi High Court in 2024 SCC OnLine Del 3456 granted bail."""
        citations = extractor.extract(text)
        assert len(citations) == 5, f"Expected 5, found {len(citations)}: {[c.text for c in citations]}"

    def test_sample_output_2_hallucinated(self, extractor):
        """Sample output 2: should find 7 citations (5 SCC + 2 AIR)."""
        text = """The Supreme Court in Rajesh Sharma v. State of UP (2023) 4 SCC 789 held that.
In Siddharth v. State of UP (2021) 10 SCC 1, the Court emphasized bail.
In Amit Kumar v. Union of India AIR 2024 SC 567, the Court reiterated.
In Satender Kumar Antil v. CBI (2022) 10 SCC 51, offences were classified.
In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, the Court issued guidelines.
In Sushila Aggarwal v. State (2020) 5 SCC 12, the Court confirmed.
In Vikram Singh v. State (2024) 8 SCC 234, the Court held."""
        citations = extractor.extract(text)
        assert len(citations) == 7, f"Expected 7, found {len(citations)}: {[c.text for c in citations]}"

    def test_no_false_positives(self, extractor):
        """Should not extract citations from plain text."""
        text = "The lawyer asked the court to grant bail. The case was about fraud."
        citations = extractor.extract(text)
        assert len(citations) == 0

    def test_zero_false_negatives(self, extractor):
        """Every real citation format must be caught."""
        test_cases = [
            "(2024) 5 SCC 123",
            "2024 SCC OnLine Del 456",
            "AIR 2024 SC 123",
            "2024 Cri LJ 789",
            "(2024) 5 SCR 123",
            "MANU/SC/0123/2024",
        ]
        for citation in test_cases:
            found = extractor.extract(citation)
            assert len(found) >= 1, f"Missed citation: {citation}"


# ─── Hallucination Detector Tests ──────────────────────────────────────

class TestHallucinationDetector:
    """Test all 4 hallucination rules."""

    def test_future_year(self, detector):
        result = detector.check("(2028) 3 SCC 45", "SCC", {"1": "2028", "2": "3", "3": "45"})
        assert result.is_hallucinated
        assert result.rule == "future_year"

    def test_impossible_scc_volume(self, detector):
        result = detector.check("(2024) 47 SCC 123", "SCC", {"1": "2024", "2": "47", "3": "123"})
        assert result.is_hallucinated
        assert result.rule == "impossible_volume"

    def test_impossible_page(self, detector):
        result = detector.check("(2024) 5 SCC 9999", "SCC", {"1": "2024", "2": "5", "3": "9999"})
        assert result.is_suspicious
        assert result.rule == "impossible_page"

    def test_pre_1900(self, detector):
        result = detector.check("(1856) 3 SCC 45", "SCC", {"1": "1856", "2": "3", "3": "45"})
        assert result.is_hallucinated
        assert result.rule == "pre_1900"

    def test_valid_citation_passes(self, detector):
        result = detector.check("(2021) 10 SCC 1", "SCC", {"1": "2021", "2": "10", "3": "1"})
        assert not result.is_hallucinated
        assert not result.is_suspicious

    def test_air_passes(self, detector):
        result = detector.check("AIR 2024 SC 123", "AIR", {"1": "2024", "2": "SC", "3": "123"})
        assert not result.is_hallucinated

    def test_manu_passes(self, detector):
        result = detector.check("MANU/SC/0123/2024", "MANU", {})
        assert not result.is_hallucinated


# ─── Section Normalizer Tests ──────────────────────────────────────────

class TestSectionNormalizer:
    """Test all 30 section mappings."""

    def test_section_420_ipc(self, normalizer):
        text = "Under Section 420 IPC, the accused committed cheating."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 318 BNS" for a in alerts)

    def test_section_406_ipc(self, normalizer):
        text = "Section 406 IPC criminal breach of trust."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 316 BNS" for a in alerts)

    def test_section_120b_ipc(self, normalizer):
        text = "Section 120B IPC criminal conspiracy."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 61 BNS" for a in alerts)

    def test_section_34_ipc(self, normalizer):
        text = "Section 34 IPC common intention."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 3(5) BNS" for a in alerts)

    def test_crpc_section_482(self, normalizer):
        text = "Section 482 CrPC inherent powers."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 528 BNSS" for a in alerts)

    def test_crpc_section_438(self, normalizer):
        text = "Section 438 CrPC anticipatory bail."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 482 BNSS" for a in alerts)

    def test_iea_section_65b(self, normalizer):
        text = "Section 65B IEA electronic evidence."
        _, alerts = normalizer.normalize(text)
        assert any(a.converted == "Section 63 BSA" for a in alerts)

    def test_sample_output_3(self, normalizer):
        """Sample output 3: should find 4 IPC references."""
        text = """COMPLAINT UNDER SECTION 420 IPC AND SECTION 406 IPC
The complainant submits that the accused committed offences under Section 420 of the Indian Penal Code
read with Section 120B IPC and Section 34 IPC.
FIR be registered under Sections 420, 406, 120B and 34 of the Indian Penal Code."""
        _, alerts = normalizer.normalize(text)
        # Should have alerts for at least 420, 406, 120B, 34
        converted = [a.converted for a in alerts]
        assert any("318 BNS" in c for c in converted), f"Missing 420 IPC → 318 BNS. Got: {converted}"
        assert any("316 BNS" in c for c in converted), f"Missing 406 IPC → 316 BNS. Got: {converted}"
        assert any("61 BNS" in c for c in converted), f"Missing 120B IPC → 61 BNS. Got: {converted}"
        assert any("3(5) BNS" in c for c in converted), f"Missing 34 IPC → 3(5) BNS. Got: {converted}"

    def test_no_false_positives(self, normalizer):
        """Normal text should not trigger alerts."""
        text = "The lawyer filed a petition for bail in the High Court."
        _, alerts = normalizer.normalize(text)
        assert len(alerts) == 0

    def test_all_30_mappings_loaded(self, normalizer):
        """Verify all 30 mappings are loaded."""
        assert len(normalizer._mappings) == 30, f"Expected 30 mappings, got {len(normalizer._mappings)}"


# ─── Citation Annotator Tests ──────────────────────────────────────────

class TestCitationAnnotator:
    """Test annotation and report generation."""

    def test_verified_annotation(self, annotator):
        text = "In (2021) 10 SCC 1, the Court held."
        citations = [ExtractedCitation("(2021) 10 SCC 1", 3, 19, "SCC", {"1": "2021", "2": "10", "3": "1"})]
        verifications = [VerificationResult(
            citation="(2021) 10 SCC 1",
            normalized="(2021) 10 SCC 1",
            status="VERIFIED",
            source="ik_api",
            case_name="Siddharth v. State of UP",
            cost=0.8,
        )]
        result = annotator.annotate(text, citations, verifications)
        assert "✅" in result["annotated_html"]
        assert result["report"].verified == 1
        assert result["report"].total_citations == 1

    def test_hallucinated_annotation(self, annotator):
        text = "In (2028) 3 SCC 45, the Court held."
        citations = [ExtractedCitation("(2028) 3 SCC 45", 3, 18, "SCC", {"1": "2028", "2": "3", "3": "45"})]
        verifications = [VerificationResult(
            citation="(2028) 3 SCC 45",
            normalized="(2028) 3 SCC 45",
            status="HALLUCINATED",
            source="pre_filter",
            reason="Future year",
        )]
        result = annotator.annotate(text, citations, verifications)
        assert "❌" in result["annotated_html"]
        assert "<del>" in result["annotated_html"]
        assert result["report"].removed == 1

    def test_mixed_annotations(self, annotator):
        text = "In (2021) 10 SCC 1 and (2028) 3 SCC 45."
        c1 = ExtractedCitation("(2021) 10 SCC 1", 3, 19, "SCC", {"1": "2021", "2": "10", "3": "1"})
        c2 = ExtractedCitation("(2028) 3 SCC 45", 24, 39, "SCC", {"1": "2028", "2": "3", "3": "45"})
        v1 = VerificationResult("(2021) 10 SCC 1", "(2021) 10 SCC 1", "VERIFIED", "ik_api", case_name="Siddharth v. State of UP", cost=0.8)
        v2 = VerificationResult("(2028) 3 SCC 45", "(2028) 3 SCC 45", "HALLUCINATED", "pre_filter", reason="Future year")
        result = annotator.annotate(text, [c1, c2], [v1, v2])
        assert result["report"].total_citations == 2
        assert result["report"].verified == 1
        assert result["report"].removed == 1

    def test_empty_text(self, annotator):
        result = annotator.annotate("", [], [])
        assert result["report"].total_citations == 0
        assert result["report"].accuracy_pct == 100.0


# ─── Integration: Full Pipeline ────────────────────────────────────────

class TestFullPipeline:
    """Test the full extraction → detection → annotation pipeline."""

    def test_scenario_1_hallucinated(self, extractor, detector, annotator):
        """Scenario 1: 7 citations, 2 fabricated, 1 corrected page."""
        text = """The Supreme Court in Rajesh Sharma v. State of UP (2023) 4 SCC 789 held that.
In Siddharth v. State of UP (2021) 10 SCC 1, the Court emphasized bail.
In Amit Kumar v. Union of India AIR 2024 SC 567, the Court reiterated.
In Satender Kumar Antil v. CBI (2022) 10 SCC 51, offences classified.
In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, guidelines issued.
In Sushila Aggarwal v. State (2020) 5 SCC 12, bail orders.
In Vikram Singh v. State (2024) 8 SCC 234, economic offences."""
        citations = extractor.extract(text)
        assert len(citations) == 7
        hallucinations = [
            detector.check(c.text, c.pattern_name, c.groups) for c in citations
        ]
        # None should be pre-filtered as hallucinated (all have valid years/volumes)
        pre_filtered = [h for h in hallucinations if h.is_hallucinated]
        assert len(pre_filtered) == 0

    def test_scenario_3_impossible(self, extractor, detector):
        """Scenario 3: Pre-filter catches future year + impossible volume."""
        text = """In State v. Balbir Singh (2028) 3 SCC 45, the Court revisited.
In Tofan Singh v. State (2024) 47 SCC 123, the majority held.
In Mohd. Arif v. State (2023) 19 SCC 456, the Court distinguished.
In Union of India v. Shiv Shankar (2021) 8 SCC 456, the Court held.
In R v. State (2020) 10 SCC 123, clarified burden.
In Abdul Rashid v. State (2022) 5 SCC 789, prolonged incarceration.
In Priya v. State (2019) 12 SCC 345, examined presumption.
In State v. Rajesh Kumar (2023) 9 SCC 123, noted bail."""
        citations = extractor.extract(text)
        assert len(citations) == 8

        hallucinations = [
            detector.check(c.text, c.pattern_name, c.groups) for c in citations
        ]
        pre_filtered = [h for h in hallucinations if h.is_hallucinated]
        assert len(pre_filtered) == 2
        rules = [h.rule for h in pre_filtered]
        assert "future_year" in rules
        assert "impossible_volume" in rules