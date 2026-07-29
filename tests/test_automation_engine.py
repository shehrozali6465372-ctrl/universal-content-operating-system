"""Comprehensive tests for Layer 23 — Module 12: Automation Engine."""
from __future__ import annotations
import time
import pytest
from typing import Any, Dict, List

from layers.layer23_website_manager.automation_engine.automation_engine import (
    AutomationEngine, get_automation_engine,
)
from layers.layer23_website_manager.automation_engine.models.automation_models import (
    AutomationConfig, Trigger, TriggerType, Rule, RuleAction, PipelineTask,
    Worker, CronSchedule, RetryPolicy, ScalingPolicy, SafetyPolicy,
    AutomationResult, AutomationStatus, ExecutionRecord,
)
from layers.layer23_website_manager.automation_engine.automation.automation_manager import (
    AutomationManager,
)
from layers.layer23_website_manager.automation_engine.triggers.trigger_engine import (
    TriggerEngine,
)
from layers.layer23_website_manager.automation_engine.rules.rule_engine import (
    RuleEngine,
)
from layers.layer23_website_manager.automation_engine.pipeline.automation_pipeline import (
    AutomationPipeline,
)
from layers.layer23_website_manager.automation_engine.workers.worker_manager import (
    WorkerManager,
)
from layers.layer23_website_manager.automation_engine.cron.cron_manager import (
    CronManager,
)
from layers.layer23_website_manager.automation_engine.retry.smart_retry_engine import (
    SmartRetryEngine,
)
from layers.layer23_website_manager.automation_engine.scaling.auto_scaling_engine import (
    AutoScalingEngine,
)
from layers.layer23_website_manager.automation_engine.optimizer.workflow_optimizer import (
    WorkflowOptimizer,
)
from layers.layer23_website_manager.automation_engine.safety.safety_manager import (
    SafetyManager,
)
from layers.layer23_website_manager.automation_engine.monitoring.automation_monitor import (
    AutomationMonitor,
)
from layers.layer23_website_manager.automation_engine.recovery.emergency_recovery import (
    EmergencyRecovery,
)
from layers.layer23_website_manager.automation_engine.api.automation_api import (
    AutomationAPI,
)
from layers.layer23_website_manager.automation_engine.exceptions import (
    AutomationError, TriggerError, RuleEngineError, WorkerError,
    ScalingError, SafetyError, RecoveryError, PipelineError,
    CronError, RetryError, OptimizationError, MonitoringError,
)


# ══════════════════════════════════════════════════════════════════════
# Models Tests
# ══════════════════════════════════════════════════════════════════════

