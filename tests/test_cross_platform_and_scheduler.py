"""Tests for Twitter Publisher, Cross-Platform Publisher, Content Scheduler."""
from __future__ import annotations
import time
import pytest
from datetime import datetime, timezone


# ══════════════════════════════════════════════════════════════════════
# Twitter Publisher Tests
# ══════════════════════════════════════════════════════════════════════

class TestTwitterPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.twitter.twitter_publisher import TwitterPublisher
        self.pub = TwitterPublisher()

    def test_platform_name(self):
        assert self.pub.get_platform_name() == "twitter"

    def test_capabilities(self):
        caps = self.pub.get_capabilities()
        assert caps.supports_images is True
        assert caps.supports_threads is True
        assert caps.supports_polls is True
        assert caps.max_length == 280
        assert caps.max_images == 4

    def test_validate(self):
        assert self.pub.validate("Hello Twitter!") is True
        assert self.pub.validate("") is False
        assert self.pub.validate("x" * 300) is False

    def test_authenticate_without_token(self):
        assert self.pub.authenticate({}) is False

    def test_publish_without_auth(self):
        result = self.pub.publish("Test tweet")
        assert result.success is False
        assert "Not authenticated" in result.error_message

    def test_edit_without_auth(self):
        result = self.pub.edit("id", "Updated")
        assert result.success is False

    def test_delete_without_auth(self):
        assert self.pub.delete("id") is False

    def test_schedule_not_supported(self):
        result = self.pub.schedule("test", time.time() + 3600)
        assert result.success is False
        assert "Free tier" in result.error_message

    def test_get_stats(self):
        stats = self.pub.get_stats()
        assert stats["platform"] == "twitter"
        assert "authenticated" in stats
        assert "rate_limit_remaining" in stats

    def test_split_into_tweets(self):
        long = "This is a very long tweet. " * 20
        chunks = self.pub._split_into_tweets(long)
        assert len(chunks) > 1
        assert all(len(c) <= 280 for c in chunks)

    def test_split_short_content(self):
        chunks = self.pub._split_into_tweets("Short tweet")
        assert len(chunks) == 1
        assert chunks[0] == "Short tweet"

    def test_calc_engagement(self):
        metrics = {"impression_count": 1000, "like_count": 50, "retweet_count": 20, "reply_count": 10}
        rate = self.pub._calc_engagement(metrics)
        assert rate == 8.0

    def test_calc_engagement_zero(self):
        assert self.pub._calc_engagement({"impression_count": 0}) == 0.0

    def test_publish_result_structure(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import PublishResult
        r = PublishResult(success=True, platform="twitter")
        d = r.to_dict()
        assert d["platform"] == "twitter"


# ══════════════════════════════════════════════════════════════════════
# Cross-Platform Publisher Tests
# ══════════════════════════════════════════════════════════════════════

class TestCrossPlatformPublisher:
    def setup_method(self):
        from layers.layer07_publishing.modules.platform_plugin_manager.cross_platform_publisher import CrossPlatformPublisher
        from layers.layer07_publishing.modules.platform_plugin_manager.mock_publisher import MockPublisher
        self.cross = CrossPlatformPublisher()
        self.cross.register_platform("facebook", MockPublisher("facebook"))
        self.cross.register_platform("twitter", MockPublisher("twitter"))

    def test_register_platform(self):
        assert "facebook" in [c.platform_name for c in self.cross._platforms.values()]

    def test_unregister_platform(self):
        assert self.cross.unregister_platform("facebook") is True
        assert self.cross.unregister_platform("nonexistent") is False

    def test_enable_disable(self):
        self.cross.disable_platform("facebook")
        assert self.cross._platforms["facebook"].enabled is False
        self.cross.enable_platform("facebook")
        assert self.cross._platforms["facebook"].enabled is True

    def test_publish_multi_platform(self):
        result = self.cross.publish(
            topic="AI Trends",
            content="AI is transforming everything!",
            platforms=["facebook", "twitter"],
        )
        assert result.success_count == 2
        assert result.failure_count == 0
        assert "facebook" in result.results
        assert "twitter" in result.results

    def test_format_for_platform_twitter(self):
        formatted = self.cross._format_for_platform("x" * 300, "twitter")
        assert len(formatted) <= 280

    def test_format_with_hashtags(self):
        formatted = self.cross._format_for_platform("Hello", "instagram", hashtags=["AI", "Tech"])
        assert "#AI" in formatted
        assert "#Tech" in formatted

    def test_get_stats(self):
        stats = self.cross.get_stats()
        assert stats["platforms_registered"] == 2
        assert stats["total_publishes"] == 0

    def test_get_capabilities(self):
        caps = self.cross.get_platform_capabilities()
        assert "facebook" in caps
        assert "twitter" in caps

    def test_publish_disabled_platform_skipped(self):
        self.cross.disable_platform("facebook")
        result = self.cross.publish(topic="Test", platforms=["facebook", "twitter"])
        assert result.success_count == 1  # Only twitter

    def test_result_to_dict(self):
        result = self.cross.publish(topic="Test")
        d = result.to_dict()
        assert "results" in d
        assert "platforms_published" in d


# ══════════════════════════════════════════════════════════════════════
# CronExpression Tests
# ══════════════════════════════════════════════════════════════════════

class TestCronExpression:
    def test_daily_preset(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression("daily")
        assert cron.raw == "daily"

    def test_matches_current_time(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression("* * * * *")
        assert cron.matches() is True

    def test_specific_time(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression("0 9 * * *")
        dt = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
        assert cron.matches(dt) is True
        dt2 = datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc)
        assert cron.matches(dt2) is False

    def test_weekdays(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression("0 9 * * 1-5")
        monday = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
        assert cron.matches(monday) is True
        saturday = datetime(2026, 7, 25, 9, 0, tzinfo=timezone.utc)
        assert cron.matches(saturday) is False

    def test_next_run_time(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression("0 9 * * *")
        nxt = cron.next_run_time()
        assert nxt is not None
        assert nxt.hour == 9
        assert nxt.minute == 0

    def test_list_presets(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression()
        presets = cron.list_presets()
        assert "daily" in presets
        assert "hourly" in presets
        assert "weekly" in presets

    def test_invalid_expression(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        with pytest.raises(ValueError):
            CronExpression("99 99 99 99 99")

    def test_every_30_minutes(self):
        from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression
        cron = CronExpression("*/30 * * * *")
        dt = datetime(2026, 7, 20, 10, 30, tzinfo=timezone.utc)
        assert cron.matches(dt) is True
        dt2 = datetime(2026, 7, 20, 10, 15, tzinfo=timezone.utc)
        assert cron.matches(dt2) is False


# ══════════════════════════════════════════════════════════════════════
# ScheduleJob Tests
# ══════════════════════════════════════════════════════════════════════

class TestScheduleJob:
    def test_create_job(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob
        job = ScheduleJob(topic="AI Trends", platforms=["facebook", "twitter"])
        assert job.topic == "AI Trends"
        assert "facebook" in job.platforms

    def test_job_status(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob, JobStatus
        job = ScheduleJob(topic="Test")
        assert job.status == JobStatus.PENDING
        job.mark_running()
        assert job.status == JobStatus.RUNNING
        job.mark_completed()
        assert job.status == JobStatus.COMPLETED
        assert job.run_count == 1

    def test_job_cancel_pause(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob, JobStatus
        job = ScheduleJob(topic="Test")
        job.cancel()
        assert job.status == JobStatus.CANCELLED
        job.resume()
        assert job.status == JobStatus.PENDING

    def test_is_due(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob
        job = ScheduleJob(topic="Test")
        job.next_run = time.time() - 10
        assert job.is_due is True

    def test_is_not_due_future(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob
        job = ScheduleJob(topic="Test")
        job.next_run = time.time() + 3600
        assert job.is_due is False

    def test_success_rate(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob
        job = ScheduleJob(topic="Test")
        job.run_count = 10
        job.fail_count = 2
        assert job.success_rate == 80.0

    def test_to_dict(self):
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob
        job = ScheduleJob(topic="Test")
        d = job.to_dict()
        assert "job_id" in d
        assert d["topic"] == "Test"
        assert "status" in d


# ══════════════════════════════════════════════════════════════════════
# ContentScheduler Tests
# ══════════════════════════════════════════════════════════════════════

class TestContentScheduler:
    def setup_method(self):
        from layers.layer07_publishing.modules.content_scheduler.scheduler import ContentScheduler
        self.scheduler = ContentScheduler()

    def test_add_job(self):
        job = self.scheduler.add_job(topic="AI Trends", cron="daily")
        assert job.topic == "AI Trends"
        assert job.next_run > 0

    def test_remove_job(self):
        job = self.scheduler.add_job(topic="Test")
        assert self.scheduler.remove_job(job.job_id) is True
        assert self.scheduler.get_job(job.job_id) is None

    def test_pause_resume(self):
        job = self.scheduler.add_job(topic="Test")
        assert self.scheduler.pause_job(job.job_id) is True
        from layers.layer07_publishing.modules.content_scheduler.schedule_job import JobStatus
        assert job.status == JobStatus.PAUSED
        self.scheduler.resume_job(job.job_id)
        assert job.status == JobStatus.PENDING

    def test_get_due_jobs(self):
        job = self.scheduler.add_job(topic="Due Test", cron="daily")
        job.next_run = time.time() - 10
        due = self.scheduler.get_due_jobs()
        assert len(due) >= 1

    def test_get_all_jobs(self):
        self.scheduler.add_job(topic="A")
        self.scheduler.add_job(topic="B")
        assert len(self.scheduler.get_all_jobs()) == 2

    def test_get_jobs_by_platform(self):
        self.scheduler.add_job(topic="FB", platforms=["facebook"])
        self.scheduler.add_job(topic="TW", platforms=["twitter"])
        fb_jobs = self.scheduler.get_jobs_by_platform("facebook")
        assert len(fb_jobs) == 1

    def test_execute_job(self):
        job = self.scheduler.add_job(topic="Execute Test")
        job.next_run = time.time() - 10
        result = self.scheduler.execute_job(job)
        assert result["status"] == "completed"
        assert job.run_count == 1

    def test_stats(self):
        self.scheduler.add_job(topic="A")
        self.scheduler.add_job(topic="B")
        stats = self.scheduler.get_stats()
        assert stats["total_jobs"] == 2
        assert stats["pending"] == 2

    def test_events(self):
        job = self.scheduler.add_job(topic="Events Test")
        events = self.scheduler.get_events()
        assert len(events) >= 1
        assert events[0]["event"] == "job_added"

    def test_execution_log(self):
        job = self.scheduler.add_job(topic="Log Test")
        self.scheduler.execute_job(job)
        log = self.scheduler.get_execution_log()
        assert len(log) == 1
        assert log[0]["job_id"] == job.job_id

    def test_to_dict(self):
        self.scheduler.add_job(topic="Dict Test")
        d = self.scheduler.to_dict()
        assert "jobs" in d
        assert "stats" in d

    def test_custom_callback(self):
        def my_callback(job):
            return {"status": "completed", "custom": True}
        self.scheduler.set_execute_callback(my_callback)
        job = self.scheduler.add_job(topic="Callback Test")
        result = self.scheduler.execute_job(job)
        assert result.get("custom") is True
