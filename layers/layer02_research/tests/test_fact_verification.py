"""
Tests for Fact Verification Module
Layer 2: Research Engine — Module 6

Run: python -m pytest layers/layer02_research/tests/test_fact_verification.py -v
"""

import pytest

from layers.layer02_research.modules.fact_verification.claim_extractor import ClaimExtractor, Claim
from layers.layer02_research.modules.fact_verification.evidence_matcher import EvidenceMatcher, EvidenceMatch
from layers.layer02_research.modules.fact_verification.source_validator import SourceValidator, SourceValidation
from layers.layer02_research.modules.fact_verification.contradiction_detector import ContradictionDetector, Contradiction
from layers.layer02_research.modules.fact_verification.citation_builder import CitationBuilder, Citation
from layers.layer02_research.modules.fact_verification.verification_engine import VerificationEngine
from layers.layer02_research.modules.fact_verification.verification_manager import VerificationManager


@pytest.fixture
def manager(tmp_path):
    return VerificationManager(storage_path=str(tmp_path / "verification.json"))


# ═══════════════════════════════════════════
# Test 1: Claim Extractor
# ═══════════════════════════════════════════

class TestClaimExtractor:
    def test_extract_basic(self):
        ce = ClaimExtractor()
        claims = ce.extract("AI jobs are increasing by 25%. The market is growing rapidly.")
        assert len(claims) >= 1

    def test_extract_statistical(self):
        ce = ClaimExtractor()
        claims = ce.extract_statistical("Revenue increased by 30% last quarter.")
        assert len(claims) >= 1
        assert claims[0].claim_type == "statistical"

    def test_extract_trends(self):
        ce = ClaimExtractor()
        claims = ce.extract_trends("AI is increasing in popularity across industries.")
        assert len(claims) >= 1
        assert claims[0].claim_type == "trend"

    def test_claim_types(self):
        ce = ClaimExtractor()
        claims = ce.extract("Python is better than Java for machine learning tasks.")
        types = [c.claim_type for c in claims]
        assert "comparative" in types or "general" in types

    def test_claim_confidence(self):
        ce = ClaimExtractor()
        claims = ce.extract("There are 5 million AI developers worldwide.")
        assert len(claims) > 0
        assert claims[0].confidence > 0

    def test_claim_to_dict(self):
        c = Claim(text="Test claim", claim_type="statistical", subject="AI")
        d = c.to_dict()
        assert d["text"] == "Test claim"
        assert d["claim_type"] == "statistical"

    def test_claim_from_dict(self):
        d = {"text": "Restored claim", "claim_type": "trend"}
        c = Claim.from_dict(d)
        assert c.text == "Restored claim"
        assert c.claim_type == "trend"

    def test_empty_text(self):
        ce = ClaimExtractor()
        assert ce.extract("") == []

    def test_short_sentences_filtered(self):
        ce = ClaimExtractor(min_claim_length=20)
        claims = ce.extract("Yes. No. Maybe.")
        assert len(claims) == 0

    def test_max_claims(self):
        ce = ClaimExtractor(max_claims=2)
        text = ". ".join([f"Sentence number {i} is a factual claim about AI." for i in range(10)])
        claims = ce.extract(text)
        assert len(claims) <= 2

    def test_hedging_reduces_confidence(self):
        ce = ClaimExtractor()
        claims = ce.extract("AI might possibly increase by 25% in the future.")
        assert len(claims) > 0
        assert claims[0].confidence < 0.7

    def test_causal_claim(self):
        ce = ClaimExtractor()
        claims = ce.extract("Machine learning causes improved prediction accuracy in healthcare.")
        types = [c.claim_type for c in claims]
        assert "causal" in types or "general" in types


# ═══════════════════════════════════════════
# Test 2: Evidence Matcher
# ═══════════════════════════════════════════