class TestModels:
    def test_trigger(self):
        t = Trigger("Daily Check", TriggerType.TIME, {"interval": 3600})
        assert t.trigger_id.startswith("trg_")
        assert t.name == "Daily Check"
        assert t.can_fire is True
        t.fire()
        assert t.fire_count == 1
        assert t.last_fired is not None
        d = t.to_dict()
        assert d["name"] == "Daily Check"

    def test_trigger_cooldown(self):
        t = Trigger("Fast", TriggerType.TIME, cooldown_seconds=999999)
        t.fire()
        assert t.can_fire is False

    def test_trigger_disabled(self):
        t = Trigger("Disabled", TriggerType.TIME)
        t.enabled = False
        assert t.can_fire is False

    def test_rule_action(self):
        a = RuleAction("generate_content", {"topic": "AI"}, "writing")
        assert a.action_id.startswith("act_")
        assert a.action_type == "generate_content"

    def test_rule(self):
        r = Rule("Traffic Rule", "traffic > 100", priority=50)
        assert r.rule_id.startswith("rule_")
        assert r.enabled is True
        d = r.to_dict()
        assert d["name"] == "Traffic Rule"

    def test_pipeline_task(self):
        pt = PipelineTask("Research", "research", "gather", order=1)
        assert pt.task_id.startswith("pt_")
        assert pt.status == "pending"
        d = pt.to_dict()
        assert d["name"] == "Research"

    def test_pipeline_task_with_deps(self):
        pt = PipelineTask("Write", "writing", "generate", order=2,
                          depends_on=["prev_task"], timeout=600)
        assert "prev_task" in pt.depends_on

    def test_worker(self):
        w = Worker("test-worker")
        assert w.worker_id.startswith("wrk_")
        assert w.status == "idle"
        assert w.is_busy is False
        d = w.to_dict()
        assert d["name"] == "test-worker"

    def test_cron_schedule(self):
        cs = CronSchedule("Daily Pub", "daily")
        assert cs.schedule_id.startswith("cron_")
        assert cs.enabled is True
        d = cs.to_dict()
        assert d["name"] == "Daily Pub"

    def test_retry_policy(self):
        rp = RetryPolicy("custom", max_retries=5, base_delay=10.0)
        assert rp.policy_id.startswith("rp_")
        assert rp.max_retries == 5

    def test_scaling_policy(self):
        sp = ScalingPolicy("aggressive", min_workers=5, max_workers=50)
        assert sp.policy_id.startswith("sp_")
        assert sp.min_workers == 5

    def test_safety_policy(self):
        sp = SafetyPolicy("strict", max_daily_executions=500,
                          blocked_hours=[0, 1, 2, 3])
        assert sp.policy_id.startswith("sf_")
        assert 0 in sp.blocked_hours

    def test_automation_config(self):
        cfg = AutomationConfig()
        assert cfg.config_id.startswith("cfg_")
        assert len(cfg.triggers) == 0

    def test_automation_result(self):
        ar = AutomationResult(workflow_id="wf_1", trigger="test")
        assert ar.result_id.startswith("ar_")
        assert ar.status == "running"
        ar.complete("completed")
        assert ar.status == "completed"
        assert ar.duration_ms > 0
        d = ar.to_dict()
        assert d["status"] == "completed"

    def test_execution_record(self):
        er = ExecutionRecord(trigger="cron", workflow_id="wf_1")
        assert er.record_id.startswith("er_")
        d = er.to_dict()
        assert d["trigger"] == "cron"


# ══════════════════════════════════════════════════════════════════════
# AutomationManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestAutomationManager:
    def setup_method(self):
        self.mgr = AutomationManager()

    def test_initial_status(self):
        assert self.mgr.status == AutomationStatus.IDLE

    def test_start(self):
        r = self.mgr.start()
        assert r["status"] == "started"
        assert self.mgr.status == AutomationStatus.RUNNING

    def test_stop(self):
        self.mgr.start()
        r = self.mgr.stop()
        assert r["status"] == "stopped"

    def test_pause_resume(self):
        self.mgr.start()
        assert self.mgr.pause()["status"] == "paused"
        assert self.mgr.status == AutomationStatus.PAUSED
        assert self.mgr.resume()["status"] == "resumed"
        assert self.mgr.status == AutomationStatus.RUNNING

    def test_pause_not_running(self):
        assert self.mgr.pause()["status"] == "not_running"

    def test_resume_not_paused(self):
        assert self.mgr.resume()["status"] == "not_paused"

    def test_restart(self):
        self.mgr.start()
        r = self.mgr.restart()
        assert r["status"] == "started"

    def test_uptime(self):
        self.mgr.start()
        time.sleep(0.01)
        assert self.mgr.uptime > 0

    def test_record_execution(self):
        self.mgr.record_execution(True)
        self.mgr.record_execution(False)
        stats = self.mgr.get_stats()
        assert stats["total_executions"] == 2
        assert stats["total_errors"] == 1


