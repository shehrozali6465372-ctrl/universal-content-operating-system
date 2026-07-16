"""Tests for Layer 6 Module 1 — Content Quality Analyzer."""
from layers.layer06_quality.modules.content_quality_analyzer.grammar_checker import GrammarChecker
from layers.layer06_quality.modules.content_quality_analyzer.readability_analyzer import ReadabilityAnalyzer
from layers.layer06_quality.modules.content_quality_analyzer.clarity_analyzer import ClarityAnalyzer
from layers.layer06_quality.modules.content_quality_analyzer.structure_analyzer import StructureAnalyzer
from layers.layer06_quality.modules.content_quality_analyzer.engagement_scorer import EngagementScorer
from layers.layer06_quality.modules.content_quality_analyzer.quality_analyzer import ContentQualityAnalyzer, QualityReport


class TestGrammarChecker:
    def setup_method(self):
        self.gc = GrammarChecker()

    def test_clean_text(self):
        issues = self.gc.check("This is a well written sentence.")
        # May find minor issues but no major ones
        assert isinstance(issues, list)

    def test_your_vs_youre(self):
        issues = self.gc.check("Your going home now!")
        assert any(i.rule == "your_youre" for i in issues)

    def test_its_vs_itis(self):
        issues = self.gc.check("Its going to rain.")
        assert any(i.rule == "its_itis" for i in issues)

    def test_double_space(self):
        issues = self.gc.check("Hello  world")
        assert any(i.rule == "double_space" for i in issues)

    def test_repeated_word(self):
        issues = self.gc.check("This is is a test")
        assert any(i.rule == "repeated_word" for i in issues)

    def test_check_batch(self):
        results = self.gc.check_batch(["Hello world", "Test text"])
        assert len(results) == 2

    def test_severity(self):
        issues = self.gc.check("Your going home now!")
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) >= 1

    def test_to_dict(self):
        issues = self.gc.check("Your good")
        if issues:
            d = issues[0].to_dict()
            assert "rule" in d
            assert "message" in d

    def test_check_count(self):
        self.gc.check("A")
        assert self.gc.check_count == 1


class TestReadabilityAnalyzer:
    def setup_method(self):
        self.ra = ReadabilityAnalyzer()

    def test_easy_text(self):
        r = self.ra.analyze("The cat sat on the mat. It was a sunny day. The cat was happy.")
        assert r.readability_level == "easy"
        assert r.flesch_score > 60

    def test_complex_text(self):
        r = self.ra.analyze("The implementation of sophisticated algorithms necessitates comprehensive understanding of computational complexity theory.")
        assert r.flesch_score < 80

    def test_word_count(self):
        r = self.ra.analyze("One two three four five")
        assert r.word_count == 5

    def test_sentence_count(self):
        r = self.ra.analyze("First sentence. Second sentence. Third sentence.")
        assert r.sentence_count == 3

    def test_reading_time(self):
        r = self.ra.analyze("word " * 200)
        assert r.reading_time_seconds > 40

    def test_short_content(self):
        r = self.ra.analyze("Hi")
        assert any("short" in i.lower() for i in r.issues)

    def test_long_sentences(self):
        r = self.ra.analyze("This is a very long sentence that goes on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on.")
        assert any("long" in i.lower() for i in r.issues)

    def test_to_dict(self):
        r = self.ra.analyze("Test text with enough words to analyze properly.")
        d = r.to_dict()
        assert "flesch_score" in d
        assert "readability_level" in d


class TestClarityAnalyzer:
    def setup_method(self):
        self.ca = ClarityAnalyzer()

    def test_clear_text(self):
        r = self.ca.analyze("AI transforms industries. Companies adopt new technology. Growth accelerates.")
        assert r.clarity_score > 0.5

    def test_filler_words(self):
        r = self.ca.analyze("Like basically it is very really actually quite good stuff things")
        assert r.filler_count > 0

    def test_weak_words(self):
        r = self.ca.analyze("The thing was very nice and good and big and small and bad and things and stuff")
        assert r.weak_word_count > 0

    def test_paragraph_length(self):
        text = " ".join(["word"] * 200)
        r = self.ca.analyze(text)
        assert r.avg_paragraph_length > 0

    def test_transitions(self):
        r = self.ca.analyze("First however therefore additionally furthermore")
        assert r.transition_score > 0

    def test_to_dict(self):
        r = self.ca.analyze("Test text")
        d = r.to_dict()
        assert "clarity_score" in d
        assert "issues" in d