class TestEvidenceMatcher:
    def test_match_basic(self):
        em = EvidenceMatcher(min_similarity=0.1)
        claim = Claim(text="AI jobs are increasing rapidly", claim_type="trend")
        evidence = [
            {"text": "AI jobs are growing fast in the tech sector", "source": "TechNews"},
            {"text": "Cooking recipes for beginners", "source": "FoodBlog"},
        ]
        matches = em.match(claim, evidence)
        assert len(matches) >= 1
        assert matches[0].evidence_source == "TechNews"

    def test_match_keyword_overlap(self):
        em = EvidenceMatcher(min_keyword_overlap=0.2)
        claim = Claim(text="Python programming language is popular", claim_type="general")
        evidence = [{"text": "Python is the most popular programming language", "source": "DevBlog"}]
        matches = em.match(claim, evidence)
        assert len(matches) >= 1

    def test_match_no_match(self):
        em = EvidenceMatcher(min_similarity=0.5, min_keyword_overlap=0.5)
        claim = Claim(text="AI jobs boom", claim_type="trend")
        evidence = [{"text": "Cooking pasta is fun", "source": "FoodBlog"}]
        matches = em.match(claim, evidence)
        assert len(matches) == 0

    def test_match_batch(self):
        em = EvidenceMatcher(min_similarity=0.1)
        claims = [
            Claim(text="AI is growing", claim_type="trend"),
            Claim(text="Python is popular", claim_type="general"),
        ]
        evidence = [{"text": "AI growth continues in 2026", "source": "TechNews"}]
        results = em.match_batch(claims, evidence)
        assert len(results) == 2

    def test_support_detection(self):
        em = EvidenceMatcher()
        claim = Claim(text="AI is increasing", claim_type="trend")
        evidence = [{"text": "AI is not decreasing at all", "source": "News"}]
        matches = em.match(claim, evidence, top_n=1)
        if matches:
            assert isinstance(matches[0].supports, bool)

    def test_match_to_dict(self):
        m = EvidenceMatch("c1", "evidence text", "source", 0.8, 0.6, True)
        d = m.to_dict()
        assert d["claim_id"] == "c1"
        assert d["similarity_score"] == 0.8


# ═══════════════════════════════════════════
# Test 3: Source Validator
# ═══════════════════════════════════════════

class TestSourceValidator:
    def test_validate_known_source(self):
        sv = SourceValidator()
        result = sv.validate("Reuters")
        assert result.credibility_score >= 0.9
        assert result.authority_level == "reputable"

    def test_validate_unknown_source(self):
        sv = SourceValidator()
        result = sv.validate("MyRandomBlog")
        assert result.credibility_score <= 0.5

    def test_validate_edu_source(self):
        sv = SourceValidator()
        result = sv.validate("MIT research paper")
        assert result.credibility_score >= 0.8
        assert result.is_primary_source is True

    def test_validate_batch(self):
        sv = SourceValidator()
        results = sv.validate_batch(["Reuters", "BBC", "RandomBlog"])
        assert len(results) == 3

    def test_cross_corroborate(self):
        sv = SourceValidator()
        validations = sv.validate_batch(["Reuters", "BBC"])
        result = sv.cross_corroborate(validations)
        assert result["is_corroborated"] is True
        assert result["avg_credibility"] > 0.8

    def test_cross_corroborate_insufficient(self):
        sv = SourceValidator()
        validations = sv.validate_batch(["RandomBlog"])
        result = sv.cross_corroborate(validations, min_sources=3)
        assert result["is_corroborated"] is False

    def test_register_source(self):
        sv = SourceValidator()
        sv.register_source("MySource", 0.85)
        assert sv.get_source_score("MySource") == 0.85

    def test_get_source_score(self):
        sv = SourceValidator()
        assert sv.get_source_score("Reuters") >= 0.9
        assert sv.get_source_score("Unknown") < 0.5

    def test_validation_to_dict(self):
        v = SourceValidation("Test")
        v.credibility_score = 0.8
        d = v.to_dict()
        assert d["source_name"] == "Test"
        assert d["credibility_score"] == 0.8


# ═══════════════════════════════════════════
# Test 4: Contradiction Detector
# ═══════════════════════════════════════════