# ══════════════════════════════════════════════════════════════════════
# TriggerEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestTriggerEngine:
    def setup_method(self):
        self.te = TriggerEngine()

    def test_register_trigger(self):
        t = self.te.register_trigger("Test", TriggerType.TIME, {"i": 3600})
        assert len(self.te.get_all_triggers()) == 1
        assert t.name == "Test"

    def test_unregister_trigger(self):
        t = self.te.register_trigger("T", TriggerType.TIME)
        assert self.te.unregister_trigger(t.trigger_id) is True
        assert self.te.unregister_trigger("bad") is False

    def test_get_trigger(self):
        t = self.te.register_trigger("T", TriggerType.TIME)
        assert self.te.get_trigger(t.trigger_id) is t
        assert self.te.get_trigger("bad") is None

    def test_enable_disable(self):
        t = self.te.register_trigger("T", TriggerType.TIME)
        assert self.te.disable_trigger(t.trigger_id) is True
        assert t.enabled is False
        assert self.te.enable_trigger(t.trigger_id) is True
        assert t.enabled is True
        assert self.te.disable_trigger("bad") is False

    def test_evaluate(self):
        t = self.te.register_trigger("T", TriggerType.TIME, cooldown=0)
        assert self.te.evaluate(t.trigger_id) is True
        assert t.fire_count == 1

    def test_evaluate_wrong_id(self):
        assert self.te.evaluate("bad") is False

    def test_register_handler(self):
        results = []
        def handler(trg, ctx):
            results.append(trg.name)
        self.te.register_handler(TriggerType.TIME, handler)
        t = self.te.register_trigger("T", TriggerType.TIME, cooldown=0)
        self.te.evaluate(t.trigger_id)
        assert len(results) == 1

    def test_evaluate_all(self):
        self.te.register_trigger("T1", TriggerType.TIME, cooldown=0)
        self.te.register_trigger("T2", TriggerType.TIME, cooldown=0)
        fired = self.te.evaluate_all()
        assert len(fired) == 2

    def test_get_stats(self):
        self.te.register_trigger("T", TriggerType.TIME, cooldown=0)
        self.te.evaluate_all()
        stats = self.te.get_stats()
        assert stats["total_triggers"] == 1
        assert stats["total_fires"] >= 1


# ══════════════════════════════════════════════════════════════════════
# RuleEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestRuleEngine:
    def setup_method(self):
        self.re = RuleEngine()

    def test_add_rule(self):
        r = self.re.add_rule("Traffic", "traffic > 100")
        assert r.rule_id.startswith("rule_")
        assert len(self.re.get_all_rules()) == 1

    def test_remove_rule(self):
        r = self.re.add_rule("R", "x > 1")
        assert self.re.remove_rule(r.rule_id) is True
        assert self.re.remove_rule("bad") is False

    def test_get_rule(self):
        r = self.re.add_rule("R", "x > 1")
        assert self.re.get_rule(r.rule_id) is r
        assert self.re.get_rule("bad") is None

    def test_enable_disable(self):
        r = self.re.add_rule("R", "x > 1")
        assert self.re.disable_rule(r.rule_id) is True
        assert r.enabled is False
        assert self.re.enable_rule(r.rule_id) is True
        assert r.enabled is True
        assert self.re.disable_rule("bad") is False

    def test_evaluate_condition_gt(self):
        assert self.re.evaluate_condition("traffic > 100", {"traffic": 200}) is True
        assert self.re.evaluate_condition("traffic > 100", {"traffic": 50}) is False

    def test_evaluate_condition_lt(self):
        assert self.re.evaluate_condition("errors < 5", {"errors": 3}) is True
        assert self.re.evaluate_condition("errors < 5", {"errors": 10}) is False

    def test_evaluate_condition_eq(self):
        assert self.re.evaluate_condition("status == 200", {"status": 200}) is True
        assert self.re.evaluate_condition("status == 200", {"status": 404}) is False

    def test_evaluate_condition_gte(self):
        assert self.re.evaluate_condition("score >= 50", {"score": 50}) is True
        assert self.re.evaluate_condition("score >= 50", {"score": 49}) is False

    def test_evaluate_condition_lte(self):
        assert self.re.evaluate_condition("count <= 10", {"count": 5}) is True
        assert self.re.evaluate_condition("count <= 10", {"count": 15}) is False

    def test_evaluate_condition_ne(self):
        assert self.re.evaluate_condition("status != 0", {"status": 1}) is True
        assert self.re.evaluate_condition("status != 0", {"status": 0}) is False

    def test_evaluate_condition_bad_expr(self):
        assert self.re.evaluate_condition("invalid", {}) is False

    def test_evaluate_rule(self):
        r = self.re.add_rule("R", "traffic > 100")
        assert self.re.evaluate_rule(r, {"traffic": 200}) is True
        assert r.trigger_count == 1

    def test_evaluate_rule_disabled(self):
        r = self.re.add_rule("R", "traffic > 100")
        self.re.disable_rule(r.rule_id)
        assert self.re.evaluate_rule(r, {"traffic": 200}) is False

    def test_evaluate_rule_with_action(self):
        results = []
        def handler(action, ctx):
            results.append(action.action_type)
        self.re.register_action("notify", handler)
        r = self.re.add_rule("R", "x > 1",
                             actions=[RuleAction("notify")])
        self.re.evaluate_rule(r, {"x": 5})
        assert len(results) == 1

    def test_evaluate_all(self):
        self.re.add_rule("R1", "cpu > 80")
        self.re.add_rule("R2", "cpu > 90")
        triggered = self.re.evaluate_all({"cpu": 95})
        assert len(triggered) == 2

    def test_get_stats(self):
        self.re.add_rule("R", "x > 1")
        self.re.evaluate_all({"x": 5})
        stats = self.re.get_stats()
        assert stats["total_rules"] == 1


