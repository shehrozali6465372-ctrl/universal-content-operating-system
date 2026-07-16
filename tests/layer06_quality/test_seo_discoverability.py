"""Tests for Layer 6 Module 5 — SEO & Discoverability Engine."""
from layers.layer06_quality.modules.seo_discoverability_engine.keyword_analyzer import KeywordAnalyzer
from layers.layer06_quality.modules.seo_discoverability_engine.hashtag_optimizer import HashtagOptimizer
from layers.layer06_quality.modules.seo_discoverability_engine.metadata_checker import MetadataChecker
from layers.layer06_quality.modules.seo_discoverability_engine.social_search_optimizer import SocialSearchOptimizer
from layers.layer06_quality.modules.seo_discoverability_engine.seo_engine import SEOEngine
from layers.layer06_quality.modules.seo_discoverability_engine.seo_report import (
    SEODiscoverabilityReport, KeywordResult, HashtagResult, MetadataResult,
)


# ── KeywordAnalyzer Tests ──

class TestKeywordAnalyzer:
    def setup_method(self):
        self.analyzer = KeywordAnalyzer()

    def test_analyze_with_keyword(self):
        result = self.analyzer.analyze(
            "AI is transforming healthcare. AI technology helps doctors.", "AI"
        )
        assert isinstance(result, KeywordResult)
        assert result.keyword_count >= 2
        assert result.keyword_density > 0

    def test_analyze_no_keyword(self):
        result = self.analyzer.analyze("Hello world.", "AI")
        assert result.keyword_count == 0

    def test_keyword_in_title(self):
        result = self.analyzer.analyze(
            "AI trends are growing.", "AI", title="AI Trends in 2024"
        )
        assert result.in_title

    def test_keyword_in_first_sentence(self):
        result = self.analyzer.analyze(
            "AI technology is here to stay.", "AI"
        )
        assert result.in_first_sentence

    def test_keyword_stuffing(self):
        content = "AI " * 50 + "is great."
        assert self.analyzer.check_keyword_stuffing(content, "AI")

    def test_no_stuffing(self):
        content = "Artificial intelligence is a transformative technology that is reshaping how industries work today. Many companies are investing heavily in research and development to stay competitive."
        assert not self.analyzer.check_keyword_stuffing(content, "AI")

    def test_extract_keywords(self):
        keywords = self.analyzer.extract_keywords(
            "Machine learning transforms artificial intelligence applications."
        )
        assert isinstance(keywords, list)
        assert len(keywords) <= 10

    def test_empty_content(self):
        result = self.analyzer.analyze("", "AI")
        assert result.keyword_count == 0

    def test_placement_score_range(self):
        result = self.analyzer.analyze("AI is great.", "AI", title="AI Guide")
        assert 0.0 <= result.keyword_placement_score <= 1.0

    def test_check_count(self):
        self.analyzer.analyze("Test", "test")
        assert self.analyzer.check_count == 1

    def test_to_dict(self):
        result = self.analyzer.analyze("AI is growing.", "AI")
        d = result.to_dict()
        assert "primary_keyword" in d
        assert "keyword_density" in d


# ── HashtagOptimizer Tests ──

class TestHashtagOptimizer:
    def setup_method(self):
        self.optimizer = HashtagOptimizer()

    def test_analyze_with_hashtags(self):
        result = self.optimizer.analyze(
            "Great post #AI #Tech #Innovation", "instagram"
        )
        assert isinstance(result, HashtagResult)
        assert result.count == 3

    def test_analyze_no_hashtags(self):
        result = self.optimizer.analyze("No hashtags here.", "facebook")
        assert result.count == 0

    def test_suggest_hashtags(self):
        tags = self.optimizer.suggest_hashtags(
            "Machine learning is transforming artificial intelligence.", count=3
        )
        assert len(tags) == 3
        assert all(t.startswith("#") for t in tags)

    def test_hashtag_limit_twitter(self):
        tags = " ".join(f"#tag{i}" for i in range(10))
        result = self.optimizer.analyze(tags, "twitter")
        assert any(i.category == "hashtag_limit" for i in result.issues)

    def test_optimal_hashtags_instagram(self):
        result = self.optimizer.analyze("#AI #Tech #Innovation #Data #ML", "instagram")
        assert result.count == 5

    def test_relevance_score(self):
        result = self.optimizer.analyze(
            "AI technology post #AI #Technology", "facebook"
        )
        assert result.relevance_score > 0

    def test_diversity_score(self):
        result = self.optimizer.analyze("#a #bb #ccc #dddd", "facebook")
        assert result.diversity_score > 0

    def test_optimize_removes_excess(self):
        content = "Post " + " ".join(f"#tag{i}" for i in range(10))
        optimized = self.optimizer.optimize(content, "twitter")
        optimized_tags = self.optimizer._extract_hashtags(optimized)
        assert len(optimized_tags) <= 5

    def test_check_count(self):
        self.optimizer.analyze("Test #tag", "facebook")
        assert self.optimizer.check_count == 1


# ── MetadataChecker Tests ──

