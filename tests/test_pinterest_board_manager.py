"""Comprehensive tests for Layer 23 — Module 3: Pinterest Board Manager."""
from __future__ import annotations
import pytest

from layers.layer23_website_manager.pinterest_board_manager.pinterest_board_manager import (
    PinterestBoardManager, get_board_manager,
)
from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import (
    PinterestBoard, BoardStatus,
)
from layers.layer23_website_manager.pinterest_board_manager.models.board_performance import BoardPerformance
from layers.layer23_website_manager.pinterest_board_manager.models.board_hierarchy import BoardNode
from layers.layer23_website_manager.pinterest_board_manager.exceptions import (
    BoardNotFoundError, DuplicateBoardError, BoardLimitError,
    BoardMappingError, BoardPermissionError,
)


# ═══════════════════════════════════════════════════════════════════
# PinterestBoard Model
# ═══════════════════════════════════════════════════════════════════

class TestPinterestBoard:
    def test_default_board(self):
        b = PinterestBoard()
        assert b.status == BoardStatus.PENDING
        assert b.board_id is not None
        assert b.is_empty is True

    def test_board_with_values(self):
        b = PinterestBoard(
            account_id="acc1", board_name="Home Decor Ideas",
            niche="home_decor", pin_count=15,
        )
        assert b.board_name == "Home Decor Ideas"
        assert b.account_id == "acc1"
        assert b.pin_count == 15
        assert b.is_empty is False

    def test_is_active(self):
        b = PinterestBoard(status=BoardStatus.ACTIVE)
        assert b.is_active is True
        b.is_archived = True
        assert b.is_active is False

    def test_to_dict(self):
        b = PinterestBoard(board_name="Test Board", niche="fashion")
        d = b.to_dict()
        assert d["board_name"] == "Test Board"
        assert d["niche"] == "fashion"
        assert "status" in d


# ═══════════════════════════════════════════════════════════════════
# BoardPerformance Model
# ═══════════════════════════════════════════════════════════════════

class TestBoardPerformance:
    def test_default(self):
        p = BoardPerformance()
        assert p.engagement_rate == 0.0

    def test_engagement_rate(self):
        p = BoardPerformance(impressions=1000, saves=100, clicks=50, closeups=20)
        assert p.save_rate == 10.0
        assert p.click_rate == 5.0
        assert p.engagement_rate == 17.0

    def test_aggregate(self):
        p1 = BoardPerformance(impressions=500, saves=50, clicks=20)
        p2 = BoardPerformance(impressions=500, saves=30, clicks=10)
        agg = BoardPerformance.aggregate([p1, p2])
        assert agg.impressions == 1000
        assert agg.saves == 80
        assert agg.clicks == 30


# ═══════════════════════════════════════════════════════════════════
# BoardNode (Hierarchy)
# ═══════════════════════════════════════════════════════════════════

class TestBoardNode:
    def test_tree_structure(self):
        root = BoardNode(board_id="root", board_name="Home")
        child = BoardNode(board_id="c1", board_name="Bedroom")
        root.add_child(child)
        assert root.children[0].board_id == "c1"
        assert root.children[0].depth == 1

    def test_flatten(self):
        root = BoardNode(board_id="r", board_name="Root", pin_count=5)
        c1 = BoardNode(board_id="c1", board_name="C1", pin_count=3)
        c2 = BoardNode(board_id="c2", board_name="C2", pin_count=2)
        root.add_child(c1)
        root.add_child(c2)
        flat = root.flatten()
        assert len(flat) == 3
        assert root.total_pins_recursive() == 10


# ═══════════════════════════════════════════════════════════════════
# BoardRegistry
# ═══════════════════════════════════════════════════════════════════

class TestBoardRegistry:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_create_board(self):
        board = self.bm.create_board("acc1", "Home Decor Ideas", niche="home_decor")
        assert board.board_name == "Home Decor Ideas"
        assert board.niche == "home_decor"
        assert board.status == BoardStatus.ACTIVE

    def test_create_board_with_full_details(self):
        board = self.bm.create_board(
            "acc1", "Modern Kitchen", description="Best kitchen ideas",
            niche="home_decor", category="kitchen",
            keywords=["modern kitchen", "kitchen design"],
        )
        assert "Best kitchen ideas" in board.board_description
        assert "modern kitchen" in board.keywords

    def test_create_duplicate_board(self):
        self.bm.create_board("acc1", "Unique Board")
        with pytest.raises(DuplicateBoardError):
            self.bm.create_board("acc1", "Unique Board")

    def test_get_board(self):
        created = self.bm.create_board("acc1", "Get Test")
        fetched = self.bm.get_board(created.board_id)
        assert fetched is not None
        assert fetched.board_name == "Get Test"

    def test_update_board(self):
        board = self.bm.create_board("acc1", "Update Me")
        updated = self.bm.update_board(board.board_id, board_name="Updated Name")
        assert updated is not None
        assert updated.board_name == "Updated Name"

    def test_delete_board(self):
        board = self.bm.create_board("acc1", "Delete Me")
        assert self.bm.delete_board(board.board_id) is True
        assert self.bm.get_board(board.board_id) is None

    def test_archive_restore_board(self):
        board = self.bm.create_board("acc1", "Archive Me")
        assert self.bm.archive_board(board.board_id) is True
        assert board.is_archived is True
        assert self.bm.restore_board(board.board_id) is True
        assert board.is_archived is False


