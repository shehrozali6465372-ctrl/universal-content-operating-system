"""
Tests for EntityLinker — Sprint 2

Covers: linking, normalization, classification, confidence,
        knowledge base lookup, aliases, custom KB, edge cases.
"""
from layers.layer03_intelligence.modules.content_understanding.entity_linker import (
    EntityLinker, LinkedEntity, EntityType,
)


class TestLinkedEntity:
    def test_create(self):
        e = LinkedEntity("OpenAI", EntityType.ORGANIZATION, "OpenAI", 0.99)
        assert e.text == "OpenAI"
        assert e.entity_type == EntityType.ORGANIZATION
        assert e.confidence == 0.99

    def test_to_dict(self):
        e = LinkedEntity("Google", EntityType.ORGANIZATION, "Google (Alphabet)", 0.99, "knowledge_base")
        d = e.to_dict()
        assert d["text"] == "Google"
        assert d["canonical"] == "Google (Alphabet)"
        assert d["source"] == "knowledge_base"

    def test_repr(self):
        e = LinkedEntity("test", EntityType.ORGANIZATION)
        assert "test" in repr(e)


class TestEntityLinkerBasic:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_link_empty(self):
        assert self.linker.link([], "") == []

    def test_link_organization(self):
        entities = [{"text": "OpenAI", "type": "organization"}]
        linked = self.linker.link(entities)
        assert len(linked) == 1
        assert linked[0].canonical == "OpenAI"
        # ORG or TECH depending on KB priority
        assert linked[0].entity_type in (EntityType.ORGANIZATION, EntityType.TECHNOLOGY)
        assert linked[0].confidence >= 0.9

    def test_link_tech(self):
        entities = [{"text": "python", "type": "organization"}]
        linked = self.linker.link(entities)
        assert linked[0].canonical == "Python"
        assert linked[0].entity_type == EntityType.TECHNOLOGY

    def test_link_person(self):
        entities = [{"text": "Elon Musk", "type": "person"}]
        linked = self.linker.link(entities)
        assert linked[0].canonical == "Elon Musk"
        assert linked[0].entity_type == EntityType.PERSON
        assert linked[0].metadata.get("roles")

    def test_link_location(self):
        entities = [{"text": "San Francisco", "type": "location"}]
        linked = self.linker.link(entities)
        assert linked[0].canonical == "San Francisco, CA"
        assert linked[0].entity_type == EntityType.LOCATION

    def test_link_alias(self):
        # "claude" is both an ORG alias (Anthropic) and TECH entry (Claude)
        # TECH takes priority because it's checked first
        entities = [{"text": "msft", "type": "organization"}]
        linked = self.linker.link(entities)
        assert linked[0].canonical == "Microsoft Corporation"
        assert linked[0].source == "alias"

    def test_link_unknown(self):
        entities = [{"text": "xyzzy123", "type": "unknown"}]
        linked = self.linker.link(entities)
        assert linked[0].entity_type == EntityType.UNKNOWN
        assert linked[0].confidence < 0.5

    def test_deduplication(self):
        entities = [
            {"text": "OpenAI", "type": "org"},
            {"text": "OpenAI", "type": "org"},
        ]
        linked = self.linker.link(entities)
        assert len(linked) == 1


class TestNormalize:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_normalize_known(self):
        assert self.linker.normalize("openai") == "OpenAI"
        assert self.linker.normalize("google") == "Google (Alphabet)"
        assert self.linker.normalize("python") == "Python"

    def test_normalize_alias(self):
        assert self.linker.normalize("msft") == "Microsoft Corporation"
        assert self.linker.normalize("alphabet") == "Google (Alphabet)"

    def test_normalize_unknown(self):
        result = self.linker.normalize("SomeNewThing")
        assert "somenew" in result.lower()