class TestContradictionDetector:
    def test_no_contradiction(self):
        cd = ContradictionDetector()
        contradictions = cd.detect("AI is increasing", "AI growth is significant")
        assert len(contradictions) == 0

    def test_direction_contradiction(self):
        cd = ContradictionDetector()
        contradictions = cd.detect("AI increase is rapid", "AI decrease is significant")
        assert len(contradictions) >= 1
        assert contradictions[0].contradiction_type in ("direction", "negation")

    def test_negation_contradiction(self):
        cd = ContradictionDetector()
        contradictions = cd.detect("This is always true", "This is never accurate")
        assert len(contradictions) >= 1

    def test_detect_batch(self):
        cd = ContradictionDetector()
        contradictions = cd.detect_batch(
            "AI is increasing",
            ["AI is decreasing", "AI growth continues"],
        )
        assert isinstance(contradictions, list)

    def test_severity(self):
        cd = ContradictionDetector()
        contradictions = cd.detect("Revenue increased by 50%", "Revenue decreased by 50%")
        if contradictions:
            assert contradictions[0].severity > 0

    def test_contradiction_to_dict(self):
        c = Contradiction("claim", "evidence", "direction", 0.7, "desc")
        d = c.to_dict()
        assert d["contradiction_type"] == "direction"
        assert d["severity"] == 0.7

    def test_sensitivity(self):
        cd_high = ContradictionDetector(sensitivity=1.0)
        cd_low = ContradictionDetector(sensitivity=0.1)
        c_high = cd_high.detect("AI is increasing", "AI is decreasing")
        c_low = cd_low.detect("AI is increasing", "AI is decreasing")
        if c_high and c_low:
            assert c_high[0].severity >= c_low[0].severity

    def test_get_contradiction_severity_empty(self):
        cd = ContradictionDetector()
        assert cd.get_contradiction_severity([]) == 0.0


# ═══════════════════════════════════════════
# Test 5: Citation Builder
# ═══════════════════════════════════════════

class TestCitationBuilder:
    def test_build_citation(self):
        cb = CitationBuilder()
        c = cb.build_citation("Reuters", title="AI Report", date="2026")
        assert c.source_name == "Reuters"
        assert "Reuters" in c.citation_text

    def test_format_inline(self):
        cb = CitationBuilder()
        c = cb.build_citation("BBC")
        assert cb.format_citation(c, "inline") == "(BBC)"

    def test_format_apa(self):
        cb = CitationBuilder()
        c = cb.build_citation("BBC", author="John Smith", date="2026", title="AI News")
        formatted = cb.format_citation(c, "apa")
        assert "John Smith" in formatted
        assert "2026" in formatted

    def test_format_mla(self):
        cb = CitationBuilder()
        c = cb.build_citation("BBC", author="Smith", title="AI News")
        formatted = cb.format_citation(c, "mla")
        assert "Smith" in formatted

    def test_build_from_evidence(self):
        cb = CitationBuilder()
        evidence = [
            {"source": "Reuters", "title": "Report", "credibility_score": 0.9},
            {"source": "BBC", "title": "News", "credibility_score": 0.8},
        ]
        citations = cb.build_from_evidence(evidence)
        assert len(citations) == 2

    def test_build_reference_list(self):
        cb = CitationBuilder()
        c1 = cb.build_citation("Reuters", date="2026")
        c2 = cb.build_citation("BBC", date="2025")
        refs = cb.build_reference_list([c1, c2], style="apa")
        assert len(refs) == 2

    def test_deduplication(self):
        cb = CitationBuilder()
        evidence = [
            {"source": "Reuters", "title": "Same Report"},
            {"source": "Reuters", "title": "Same Report"},
        ]
        citations = cb.build_from_evidence(evidence)
        assert len(citations) == 1

    def test_citation_to_dict(self):
        c = Citation("Reuters", title="Test")
        d = c.to_dict()
        assert d["source_name"] == "Reuters"

    def test_format_plain(self):
        cb = CitationBuilder()
        c = cb.build_citation("Reuters", title="AI Report")
        assert cb.format_citation(c, "plain") == c.citation_text


# ═══════════════════════════════════════════
# Test 6: Verification Engine
# ═══════════════════════════════════════════