class TestStructureAnalyzer:
    def setup_method(self):
        self.sa = StructureAnalyzer()

    def test_has_hook(self):
        r = self.sa.analyze("Did you know AI is growing?")
        assert r.has_hook is True

    def test_has_cta(self):
        r = self.sa.analyze("Great content! Comment below and let us know what you think.")
        assert r.has_cta is True

    def test_has_conclusion(self):
        r = self.sa.analyze("Content here.\n\nIn conclusion, this is important.")
        assert r.has_conclusion is True

    def test_paragraph_count(self):
        r = self.sa.analyze("Para one.\n\nPara two.\n\nPara three.")
        assert r.paragraph_count == 3

    def test_heading_detection(self):
        r = self.sa.analyze("## Title\n\nContent here.")
        assert r.heading_count == 1
        assert r.structure_type == "article"

    def test_list_detection(self):
        r = self.sa.analyze("- Item one\n- Item two\n- Item three")
        assert r.list_detected is True
        assert r.structure_type == "listicle"

    def test_structure_score(self):
        r = self.sa.analyze("Hook question?\n\nBody content.\n\nComment below!")
        assert r.structure_score > 0.7

    def test_no_cta_warning(self):
        r = self.sa.analyze("This is general content without any engagement words.")
        assert any("cta" in i.lower() for i in r.issues)

    def test_to_dict(self):
        r = self.sa.analyze("Test content")
        d = r.to_dict()
        assert "has_hook" in d
        assert "structure_type" in d


class TestEngagementScorer:
    def setup_method(self):
        self.es = EngagementScorer()

    def test_high_engagement(self):
        r = self.es.score("Did you know? This amazing secret will transform your life! Share now!")
        assert r.engagement_score > 0.5

    def test_question_boosts(self):
        r = self.es.score("What do you think about AI?")
        assert r.question_detected is True
        assert r.comment_probability >= 0.5

    def test_emotional_words(self):
        r = self.es.score("This is incredible and shocking and amazing news!")
        assert r.emotional_words >= 2

    def test_power_words(self):
        r = self.es.score("You must discover this proven secret now!")
        assert r.power_words >= 2

    def test_hook_strength(self):
        r = self.es.score("Discover the secret behind AI success!")
        assert r.hook_strength > 0.5

    def test_urgency(self):
        r = self.es.score("buy now hurry limited today exclusive offer now urgent")
        assert r.urgency_score > 0

    def test_shareability(self):
        r = self.es.score("This incredible and shocking news will amaze you!")
        assert r.shareability >= 0.6

    def test_to_dict(self):
        r = self.es.score("Test engagement text with questions?")
        d = r.to_dict()
        assert "engagement_score" in d
        assert "shareability" in d


class TestContentQualityAnalyzer:
    def setup_method(self):
        self.cqa = ContentQualityAnalyzer()

    def test_analyze_good_content(self):
        text = "Did you know AI is transforming industries? Companies are adopting new technology. In conclusion, the future is bright. Comment below with your thoughts!"
        report = self.cqa.analyze(text)
        assert isinstance(report, QualityReport)
        assert report.overall_score > 0
        assert report.grade != ""

    def test_analyze_bad_content(self):
        text = "Your going home now and its important and its going to be good"
        report = self.cqa.analyze(text)
        assert len(report.grammar_issues) > 0

    def test_analyze_empty(self):
        report = self.cqa.analyze("")
        assert report.overall_score >= 0

    def test_analyze_has_all_components(self):
        text = "AI is great. It helps businesses grow. Comment and share your views!"
        report = self.cqa.analyze(text)
        assert report.readability is not None
        assert report.clarity is not None
        assert report.structure is not None
        assert report.engagement is not None

    def test_pass_recommendation(self):
        text = "Did you know? This amazing discovery will change everything! Companies love it. Share with friends! In conclusion, it's revolutionary."
        report = self.cqa.analyze(text)
        assert report.pass_recommendation in ("READY TO PUBLISH", "NEEDS IMPROVEMENT", "REVISION REQUIRED")

    def test_to_dict(self):
        text = "Good content with proper structure and engagement."
        report = self.cqa.analyze(text)
        d = report.to_dict()
        assert "overall_score" in d
        assert "grade" in d
        assert "pass_recommendation" in d

    def test_platform_metadata(self):
        report = self.cqa.analyze("Test content", platform="instagram")
        assert report.metadata.get("platform") == "instagram"

    def test_analysis_count(self):
        self.cqa.analyze("A")
        assert self.cqa.analysis_count == 1

    def test_issues_collected(self):
        text = "Your going tommorow."
        report = self.cqa.analyze(text)
        assert isinstance(report.issues, list)