# ══════════════════════════════════════════════════════════════════════
# AutomationPipeline Tests
# ══════════════════════════════════════════════════════════════════════

class TestAutomationPipeline:
    def setup_method(self):
        self.pl = AutomationPipeline()

    def test_add_task(self):
        t = self.pl.add_task("Research", "research", "gather", order=1)
        assert t.task_id.startswith("pt_")
        assert len(self.pl.get_all_tasks()) == 1

    def test_remove_task(self):
        t = self.pl.add_task("T", "m", "a")
        assert self.pl.remove_task(t.task_id) is True
        assert self.pl.remove_task("bad") is False

    def test_get_task(self):
        t = self.pl.add_task("T", "m", "a")
        assert self.pl.get_task(t.task_id) is t
        assert self.pl.get_task("bad") is None

    def test_execute_empty(self):
        result = self.pl.execute()
        assert result.status == "completed"

    def test_execute_with_tasks(self):
        self.pl.add_task("T1", "m", "action1", order=1)
        self.pl.add_task("T2", "m", "action2", order=2)
        result = self.pl.execute()
        assert result.tasks_completed == 2
        assert result.status == "completed"

    def test_execute_with_handler(self):
        results = []
        def handler(task, ctx):
            results.append(task.name)
        self.pl.register_handler("custom", handler)
        self.pl.add_task("Custom", "m", "custom", order=1)
        result = self.pl.execute()
        assert len(results) == 1

    def test_get_stats(self):
        self.pl.add_task("T", "m", "a")
        stats = self.pl.get_stats()
        assert stats["total_tasks"] == 1


# ══════════════════════════════════════════════════════════════════════
# WorkerManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestWorkerManager:
    def setup_method(self):
        self.wm = WorkerManager(min_workers=2, max_workers=5)

    def test_initialize(self):
        self.wm.initialize()
        assert len(self.wm.get_all_workers()) >= 2

    def test_add_remove_worker(self):
        w = self.wm.add_worker("custom")
        assert w.name == "custom"
        assert self.wm.remove_worker(w.worker_id) is True
        assert self.wm.remove_worker("bad") is False

    def test_get_idle_worker(self):
        self.wm.initialize()
        w = self.wm.get_idle_worker()
        assert w is not None
        assert w.is_busy is False

    def test_dispatch(self):
        self.wm.initialize()
        assert self.wm.dispatch({"name": "task1"}) is True
        stats = self.wm.get_stats()
        assert stats["busy"] == 1

    def test_dispatch_no_worker(self):
        assert self.wm.dispatch({"name": "task"}) is False  # no workers

    def test_complete_task(self):
        self.wm.initialize()
        worker = self.wm.get_idle_worker()
        self.wm.dispatch({"name": "task"})
        assert self.wm.complete_task(worker.worker_id, True) is True
        assert worker.is_busy is False
        assert worker.completed_tasks == 1
        assert self.wm.complete_task("bad", True) is False

    def test_scale_to(self):
        self.wm.initialize()
        assert self.wm.scale_to(4) == 4
        assert len(self.wm.get_all_workers()) == 4
        assert self.wm.scale_to(1) >= 2  # min_workers

    def test_get_stats(self):
        self.wm.initialize()
        stats = self.wm.get_stats()
        assert stats["min_workers"] == 2
        assert stats["max_workers"] == 5