class TestVerificationEngine:
    def test_verify_basic(self):
        ve = VerificationEngine()
        claim = Claim(text="AI jobs are increasing rapidly", claim_type="trend")
        evidence = [
            {"text": "AI jobs growing fast in 2026", "source": "TechNews"},
            {"text": "AI employment opportunities expanding", "source": "IndustryReport"},
        ]
        result = ve.verify(claim, evidence)
        assert result.status in ("verified", "partially_verified", "unverified")
        assert result.confidence_result.confidence > 0

    def test_verify_contradicted(self):
        ve = VerificationEngine()
        claim = Claim(text="AI increase is rapid in all sectors", claim_type="trend")
        evidence = [
            {"text": "AI decrease is significant across all industries", "source": "Report"},
        ]
        result = ve.verify(claim, evidence)
        # Contradictions detected OR status reflects uncertainty
        assert result.status in ("contradicted", "unverified", "partially_verified") or len(result.contradictions) > 0

    def test_verify_insufficient_data(self):
        ve = VerificationEngine()
        claim = Claim(text="Quantum computing cures cancer", claim_type="general")
        evidence = []
        result = ve.verify(claim, evidence)
        assert result.status == "insufficient_data"

    def test_verify_batch(self):
        ve = VerificationEngine()
        claims = [
            Claim(text="AI is growing", claim_type="trend"),
            Claim(text="Python is popular", claim_type="general"),
        ]
        evidence = [{"text": "AI growth continues", "source": "TechNews"}]
        results = ve.verify_batch(claims, evidence)
        assert len(results) == 2

    def test_result_to_dict(self):
        ve = VerificationEngine()
        claim = Claim(text="Test claim")
        result = ve.verify(claim, [])
        d = result.to_dict()
        assert "claim" in d
        assert "status" in d
        assert "confidence" in d

    def test_evidence_matches_in_result(self):
        ve = VerificationEngine()
        claim = Claim(text="AI is increasing")
        evidence = [{"text": "AI growth is significant", "source": "News"}]
        result = ve.verify(claim, evidence)
        assert isinstance(result.evidence_matches, list)


# ═══════════════════════════════════════════
# Test 7: Verification Manager
# ═══════════════════════════════════════════

class TestManager:
    def test_verify_text(self, manager):
        text = "AI jobs are increasing by 25%. The market is growing rapidly."
        evidence = [{"text": "AI employment is growing fast", "source": "TechNews"}]
        results = manager.verify_text(text, evidence)
        assert len(results) >= 1

    def test_verify_claim(self, manager):
        evidence = [{"text": "AI growth continues in 2026", "source": "TechNews"}]
        result = manager.verify_claim("AI is increasing", evidence)
        assert result.status in ("verified", "partially_verified", "unverified", "insufficient_data")

    def test_get_result(self, manager):
        evidence = [{"text": "test evidence", "source": "News"}]
        result = manager.verify_claim("Test claim", evidence)
        found = manager.get_result(result.claim.claim_id)
        assert found is not None

    def test_get_statistics(self, manager):
        evidence = [{"text": "evidence", "source": "News"}]
        manager.verify_claim("Claim 1", evidence)
        manager.verify_claim("Claim 2", evidence)
        stats = manager.get_statistics()
        assert stats["total"] == 2

    def test_get_verified_claims(self, manager):
        verified = manager.get_verified_claims()
        assert isinstance(verified, list)

    def test_get_contradicted_claims(self, manager):
        contradicted = manager.get_contradicted_claims()
        assert isinstance(contradicted, list)

    def test_get_average_confidence(self, manager):
        evidence = [{"text": "evidence", "source": "News"}]
        manager.verify_claim("Claim", evidence)
        avg = manager.get_average_confidence()
        assert avg >= 0

    def test_health_check(self, manager):
        h = manager.health_check()
        assert h["total_verified"] == 0
        assert h["claim_extractor_ready"] is True
        assert h["confidence_engine_ready"] is True

    def test_health_check_with_data(self, manager):
        evidence = [{"text": "evidence", "source": "News"}]
        manager.verify_claim("Claim", evidence)
        h = manager.health_check()
        assert h["total_verified"] == 1

    def test_persistence(self, tmp_path):
        path = tmp_path / "verify.json"
        m1 = VerificationManager(storage_path=str(path))
        evidence = [{"text": "evidence", "source": "News"}]
        m1.verify_claim("Test", evidence)
        # Verify file was written
        assert path.exists()
        import json
        data = json.loads(path.read_text())
        assert len(data.get("history", [])) >= 1

    def test_no_storage(self):
        m = VerificationManager()
        evidence = [{"text": "evidence", "source": "News"}]
        m.verify_claim("Test", evidence)
        assert m.get_statistics()["total"] == 1

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid")
        m = VerificationManager(storage_path=str(path))
        assert m.get_statistics()["total"] == 0

    def test_verify_text_multiple_claims(self, manager):
        text = "AI is increasing by 30%. Python is better than Java. The market is growing."
        evidence = [{"text": "AI growth continues", "source": "News"}]
        results = manager.verify_text(text, evidence)
        assert len(results) >= 1

    def test_concurrent_verification(self, manager):
        import threading
        errors = []

        def verify(i):
            try:
                manager.verify_claim(f"Claim {i}", [{"text": "evidence", "source": "News"}])
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=verify, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert manager.get_statistics()["total"] == 10