class TestClassify:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_classify_org(self):
        assert self.linker.classify("Facebook") == EntityType.ORGANIZATION
        assert self.linker.classify("OpenAI") == EntityType.ORGANIZATION

    def test_classify_tech(self):
        assert self.linker.classify("Python") == EntityType.TECHNOLOGY
        assert self.linker.classify("Bitcoin") == EntityType.TECHNOLOGY
        assert self.linker.classify("GPT-4") == EntityType.TECHNOLOGY

    def test_classify_person(self):
        assert self.linker.classify("Elon Musk") == EntityType.PERSON

    def test_classify_location(self):
        assert self.linker.classify("Tokyo") == EntityType.LOCATION
        assert self.linker.classify("Lahore") == EntityType.LOCATION

    def test_classify_url(self):
        assert self.linker.classify("https://example.com") == EntityType.URL

    def test_classify_email(self):
        assert self.linker.classify("user@example.com") == EntityType.EMAIL

    def test_classify_hashtag(self):
        assert self.linker.classify("#AI") == EntityType.HASHTAG

    def test_classify_mention(self):
        assert self.linker.classify("@john") == EntityType.MENTION

    def test_classify_money(self):
        assert self.linker.classify("$5,000") == EntityType.MONEY

    def test_classify_date(self):
        assert self.linker.classify("2026-07-14") == EntityType.DATE

    def test_classify_person_pattern(self):
        assert self.linker.classify("John Smith") == EntityType.PERSON

    def test_classify_unknown(self):
        assert self.linker.classify("xyzzy") == EntityType.UNKNOWN

    def test_classify_with_context_ceo(self):
        t = self.linker.classify("Tim Cook", "Tim Cook is the CEO of Apple")
        assert t == EntityType.PERSON


class TestConfidence:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_kb_confidence_high(self):
        c = self.linker.confidence("OpenAI")
        assert c >= 0.9

    def test_alias_confidence(self):
        c = self.linker.confidence("gpt")
        assert 0.7 <= c <= 0.95

    def test_url_confidence(self):
        c = self.linker.confidence("https://example.com", EntityType.URL)
        assert c >= 0.9

    def test_pattern_person_confidence(self):
        c = self.linker.confidence("John Smith", EntityType.PERSON)
        assert 0.4 <= c <= 0.7

    def test_unknown_low_confidence(self):
        c = self.linker.confidence("randomword")
        assert c < 0.5


class TestGetEntityLinks:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_single_match(self):
        links = self.linker.get_entity_links("openai")
        assert len(links) >= 1
        assert links[0]["canonical"] == "OpenAI"

    def test_no_match(self):
        links = self.linker.get_entity_links("zzznonexistent")
        assert len(links) == 0

    def test_multiple_matches(self):
        # "gpt" could match as alias in TECH
        links = self.linker.get_entity_links("gpt")
        assert len(links) >= 1
        assert links[0]["confidence"] > 0


class TestAddEntity:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_add_custom_org(self):
        self.linker.add_entity("ORG", "Acme Corp", {
            "canonical": "Acme Corporation",
            "confidence": 0.85,
        })
        links = self.linker.get_entity_links("acme corp")
        assert len(links) >= 1
        assert links[0]["canonical"] == "Acme Corporation"


class TestKBStats:
    def setup_method(self):
        self.linker = EntityLinker()

    def test_stats(self):
        stats = self.linker.get_kb_stats()
        assert stats["ORG"] > 10
        assert stats["TECH"] > 10
        assert stats["PERSON"] >= 5
        assert stats["LOC"] > 5


class TestCustomKB:
    def test_custom_kb(self):
        custom = {
            "ORG": {"myco": {"canonical": "My Company", "confidence": 0.9}},
            "TECH": {},
            "PERSON": {},
            "LOC": {},
        }
        linker = EntityLinker(custom_kb=custom)
        entities = [{"text": "myco", "type": "org"}]
        linked = linker.link(entities)
        assert linked[0].canonical == "My Company"