# ══════════════════════════════════════════════════════════════════════
# CronManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestCronManager:
    def setup_method(self):
        self.cm = CronManager()

    def test_add_schedule(self):
        s = self.cm.add_schedule("Daily", "daily", "wf_1")
        assert s.schedule_id.startswith("cron_")
        assert len(self.cm.get_all_schedules()) == 1

    def test_remove_schedule(self):
        s = self.cm.add_schedule("D", "daily")
        assert self.cm.remove_schedule(s.schedule_id) is True
        assert self.cm.remove_schedule("bad") is False

    def test_get_schedule(self):
        s = self.cm.add_schedule("D", "daily")
        assert self.cm.get_schedule(s.schedule_id) is s
        assert self.cm.get_schedule("bad") is None

    def test_enable_disable(self):
        s = self.cm.add_schedule("D", "daily")
        assert self.cm.disable_schedule(s.schedule_id) is True
        assert s.enabled is False
        assert self.cm.enable_schedule(s.schedule_id) is True
        assert s.enabled is True
        assert self.cm.disable_schedule("bad") is False

    def test_get_due_schedules(self):
        s = self.cm.add_schedule("D", "daily")
        s.next_run = time.time() - 10
        due = self.cm.get_due_schedules()
        assert len(due) == 1

    def test_tick(self):
        s = self.cm.add_schedule("D", "daily")
        s.next_run = time.time() - 10
        fired = self.cm.tick()
        assert len(fired) == 1
        assert s.run_count == 1
        assert s.next_run > time.time()

    def test_tick_with_handler(self):
        results = []
        def handler(sched):
            results.append(sched.name)
        s = self.cm.add_schedule("D", "daily")
        s.next_run = time.time() - 10
        self.cm.register_handler(s.schedule_id, handler)
        self.cm.tick()
        assert len(results) == 1

    def test_get_stats(self):
        self.cm.add_schedule("D1", "daily")
        self.cm.add_schedule("D2", "weekly")
        stats = self.cm.get_stats()
        assert stats["total_schedules"] == 2


# ══════════════════════════════════════════════════════════════════════
# SmartRetryEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestSmartRetryEngine:
    def setup_method(self):
        self.re = SmartRetryEngine()

    def test_should_retry(self):
        assert self.re.should_retry(0) is True
        assert self.re.should_retry(3) is False  # max_retries = 3

    def test_calculate_delay(self):
        d1 = self.re.calculate_delay(0)
        assert d1 >= 5.0
        d2 = self.re.calculate_delay(2)
        assert d2 >= 20.0

    def test_record_retry(self):
        entry = self.re.record_retry("task_1", 1, "timeout error")
        assert entry["attempt"] == 1
        assert "timeout" in entry["error"]

    def test_get_history(self):
        self.re.record_retry("task_1", 1)
        self.re.record_retry("task_1", 2)
        assert len(self.re.get_history("task_1")) == 2

    def test_get_stats(self):
        self.re.record_retry("t1", 1)
        stats = self.re.get_stats()
        assert stats["total_retries"] == 1
        assert stats["tracked_tasks"] == 1


# ══════════════════════════════════════════════════════════════════════
# AutoScalingEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestAutoScalingEngine:
    def setup_method(self):
        self.se = AutoScalingEngine()

    def test_should_scale_up_cpu(self):
        assert self.se.should_scale_up(5, cpu=85.0) is True

    def test_should_scale_up_queue(self):
        assert self.se.should_scale_up(5, queue_size=100) is True

    def test_should_scale_up_maxed(self):
        assert self.se.should_scale_up(20, cpu=85.0) is False  # max

    def test_should_scale_down(self):
        assert self.se.should_scale_down(10, cpu=20.0) is True

    def test_should_scale_down_at_min(self):
        assert self.se.should_scale_down(2, cpu=20.0) is False  # min

    def test_scale_up(self):
        assert self.se.scale_up(5) > 5

    def test_scale_down(self):
        assert self.se.scale_down(10) < 10

    def test_get_stats(self):
        self.se.scale_up(5)
        stats = self.se.get_stats()
        assert stats["total_scale_ups"] == 1


# ══════════════════════════════════════════════════════════════════════
# WorkflowOptimizer Tests
# ══════════════════════════════════════════════════════════════════════