class TestMetadataChecker:
    def setup_method(self):
        self.checker = MetadataChecker()

    def test_good_title(self):
        score = self.checker.check_title("Top 10 AI Tools for Content Creation")
        assert score >= 0.5

    def test_empty_title(self):
        score = self.checker.check_title("")
        assert score == 0.0

    def test_title_with_power_word(self):
        score = self.checker.check_title("The Ultimate Guide to AI")
        assert score >= 0.5

    def test_good_description(self):
        score = self.checker.check_description(
            "Discover the top AI tools that will transform your content creation workflow in 2024."
        )
        assert score >= 0.5

    def test_empty_description(self):
        score = self.checker.check_description("")
        assert score == 0.0

    def test_full_check(self):
        result = self.checker.full_check(
            title="AI Guide",
            description="A complete guide to artificial intelligence.",
            content="Learn more at https://example.com",
        )
        assert isinstance(result, MetadataResult)
        assert result.has_url

    def test_cta_detection(self):
        result = self.checker.full_check(
            title="Test", description="Test desc",
            content="Learn more about our product today!"
        )
        assert result.has_cta

    def test_no_cta(self):
        result = self.checker.full_check(
            title="Test", description="Test desc",
            content="Information about a topic."
        )
        assert not result.has_cta

    def test_issues_found(self):
        result = self.checker.full_check()
        assert len(result.issues) >= 1

    def test_check_count(self):
        self.checker.full_check(title="Test", description="Test")
        assert self.checker.check_count == 1

    def test_to_dict(self):
        result = self.checker.full_check(title="Test", description="Test")
        d = result.to_dict()
        assert "title_score" in d
        assert "description_score" in d


# ── SocialSearchOptimizer Tests ──

class TestSocialSearchOptimizer:
    def setup_method(self):
        self.optimizer = SocialSearchOptimizer()

    def test_optimize_google(self):
        result = self.optimizer.optimize(
            "# Heading\n\nThis is content about AI.", "google", "AI"
        )
        assert result.platform == "google"
        assert 0.0 <= result.score <= 1.0

    def test_optimize_instagram(self):
        result = self.optimizer.optimize(
            "Post #AI #Tech", "instagram", "AI"
        )
        assert result.platform == "instagram"

    def test_optimize_youtube(self):
        result = self.optimizer.optimize(
            "00:00 Intro\n\nThis is my video about AI tools.", "youtube", "AI"
        )
        assert result.platform == "youtube"

    def test_optimize_unknown_platform(self):
        result = self.optimizer.optimize("Test", "myspace")
        assert result.score == 0.5

    def test_optimize_all(self):
        results = self.optimizer.optimize_all("Test content #AI", "AI")
        assert len(results) >= 5

    def test_get_best_platforms(self):
        results = self.optimizer.optimize_all("Professional content about AI.", "AI")
        best = self.optimizer.get_best_platforms(results)
        assert isinstance(best, list)

    def test_optimization_level(self):
        result = self.optimizer.optimize("Good content #AI", "facebook", "AI")
        assert result.optimization_level in ("excellent", "good", "fair", "poor")

    def test_check_count(self):
        self.optimizer.optimize("Test", "facebook")
        assert self.optimizer.check_count == 1

    def test_to_dict(self):
        result = self.optimizer.optimize("Test #AI", "facebook", "AI")
        d = result.to_dict()
        assert "platform" in d
        assert "score" in d


# ── SEOEngine Tests ──

class TestSEOEngine:
    def setup_method(self):
        self.engine = SEOEngine()

    def test_check_basic(self):
        report = self.engine.check(
            "AI technology is transforming the world. #AI #Tech",
            keyword="AI", title="AI Technology Guide",
            description="Learn about AI technology.", platform="facebook"
        )
        assert isinstance(report, SEODiscoverabilityReport)
        assert report.overall_score >= 0.0

    def test_check_quick(self):
        result = self.engine.check_quick(
            "AI is growing. #AI", keyword="AI"
        )
        assert "overall_score" in result
        assert "keyword_score" in result

    def test_check_multi_platform(self):
        report = self.engine.check_multi_platform(
            "AI technology post. #AI", keyword="AI"
        )
        assert len(report.platform_results) >= 5

    def test_statistics_populated(self):
        report = self.engine.check("Content #AI", keyword="AI")
        assert "check_time_ms" in report.statistics

    def test_check_count(self):
        self.engine.check("Test", keyword="test")
        self.engine.check("Test 2", keyword="test")
        assert self.engine.check_count == 2

    def test_report_to_dict(self):
        report = self.engine.check("Content #AI", keyword="AI")
        d = report.to_dict()
        assert "overall_score" in d
        assert "keyword_result" in d

    def test_compute_overall_no_components(self):
        report = SEODiscoverabilityReport()
        report.compute_overall()
        assert report.overall_score == 0.0

    def test_keyword_in_title_boost(self):
        with_title = self.engine.check(
            "AI is great.", keyword="AI", title="AI Guide"
        )
        without_title = self.engine.check(
            "AI is great.", keyword="AI", title="Technology Guide"
        )
        assert with_title.overall_score >= without_title.overall_score
