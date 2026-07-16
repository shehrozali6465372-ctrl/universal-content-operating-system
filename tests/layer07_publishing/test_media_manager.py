"""Tests for Layer 7 Module 3 — Media Manager."""
from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
from layers.layer07_publishing.modules.media_manager.media_validator import MediaValidator, ValidationIssue
from layers.layer07_publishing.modules.media_manager.media_optimizer import MediaOptimizer, OptimizationResult
from layers.layer07_publishing.modules.media_manager.media_manager import MediaManager


class TestMediaAsset:
    def test_create_image(self):
        a = MediaAsset("photo.jpg", "image")
        assert a.media_type == "image"
        assert a.get_extension() == "jpg"

    def test_is_image(self):
        a = MediaAsset("photo.jpg", "image")
        a.format = "jpg"
        assert a.is_image()

    def test_is_video(self):
        a = MediaAsset("clip.mp4", "video")
        a.format = "mp4"
        assert a.is_video()

    def test_is_document(self):
        a = MediaAsset("report.pdf", "document")
        a.format = "pdf"
        assert a.is_document()

    def test_compute_checksum(self):
        a = MediaAsset("test.jpg")
        cs = a.compute_checksum(b"hello world")
        assert len(cs) == 32

    def test_to_dict(self):
        a = MediaAsset("img.png", "image")
        d = a.to_dict()
        assert "file_name" in d
        assert "media_type" in d


class TestValidationIssue:
    def test_to_dict(self):
        v = ValidationIssue("format", "high", "Bad format", "Use PNG")
        d = v.to_dict()
        assert d["severity"] == "high"


class TestMediaValidator:
    def setup_method(self):
        self.validator = MediaValidator()

    def test_valid_image(self):
        a = MediaAsset("", "image")
        a.format = "jpg"
        a.size_bytes = 1024 * 500  # 500KB
        issues = self.validator.validate(a, "facebook")
        high_issues = [i for i in issues if i.severity in ("high", "critical")]
        assert len(high_issues) == 0

    def test_unsupported_format(self):
        a = MediaAsset("nonexistent.png", "image")
        a.format = "png"
        issues = self.validator.validate(a, "instagram")
        assert any(i.severity == "critical" for i in issues)  # file not found

    def test_missing_alt_text(self):
        a = MediaAsset("photo.jpg", "image")
        a.format = "jpg"
        a.size_bytes = 1000
        issues = self.validator.validate(a, "facebook")
        assert any(i.field == "accessibility" for i in issues)

    def test_image_too_large(self):
        a = MediaAsset("huge.jpg", "image")
        a.format = "jpg"
        a.size_bytes = 20 * 1024 * 1024  # 20MB
        issues = self.validator.validate(a, "facebook")
        assert any(i.field == "size" for i in issues)

    def test_batch_validate(self):
        assets = [MediaAsset("a.jpg", "image"), MediaAsset("b.png", "image")]
        results = self.validator.validate_batch(assets, "facebook")
        assert len(results) == 2

    def test_platform_limits(self):
        assets = [MediaAsset(f"img{i}.jpg", "image") for i in range(15)]
        issues = self.validator.validate_platform_limits(assets, "twitter")
        assert any(i.field == "count" for i in issues)

    def test_check_count(self):
        self.validator.validate(MediaAsset("test.jpg", "image"), "facebook")
        assert self.validator.check_count == 1


class TestMediaOptimizer:
    def setup_method(self):
        self.optimizer = MediaOptimizer()

    def test_optimize_image(self):
        a = MediaAsset("photo.jpg", "image")
        a.width = 2000
        a.height = 1500
        a.size_bytes = 5 * 1024 * 1024
        result = self.optimizer.optimize(a, "facebook")
        assert isinstance(result, OptimizationResult)
        assert result.original_size > 0

    def test_optimize_video(self):
        a = MediaAsset("clip.mp4", "video")
        a.size_bytes = 100 * 1024 * 1024
        result = self.optimizer.optimize(a, "youtube")
        assert result.optimized_size < result.original_size

    def test_optimal_dimensions(self):
        dims = self.optimizer.get_optimal_dimensions("instagram")
        assert "image_width" in dims
        assert dims["image_width"] == 1080

    def test_mark_platform_ready(self):
        a = MediaAsset("photo.jpg", "image")
        self.optimizer.mark_platform_ready(a, "facebook")
        assert a.platform_ready

    def test_batch_optimize(self):
        assets = [MediaAsset(f"img{i}.jpg", "image") for i in range(3)]
        for a in assets:
            a.width = 1920
            a.height = 1080
            a.size_bytes = 3 * 1024 * 1024
        results = self.optimizer.optimize_batch(assets, "facebook")
        assert len(results) == 3


class TestMediaManager:
    def setup_method(self):
        self.manager = MediaManager()

    def test_add_image(self):
        asset = self.manager.add_image("photo.jpg", alt_text="A photo")
        assert asset.file_name == "photo.jpg"
        assert asset.alt_text == "A photo"

    def test_add_video(self):
        asset = self.manager.add_video("clip.mp4", duration=30.0)
        assert asset.is_video()

    def test_add_document(self):
        asset = self.manager.add_document("report.pdf")
        assert asset.is_document()

    def test_validate(self):
        asset = self.manager.add_image("photo.jpg")
        issues = self.manager.validate(asset.asset_id, "facebook")
        assert isinstance(issues, list)

    def test_optimize(self):
        asset = self.manager.add_image("photo.jpg")
        asset.width = 2000
        asset.height = 1500
        asset.size_bytes = 5 * 1024 * 1024
        result = self.manager.optimize(asset.asset_id, "facebook")
        assert result is not None

    def test_prepare_for_platform(self):
        asset = self.manager.add_image("photo.jpg")
        asset.width = 2000
        asset.height = 1500
        asset.size_bytes = 5 * 1024 * 1024
        result = self.manager.prepare_for_platform(asset.asset_id, "facebook")
        assert "valid" in result
        assert "optimization" in result

    def test_find_duplicate(self):
        asset1 = self.manager.add_image("a.jpg")
        asset1.checksum = "abc123"
        asset2 = self.manager.add_image("b.jpg")
        asset2.checksum = "abc123"
        dup = self.manager.find_duplicate(asset2.asset_id)
        assert dup == asset1.asset_id

    def test_no_duplicate(self):
        asset = self.manager.add_image("unique.jpg")
        assert self.manager.find_duplicate(asset.asset_id) is None

    def test_get_asset(self):
        asset = self.manager.add_image("photo.jpg")
        found = self.manager.get_asset(asset.asset_id)
        assert found is not None

    def test_list_assets(self):
        self.manager.add_image("a.jpg")
        self.manager.add_video("b.mp4")
        assert len(self.manager.list_assets()) == 2

    def test_remove_asset(self):
        asset = self.manager.add_image("remove.jpg")
        assert self.manager.remove_asset(asset.asset_id)
        assert self.manager.get_asset(asset.asset_id) is None

    def test_statistics(self):
        self.manager.add_image("a.jpg")
        self.manager.add_image("b.png")
        self.manager.add_video("c.mp4")
        stats = self.manager.get_statistics()
        assert stats["total_assets"] == 3
        assert stats["images"] == 2
        assert stats["videos"] == 1

    def test_manage_count(self):
        self.manager.add_image("a.jpg")
        self.manager.add_video("b.mp4")
        assert self.manager.manage_count == 2

    def test_validate_nonexistent(self):
        issues = self.manager.validate("nonexistent", "facebook")
        assert any(i.severity == "critical" for i in issues)