class TestWorkflowOptimizer:
    def setup_method(self):
        self.wo = WorkflowOptimizer()

    def test_optimize_order_no_deps(self):
        tasks = [
            PipelineTask("B", "m", "b", order=2),
            PipelineTask("A", "m", "a", order=1),
        ]
        ordered = self.wo.optimize_order(tasks)
        # With no deps, order stays as given (dependency-based)
        assert len(ordered) == 2

    def test_estimate_duration(self):
        tasks = [PipelineTask("T", "m", "a")]
        assert self.wo.estimate_duration(tasks) == 10.0

    def test_suggest_parallelism(self):
        tasks = [
            PipelineTask("A", "m", "a"),
            PipelineTask("B", "m", "b", depends_on=["pt_a"]),
        ]
        n = self.wo.suggest_parallelism(tasks)
        assert n == 1  # only 1 independent task

    def test_get_stats(self):
        stats = self.wo.get_stats()
        assert stats["total_optimizations"] == 0


# ══════════════════════════════════════════════════════════════════════
# SafetyManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestSafetyManager:
    def setup_method(self):
        self.sm = SafetyManager()

    def test_check_rate_limit(self):
        for _ in range(60):
            assert self.sm.check_rate_limit() is True
        # 61st should fail
        assert self.sm.check_rate_limit() is False

    def test_check_concurrent(self):
        assert self.sm.check_concurrent(5) is True
        assert self.sm.check_concurrent(15) is False

    def test_check_daily_limit(self):
        assert self.sm.check_daily_limit(500) is True
        assert self.sm.check_daily_limit(1500) is False

    def test_check_interval(self):
        assert self.sm.check_interval(None) is True
        assert self.sm.check_interval(time.time() - 100) is True
        assert self.sm.check_interval(time.time()) is False

    def test_check_blocked_hours(self):
        assert self.sm.check_blocked_hours() is True  # current hour not blocked

    def test_get_daily_count(self):
        self.sm.record_execution()
        d = self.sm.get_daily_count()
        assert d == 1

    def test_get_stats(self):
        self.sm.record_execution()
        stats = self.sm.get_stats()
        assert stats["daily_executions"] == 1


# ══════════════════════════════════════════════════════════════════════
# AutomationMonitor Tests
# ══════════════════════════════════════════════════════════════════════

class TestAutomationMonitor:
    def setup_method(self):
        self.mon = AutomationMonitor()

    def test_record_snapshot(self):
        self.mon.record_snapshot({"workers": 5})
        assert self.mon.get_stats()["snapshots"] == 1

    def test_record_warning(self):
        self.mon.record_warning("High CPU", "monitor")
        assert self.mon.get_stats()["warnings"] == 1

    def test_record_error(self):
        self.mon.record_error("Failed", "pipeline", "timeout")
        assert self.mon.get_stats()["errors"] == 1

    def test_get_status(self):
        status = self.mon.get_status(
            {"busy": 2}, {"total_tasks": 10}, {"violations": 0}
        )
        assert "status" in status
        assert "workers" in status


# ══════════════════════════════════════════════════════════════════════
# EmergencyRecovery Tests
# ══════════════════════════════════════════════════════════════════════

class TestEmergencyRecovery:
    def setup_method(self):
        self.er = EmergencyRecovery()

    def test_recover_no_handler(self):
        result = self.er.recover("crash")
        assert result["status"] == "no_handler"

    def test_recover_with_handler(self):
        def handler(ctx):
            return {"recovered": True}
        self.er.register_handler("api_failure", handler)
        result = self.er.recover("api_failure")
        assert result["status"] == "recovered"

    def test_recover_crashed_jobs(self):
        def handler(ctx):
            return {"ok": True}
        self.er.register_handler("crashed_job", handler)
        jobs = [{"id": "1"}, {"id": "2"}]
        count = self.er.recover_crashed_jobs(jobs)
        assert count == 2

    def test_get_logs(self):
        result = self.er.recover("test_scenario")
        logs = self.er.get_logs()
        assert len(logs) >= 1
        assert logs[0]["scenario"] == "test_scenario"

    def test_get_stats(self):
        result = self.er.recover("test")
        stats = self.er.get_stats()
        assert stats["total_incidents"] >= 1