class TestCreator:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_ai_board_creation(self):
        board = self.bm.create_board_ai("acc1", "Modern Bedroom", niche="home_decor")
        assert board.board_name is not None
        assert "Bedroom" in board.board_name or "Modern" in board.board_name
        assert board.is_ai_created is True
        assert board.board_description is not None

    def test_ai_board_creation_tech(self):
        board = self.bm.create_board_ai("acc1", "AI Technology", niche="tech")
        assert board.is_ai_created is True
        assert board.niche == "tech"

    def test_generate_board_name(self):
        name = self.bm.creator.generate_board_name("Minimalist", "home_decor")
        assert "Minimalist" in name

    def test_generate_keywords(self):
        keywords = self.bm.creator.generate_keywords("bedroom design", "home_decor")
        assert len(keywords) >= 2
        assert "bedroom design" in keywords


class TestSEOManager:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_seo_optimization_on_create(self):
        board = self.bm.create_board("acc1", "Kitchen Ideas", niche="home_decor",
                                      keywords=["kitchen", "design"])
        assert board.seo_score > 0
        assert board.hashtags is not None

    def test_optimize_board_seo(self):
        board = self.bm.create_board("acc1", "Test SEO")
        result = self.bm.optimize_board_seo(board.board_id)
        assert result is not None
        assert result["seo_score"] >= 0
        assert result["optimized"] is True

    def test_generate_hashtags(self):
        tags = self.bm.seo.generate_hashtags(["kitchen", "design"], "home_decor")
        assert len(tags) > 0
        assert all(t.startswith("#") for t in tags)

    def test_optimize_title(self):
        optimized = self.bm.seo.optimize_title("Kitchen", "home_decor", ["kitchen ideas"])
        assert "Inspiration" in optimized or len(optimized) >= len("Kitchen")

    def test_recalculate_scores(self):
        self.bm.create_board("acc1", "Board A")
        self.bm.create_board("acc1", "Board B")
        count = self.bm.recalculate_seo_scores("acc1")
        assert count >= 2


class TestMapping:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_map_topic_to_board(self):
        self.bm.create_board("acc1", "Modern Bedroom Ideas", niche="home_decor")
        board = self.bm.map_topic_to_board("Small bedroom design ideas", "home_decor")
        assert board is not None
        assert board.niche == "home_decor"

    def test_map_topic_no_match(self):
        self.bm.create_board("acc1", "Fashion Trends", niche="fashion",
                              keywords=[], description="")
        # Clear auto-added keywords
        board = self.bm.get_boards_for_account("acc1")[0]
        board.keywords = ["fashion", "style"]
        board.niche = "fashion"
        board = self.bm.map_topic_to_board("Quantum physics research paper", "science")
        assert board is None


class TestHierarchy:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_board_tree_structure(self):
        home = self.bm.create_board("acc1", "Home Decor", niche="home_decor")
        bedroom = self.bm.create_board("acc1", "Bedroom Ideas", niche="home_decor",
                                        parent_board_id=home.board_id)
        kitchen = self.bm.create_board("acc1", "Kitchen Ideas", niche="home_decor",
                                        parent_board_id=home.board_id)
        tree = self.bm.get_board_tree("acc1")
        assert len(tree) == 1
        assert tree[0].board_name == "Home Decor" or tree[0].board_name == "Home Decor"
        children_names = [c.board_name for c in tree[0].children]
        assert "Bedroom Ideas" in children_names
        assert "Kitchen Ideas" in children_names

    def test_set_board_parent(self):
        parent = self.bm.create_board("acc1", "Parent Board")
        child = self.bm.create_board("acc1", "Child Board")
        assert self.bm.set_board_parent(child.board_id, parent.board_id) is True
        assert child.parent_board_id == parent.board_id
        assert child.board_depth == parent.board_depth + 1


class TestAnalytics:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_record_performance(self):
        board = self.bm.create_board("acc1", "Analytics Test")
        result = self.bm.record_performance(board.board_id, impressions=5000, saves=200, clicks=80)
        assert result["impressions"] == 5000
        assert result["saves"] == 200
        assert board.total_impressions == 5000

    def test_simulate_daily(self):
        board = self.bm.create_board("acc1", "Simulation Test")
        result = self.bm.simulate_daily_performance(board.board_id)
        assert result["impressions"] > 0
        assert board.total_impressions > 0

    def test_get_top_boards(self):
        for i in range(5):
            b = self.bm.create_board("acc1", f"Board {i}")
            b.engagement_rate = i * 20
        tops = self.bm.get_top_boards("acc1", top_k=3)
        assert len(tops) <= 3
        assert tops[0].engagement_rate >= tops[-1].engagement_rate