# ══════════════════════════════════════════════════════════════════════
# AutomationAPI Tests
# ══════════════════════════════════════════════════════════════════════

class TestAutomationAPI:
    def setup_method(self):
        self.engine = AutomationEngine()
        self.api = self.engine.api

    def test_get_status(self):
        status = self.api.get_status()
        assert "automation" in status
        assert "triggers" in status
        assert "rules" in status
        assert "pipeline" in status
        assert "workers" in status
        assert "cron" in status
        assert "retry" in status
        assert "scaling" in status
        assert "safety" in status
        assert "monitoring" in status
        assert "recovery" in status
        assert "optimizer" in status

    def test_get_health(self):
        health = self.api.get_health()
        assert "status" in health
        assert "workers" in health

    def test_execute_workflow(self):
        result = self.api.execute_workflow("test", {"key": "val"})
        assert "status" in result


# ══════════════════════════════════════════════════════════════════════
# AutomationEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestAutomationEngine:
    def setup_method(self):
        self.engine = AutomationEngine()

    def test_initialization(self):
        assert self.engine.automation is not None
        assert self.engine.triggers is not None
        assert self.engine.rules is not None
        assert self.engine.pipeline is not None
        assert self.engine.workers is not None
        assert self.engine.cron is not None
        assert self.engine.retry is not None
        assert self.engine.scaling is not None
        assert self.engine.optimizer is not None
        assert self.engine.safety is not None
        assert self.engine.monitor is not None
        assert self.engine.recovery is not None
        assert self.engine.api is not None

    def test_default_pipeline(self):
        tasks = self.engine.pipeline.get_all_tasks()
        assert len(tasks) >= 10  # 10 default tasks

    def test_start_stop(self):
        r = self.engine.start()
        assert r["status"] == "started"
        r = self.engine.stop()
        assert r["status"] == "stopped"

    def test_pause_resume(self):
        self.engine.start()
        assert self.engine.pause()["status"] == "paused"
        assert self.engine.resume()["status"] == "resumed"
        self.engine.stop()

    def test_execute_pipeline(self):
        result = self.engine.execute_pipeline()
        assert "status" in result
        assert "tasks_completed" in result or "status" == "rate_limited"

    def test_execute_pipeline_concurrent_limit(self):
        # Busy all workers
        self.engine.workers.initialize()
        for w in self.engine.workers.get_all_workers():
            w.is_busy = True
        result = self.engine.execute_pipeline()
        assert result["status"] in ("no_worker_available", "rate_limited", "concurrent_limit")

    def test_get_status(self):
        status = self.engine.get_status()
        assert "module" in status
        assert "Automation Engine" in status["module"]
        assert "automation" in status
        assert "workers" in status


# ══════════════════════════════════════════════════════════════════════
# Exception Classes
# ══════════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_base(self):
        with pytest.raises(AutomationError):
            raise AutomationError()

    def test_trigger(self):
        with pytest.raises(TriggerError):
            raise TriggerError()

    def test_rule(self):
        with pytest.raises(RuleEngineError):
            raise RuleEngineError()

    def test_worker(self):
        with pytest.raises(WorkerError):
            raise WorkerError()

    def test_scaling(self):
        with pytest.raises(ScalingError):
            raise ScalingError()

    def test_safety(self):
        with pytest.raises(SafetyError):
            raise SafetyError()

    def test_recovery(self):
        with pytest.raises(RecoveryError):
            raise RecoveryError()

    def test_pipeline(self):
        with pytest.raises(PipelineError):
            raise PipelineError()

    def test_cron(self):
        with pytest.raises(CronError):
            raise CronError()

    def test_retry(self):
        with pytest.raises(RetryError):
            raise RetryError()

    def test_optimization(self):
        with pytest.raises(OptimizationError):
            raise OptimizationError()

    def test_monitoring(self):
        with pytest.raises(MonitoringError):
            raise MonitoringError()


# ══════════════════════════════════════════════════════════════════════
# Singleton Tests
# ══════════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_engine(self):
        e1 = get_automation_engine()
        e2 = get_automation_engine()
        assert e1 is e2