class TestHealth:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_healthy_board(self):
        board = self.bm.create_board("acc1", "Healthy Board", description="A complete description with enough detail for SEO.",
                                      keywords=["kw1", "kw2", "kw3"])
        result = self.bm.check_board_health(board.board_id)
        assert result["health_score"] >= 50

    def test_unhealthy_empty_board(self):
        board = self.bm.create_board("acc1", "Empty Board")
        board.board_name = ""  # Clear name for health issue
        board.keywords = []  # Clear keywords
        board.hashtags = []  # Clear hashtags
        result = self.bm.check_board_health(board.board_id)
        assert result["issue_count"] > 0

    def test_check_all_health(self):
        self.bm.create_board("acc1", "Board A")
        self.bm.create_board("acc1", "Board B")
        report = self.bm.check_all_health("acc1")
        assert report["total_checked"] == 2
        assert report["overall_score"] >= 0


class TestRecommendation:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_recommend_new_boards(self):
        self.bm.create_board("acc1", "Modern Bedroom Ideas", niche="home_decor")
        recs = self.bm.recommend_new_boards("home_decor", "acc1")
        assert len(recs) > 0
        assert recs[0]["niche"] == "home_decor"

    def test_detect_gaps(self):
        self.bm.create_board("acc1", "Bedroom Ideas", niche="home_decor")
        gaps = self.bm.detect_board_gaps("home_decor", "acc1")
        assert len(gaps) > 0
        assert all("Minimalist" in g["suggested_board"] or g["gap_keyword"] != "Minimalist" for g in gaps)


class TestPermissions:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_check_edit_permission(self):
        board = self.bm.create_board("acc1", "Perm Board")
        assert self.bm.permissions.check_permission(board, "owner", "edit") is True

    def test_grant_revoke_permission(self):
        board = self.bm.create_board("acc1", "Access Board")
        assert self.bm.permissions.grant_permission(board, "editor1", "edit") is True
        assert "editor1" in board.can_edit
        assert self.bm.permissions.revoke_permission(board, "editor1", "edit") is True
        assert "editor1" not in board.can_edit


class TestMultiAccount:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_boards_across_accounts(self):
        self.bm.create_board("acc1", "Board in Acc1")
        self.bm.create_board("acc2", "Board in Acc2")
        assert len(self.bm.get_boards_for_account("acc1")) == 1
        assert len(self.bm.get_boards_for_account("acc2")) == 1

    def test_get_all_boards(self):
        self.bm.create_board("acc1", "Board 1")
        self.bm.create_board("acc2", "Board 2")
        self.bm.create_board("acc2", "Board 3")
        all_boards = self.bm.get_all_boards()
        assert len(all_boards) == 3

    def test_boards_by_niche(self):
        self.bm.create_board("acc1", "Fashion 1", niche="fashion")
        self.bm.create_board("acc2", "Fashion 2", niche="fashion")
        self.bm.create_board("acc1", "Tech 1", niche="tech")
        fashion = self.bm.get_boards_by_niche("fashion")
        assert len(fashion) == 2


class TestStatus:
    def setup_method(self):
        self.bm = PinterestBoardManager()
        self.bm.create_board("acc1", "Status Board", niche="tech")

    def test_get_status(self):
        status = self.bm.get_status()
        assert status["module"] == "Pinterest Board Manager (Layer 23 / Module 3)"
        assert status["version"] == "1.0.0"
        assert "boards" in status
        assert "health" in status
        assert "seo" in status

    def test_board_stats(self):
        status = self.bm.get_status()
        assert status["boards"]["total_boards"] >= 1


class TestErrorHandling:
    def setup_method(self):
        self.bm = PinterestBoardManager()

    def test_get_nonexistent(self):
        assert self.bm.get_board("nonexistent") is None

    def test_delete_nonexistent(self):
        assert self.bm.delete_board("nonexistent") is False

    def test_update_nonexistent(self):
        assert self.bm.update_board("nonexistent", board_name="X") is None

    def test_optimize_nonexistent(self):
        assert self.bm.optimize_board_seo("nonexistent") is None

    def test_archive_nonexistent(self):
        assert self.bm.archive_board("nonexistent") is False


class TestSingleton:
    def test_get_board_manager(self):
        bm1 = get_board_manager()
        bm2 = get_board_manager()
        assert bm1 is bm2


class TestBoardLimit:
    def test_board_limit(self):
        bm = PinterestBoardManager()
        bm.registry._max_boards_per_account = 2
        bm.create_board("acc1", "Board 1")
        bm.create_board("acc1", "Board 2")
        with pytest.raises(BoardLimitError):
            bm.create_board("acc1", "Board 3")


class TestCreatorAllNiches:
    def test_all_niches_can_create(self):
        bm = PinterestBoardManager()
        niches = ["home_decor", "fashion", "beauty", "food", "tech", "fitness", "travel", "finance", "DIY"]
        for niche in niches:
            board = bm.create_board_ai("acc1", f"{niche} idea", niche=niche)
            assert board.board_name is not None
            assert len(board.keywords) >= 1
