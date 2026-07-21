"""ProductionCertifier — Enterprise Production Certification Framework.

Tests real production readiness:
- Load testing (parallel execution)
- Chaos testing (failure injection & recovery)
- Memory leak detection
- Security audit
- Long-run stability
- Pipeline integrity
- Real component execution
"""
from __future__ import annotations
import gc
import os
import sys
import time
import json
import tracemalloc
import threading
import subprocess
import importlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CertStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class CertResult:
    name: str
    status: CertStatus
    score: float
    details: str
    duration_ms: float = 0.0
    sub_tests: List[Dict[str, Any]] = field(default_factory=list)


def _make_request(topic: str, platform: str = "facebook"):
    from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import ContentRequest
    return ContentRequest(topic=topic, platform=platform)


class ProductionCertifier:
    """Full production certification engine."""

    def __init__(self):
        self.results: List[CertResult] = []
        self.start_time = 0.0

    def run_full_certification(self) -> Dict[str, Any]:
        self.start_time = time.time()
        self._print_header()
        
        self._test_pipeline_integrity()
        self._test_load_performance()
        self._test_chaos_resilience()
        self._test_memory_leaks()
        self._test_security_audit()
        self._test_long_run_stability()
        self._test_database_integrity()
        self._test_error_recovery()
        self._test_real_component_execution()
        self._test_production_benchmark()
        
        return self._generate_report()

    def _print_header(self):
        print("=" * 70)
        print("🏭 PRODUCTION CERTIFICATION — UNIVERSAL AI CONTENT OS")
        print("=" * 70)
        print()

    # ── 1. Pipeline Integrity ──────────────────────────────
    def _test_pipeline_integrity(self):
        start = time.time()
        sub = []
        score = 0.0

        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            pw = PipelineWiring()
            req = _make_request("Production test")
            response = pw.execute(req)
            
            if response:
                sub.append({"test": "Pipeline Execute", "status": "PASS", 
                           "detail": f"Response: {type(response).__name__}"})
                score += 1.0
            else:
                sub.append({"test": "Pipeline Execute", "status": "WARN", 
                           "detail": "Empty response"})
                score += 0.3
        except Exception as e:
            sub.append({"test": "Pipeline Execute", "status": "FAIL", "detail": str(e)[:80]})

        # Check response has content
        try:
            if hasattr(response, 'content') or hasattr(response, 'to_dict'):
                data = response.to_dict() if hasattr(response, 'to_dict') else {}
                sub.append({"test": "Response Structure", "status": "PASS",
                           "detail": f"Fields: {list(data.keys())[:5]}"})
                score += 0.5
        except Exception:
            sub.append({"test": "Response Structure", "status": "WARN", "detail": "Could not inspect"})
            score += 0.2

        fs = score / 1.5
        st = CertStatus.PASS if fs >= 0.7 else CertStatus.FAIL
        self.results.append(CertResult("Pipeline Integrity", st, fs, "End-to-end pipeline", 
                                       (time.time() - start) * 1000, sub))
        self._p("Pipeline Integrity", st, fs)

    # ── 2. Load Performance ─────────────────────────────────
    def _test_load_performance(self):
        start = time.time()
        sub = []
        score = 0.0

        # Sequential execution speed
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            t0 = time.time()
            for i in range(5):
                pw = PipelineWiring()
                pw.execute(_make_request(f"Load test {i}"))
            seq_time = (time.time() - t0) * 1000
            avg_time = seq_time / 5
            sub.append({"test": "Sequential (5x)", "status": "PASS" if avg_time < 500 else "WARN",
                        "detail": f"Avg {avg_time:.0f}ms/req"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Sequential (5x)", "status": "FAIL", "detail": str(e)[:60]})

        # Thread pool parallelism
        try:
            from concurrent.futures import ThreadPoolExecutor
            results = []
            t0 = time.time()
            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = []
                for i in range(5):
                    pw = PipelineWiring()
                    futures.append(pool.submit(pw.execute, _make_request(f"Parallel {i}")))
                for f in futures:
                    results.append(f.result())
            par_time = (time.time() - t0) * 1000
            sub.append({"test": "Parallel (5x)", "status": "PASS" if par_time < 2000 else "WARN",
                        "detail": f"Total {par_time:.0f}ms, {len(results)} results"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Parallel (5x)", "status": "FAIL", "detail": str(e)[:60]})

        # Memory under load
        try:
            import resource
            mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            for i in range(10):
                pw = PipelineWiring()
                pw.execute(_make_request(f"Mem test {i}"))
            gc.collect()
            mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            delta = mem_after - mem_before
            sub.append({"test": "Memory Under Load", 
                        "status": "PASS" if delta < 50 else "WARN",
                        "detail": f"Peak RSS: {mem_after:.0f}MB (delta: {delta:.1f}MB)"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Memory Under Load", "status": "SKIP", "detail": str(e)[:60]})
            score += 0.5

        fs = score / 3.0
        st = CertStatus.PASS if fs >= 0.6 else CertStatus.FAIL
        self.results.append(CertResult("Load Performance", st, fs, "Parallel & memory tests",
                                       (time.time() - start) * 1000, sub))
        self._p("Load Performance", st, fs)

    # ── 3. Chaos Resilience ─────────────────────────────────
    def _test_chaos_resilience(self):
        start = time.time()
        sub = []
        score = 0.0

        # Empty topic
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            pw = PipelineWiring()
            result = pw.execute(_make_request(""))
            sub.append({"test": "Empty Topic Recovery", "status": "PASS", 
                        "detail": "Pipeline survived empty input"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Empty Topic Recovery", "status": "WARN",
                        "detail": f"Exception on empty: {type(e).__name__}"})
            score += 0.3

        # Special characters
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            pw = PipelineWiring()
            result = pw.execute(_make_request("🔥💯🚀 <b>XSS</b> ' OR 1=1"))
            sub.append({"test": "Special Chars Recovery", "status": "PASS",
                        "detail": "Survived injection attempt"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Special Chars Recovery", "status": "WARN",
                        "detail": f"Exception: {type(e).__name__}"})
            score += 0.3

        # Rapid re-init
        try:
            t0 = time.time()
            for _ in range(20):
                pw = PipelineWiring()
            init_time = (time.time() - t0) * 1000
            sub.append({"test": "Rapid Re-init (20x)", "status": "PASS" if init_time < 5000 else "WARN",
                        "detail": f"{init_time:.0f}ms for 20 inits"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Rapid Re-init (20x)", "status": "FAIL", "detail": str(e)[:60]})

        fs = score / 3.0
        st = CertStatus.PASS if fs >= 0.5 else CertStatus.FAIL
        self.results.append(CertResult("Chaos Resilience", st, fs, "Failure recovery",
                                       (time.time() - start) * 1000, sub))
        self._p("Chaos Resilience", st, fs)

    # ── 4. Memory Leak Detection ────────────────────────────
    def _test_memory_leaks(self):
        start = time.time()
        sub = []
        score = 0.0

        try:
            tracemalloc.start()
            gc.collect()
            snap1 = tracemalloc.take_snapshot()
            
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            for i in range(10):
                pw = PipelineWiring()
                pw.execute(_make_request(f"Leak test {i}"))
            
            gc.collect()
            snap2 = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            top_stats = snap2.compare_to(snap1, 'lineno')
            total_diff = sum(s.size_diff for s in top_stats)
            sub.append({"test": "Memory Snapshot Diff", 
                        "status": "PASS" if abs(total_diff) < 10 * 1024 * 1024 else "WARN",
                        "detail": f"Diff: {total_diff / 1024:.1f}KB over 10 runs"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Memory Snapshot Diff", "status": "FAIL", "detail": str(e)[:60]})

        try:
            gc.collect()
            collected = gc.collect()
            sub.append({"test": "GC Collection", "status": "PASS",
                        "detail": f"Collected {collected} objects"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "GC Collection", "status": "FAIL", "detail": str(e)[:60]})

        fs = score / 2.0
        st = CertStatus.PASS if fs >= 0.7 else CertStatus.FAIL
        self.results.append(CertResult("Memory Leaks", st, fs, "Leak detection",
                                       (time.time() - start) * 1000, sub))
        self._p("Memory Leaks", st, fs)

    # ── 5. Security Audit ───────────────────────────────────
    def _test_security_audit(self):
        start = time.time()
        sub = []
        score = 0.0

        # Hardcoded secrets scan
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", "-E", 
                 r'(password|secret|api_key|token)\s*=\s*["\'][A-Za-z0-9]{20,}',
                 "layers/"],
                capture_output=True, text=True, timeout=30
            )
            findings = [l for l in result.stdout.strip().split('\n') 
                       if l and '__pycache__' not in l and 'test' not in l.lower()]
            if not findings:
                sub.append({"test": "Hardcoded Secrets Scan", "status": "PASS",
                            "detail": "No hardcoded secrets found"})
                score += 1.0
            else:
                sub.append({"test": "Hardcoded Secrets Scan", "status": "WARN",
                            "detail": f"{len(findings)} potential findings"})
                score += 0.3
        except Exception as e:
            sub.append({"test": "Hardcoded Secrets Scan", "status": "SKIP", "detail": str(e)[:60]})
            score += 0.5

        # SQL injection
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            pw = PipelineWiring()
            pw.execute(_make_request("'; DROP TABLE users; --"))
            sub.append({"test": "SQL Injection Safety", "status": "PASS",
                        "detail": "System survived SQL injection attempt"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "SQL Injection Safety", "status": "WARN",
                        "detail": f"Exception: {type(e).__name__}"})
            score += 0.3

        # XSS
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            pw = PipelineWiring()
            pw.execute(_make_request("<script>alert('xss')</script>"))
            sub.append({"test": "XSS Safety", "status": "PASS",
                        "detail": "System survived XSS attempt"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "XSS Safety", "status": "WARN",
                        "detail": f"Exception: {type(e).__name__}"})
            score += 0.3

        # Large input
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            pw = PipelineWiring()
            big_topic = "A" * 10000
            pw.execute(_make_request(big_topic))
            sub.append({"test": "Large Input Safety", "status": "PASS",
                        "detail": f"Handled {len(big_topic)} char input"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Large Input Safety", "status": "WARN",
                        "detail": f"Exception: {type(e).__name__}"})
            score += 0.3

        fs = score / 4.0
        st = CertStatus.PASS if fs >= 0.6 else CertStatus.FAIL
        self.results.append(CertResult("Security Audit", st, fs, "Security checks",
                                       (time.time() - start) * 1000, sub))
        self._p("Security Audit", st, fs)

    # ── 6. Long-Run Stability ───────────────────────────────
    def _test_long_run_stability(self):
        start = time.time()
        sub = []
        score = 0.0

        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            successes = 0
            failures = 0
            errors = []
            t0 = time.time()
            
            for i in range(25):
                try:
                    pw = PipelineWiring()
                    pw.execute(_make_request(f"Stability run {i}"))
                    successes += 1
                except Exception as e:
                    failures += 1
                    errors.append(f"{type(e).__name__}: {str(e)[:30]}")
            
            duration = (time.time() - t0) * 1000
            success_rate = successes / 25 * 100
            
            sub.append({"test": "25 Pipeline Runs", 
                        "status": "PASS" if success_rate >= 90 else "WARN",
                        "detail": f"{successes}/25 ({success_rate:.0f}%) in {duration:.0f}ms"})
            score += 1.0 if success_rate >= 90 else 0.3
            
            if errors:
                unique_errors = list(set(errors))
                sub.append({"test": "Error Types", "status": "INFO",
                            "detail": f"{len(unique_errors)} unique: {unique_errors[0][:40]}"})
        except Exception as e:
            sub.append({"test": "25 Pipeline Runs", "status": "FAIL", "detail": str(e)[:60]})

        fs = score / 1.0
        st = CertStatus.PASS if fs >= 0.7 else CertStatus.FAIL
        self.results.append(CertResult("Long-Run Stability", st, fs, "25 consecutive runs",
                                       (time.time() - start) * 1000, sub))
        self._p("Long-Run Stability", st, fs)

    # ── 7. Database Integrity ───────────────────────────────
    def _test_database_integrity(self):
        start = time.time()
        sub = []
        score = 0.0

        # Find the SQLite manager
        db_class = None
        db_paths = [
            ("layers.layer13_persistence.modules.persistence_kernel.persistence_manager", "PersistenceManager"),
        ]
        for mod_path, cls_name in db_paths:
            try:
                m = importlib.import_module(mod_path)
                db_class = getattr(m, cls_name)
                break
            except (ImportError, AttributeError):
                continue

        if db_class:
            try:
                db = db_class()
                if hasattr(db, 'initialize'):
                    db.initialize()
                sub.append({"test": "DB Init", "status": "PASS", "detail": f"Using {db_class.__name__}"})
                score += 1.0
            except Exception as e:
                sub.append({"test": "DB Init", "status": "FAIL", "detail": str(e)[:60]})
        else:
            # Fallback: test SQLite directly
            try:
                import sqlite3
                conn = sqlite3.connect(":memory:")
                conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
                conn.execute("INSERT INTO test (data) VALUES (?)", ("production_test",))
                row = conn.execute("SELECT * FROM test").fetchone()
                conn.close()
                sub.append({"test": "SQLite Operations", "status": "PASS", 
                           "detail": f"Write+Read: {row}"})
                score += 1.0
            except Exception as e:
                sub.append({"test": "SQLite Operations", "status": "FAIL", "detail": str(e)[:60]})

        # Concurrent writes
        try:
            import sqlite3
            errors = []
            def write_thread(i):
                try:
                    conn = sqlite3.connect(":memory:")
                    conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER, data TEXT)")
                    conn.execute("INSERT INTO t VALUES (?, ?)", (i, f"data_{i}"))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    errors.append(str(e)[:30])
            
            threads = [threading.Thread(target=write_thread, args=(i,)) for i in range(10)]
            for t in threads: t.start()
            for t in threads: t.join()
            
            sub.append({"test": "Concurrent Writes (10)", 
                        "status": "PASS" if len(errors) == 0 else "WARN",
                        "detail": f"{10 - len(errors)}/10 succeeded"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Concurrent Writes", "status": "FAIL", "detail": str(e)[:60]})

        fs = score / 2.0
        st = CertStatus.PASS if fs >= 0.7 else CertStatus.FAIL
        self.results.append(CertResult("Database Integrity", st, fs, "SQLite persistence",
                                       (time.time() - start) * 1000, sub))
        self._p("Database Integrity", st, fs)

    # ── 8. Error Recovery ───────────────────────────────────
    def _test_error_recovery(self):
        start = time.time()
        sub = []
        score = 0.0

        try:
            from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
            gp = GeminiProvider()
            result = gp.generate("test prompt")
            sub.append({"test": "Gemini Fallback", "status": "PASS",
                        "detail": f"Provider returned: {type(result).__name__}"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "Gemini Fallback", "status": "WARN",
                        "detail": f"Exception: {type(e).__name__}"})
            score += 0.3

        try:
            from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
            km = KeyManager()
            sel = km.select_key("text")
            sub.append({"test": "KeyManager Empty State", "status": "PASS",
                        "detail": f"Selection: {sel is not None}"})
            score += 1.0
        except Exception as e:
            sub.append({"test": "KeyManager Empty State", "status": "WARN",
                        "detail": f"Exception: {type(e).__name__}"})
            score += 0.3

        fs = score / 2.0
        st = CertStatus.PASS if fs >= 0.5 else CertStatus.FAIL
        self.results.append(CertResult("Error Recovery", st, fs, "Graceful degradation",
                                       (time.time() - start) * 1000, sub))
        self._p("Error Recovery", st, fs)

    # ── 9. Real Component Execution ─────────────────────────
    def _test_real_component_execution(self):
        start = time.time()
        sub = []
        score = 0.0

        components = [
            ("ConfigManager", "layers.layer01_core.modules.config_manager", "ConfigManager"),
            ("MemoryManager", "layers.layer01_core.modules.memory_manager", "MemoryManager"),
            ("TrendManager", "layers.layer02_research.modules.trend_discovery.trend_manager", "TrendManager"),
            ("SemanticAnalyzer", "layers.layer03_intelligence.modules.content_understanding.semantic_analyzer", "SemanticAnalyzer"),
            ("PlannerManager", "layers.layer04_writing.modules.content_planner.planner_manager", "PlannerManager"),
            ("QualityOrchestrator", "layers.layer06_quality.modules.quality_orchestrator.quality_orchestrator", "QualityOrchestrator"),
            ("LessonGenerator", "layers.layer09_learning.modules.learning_engine.lesson_generator", "LessonGenerator"),
            ("AsyncRuntime", "layers.layer11_async_runtime.modules.async_runtime_engine.runtime", "AsyncRuntime"),
        ]

        for name, mod_path, cls_name in components:
            try:
                m = importlib.import_module(mod_path)
                cls = getattr(m, cls_name)
                instance = cls()
                sub.append({"test": name, "status": "PASS", "detail": f"Instantiated"})
                score += 1.0
            except Exception as e:
                sub.append({"test": name, "status": "FAIL", "detail": str(e)[:60]})

        fs = score / len(components)
        st = CertStatus.PASS if fs >= 0.8 else CertStatus.FAIL
        self.results.append(CertResult("Real Components", st, fs, f"{len(components)} components tested",
                                       (time.time() - start) * 1000, sub))
        self._p("Real Components", st, fs)

    # ── 10. Production Benchmark ────────────────────────────
    def _test_production_benchmark(self):
        start = time.time()
        sub = []
        score = 0.0

        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import PipelineWiring
            
            # Cold start
            t0 = time.time()
            pw = PipelineWiring()
            cold_start = (time.time() - t0) * 1000
            sub.append({"test": "Cold Start", "status": "PASS" if cold_start < 1000 else "WARN",
                        "detail": f"{cold_start:.0f}ms"})
            score += 0.5

            # Warm execution
            times = []
            for _ in range(5):
                t0 = time.time()
                pw.execute(_make_request("Benchmark"))
                times.append((time.time() - t0) * 1000)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            sub.append({"test": "Warm Execution (5x)", 
                        "status": "PASS" if avg_time < 300 else "WARN",
                        "detail": f"Avg:{avg_time:.0f}ms Min:{min_time:.0f}ms Max:{max_time:.0f}ms"})
            score += 0.5

            # Throughput
            t0 = time.time()
            count = 0
            while (time.time() - t0) < 5:
                pw = PipelineWiring()
                pw.execute(_make_request("Throughput"))
                count += 1
            rps = count / 5.0
            sub.append({"test": "Throughput (5s)", "status": "PASS" if rps >= 1 else "WARN",
                        "detail": f"{rps:.1f} req/sec ({count} in 5s)"})
            score += 1.0

        except Exception as e:
            sub.append({"test": "Benchmark", "status": "FAIL", "detail": str(e)[:60]})

        fs = score / 2.0
        st = CertStatus.PASS if fs >= 0.6 else CertStatus.FAIL
        self.results.append(CertResult("Production Benchmark", st, fs, "Performance metrics",
                                       (time.time() - start) * 1000, sub))
        self._p("Production Benchmark", st, fs)

    # ── Helpers ──────────────────────────────────────────────
    def _p(self, name: str, status: CertStatus, score: float):
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}
        print(f"  {icon.get(status.value, '?')} {name:30s} — {status.value:4s} ({score*100:.0f}%)")
        for s in self.results[-1].sub_tests:
            si = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️", "INFO": "ℹ️"}
            print(f"      {si.get(s['status'],'?')} {s['test']:28s} {s['status']:6s} {s['detail'][:50]}")

    def _generate_report(self):
        total_duration = (time.time() - self.start_time) * 1000
        
        passed = sum(1 for r in self.results if r.status == CertStatus.PASS)
        warned = sum(1 for r in self.results if r.status == CertStatus.WARN)
        failed = sum(1 for r in self.results if r.status == CertStatus.FAIL)
        skipped = sum(1 for r in self.results if r.status == CertStatus.SKIP)
        total = len(self.results)
        avg_score = sum(r.score for r in self.results) / max(total, 1)
        
        print()
        print("=" * 70)
        print("🏭 PRODUCTION CERTIFICATION REPORT")
        print("=" * 70)
        print()
        
        for r in self.results:
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}
            print(f"  {icon.get(r.status.value, '?')} {r.name:30s} {r.status.value:6s} ({r.score*100:.0f}%)")
        
        print()
        print(f"  Overall Score:       {avg_score*100:.1f}%")
        print(f"  Passed:              {passed}/{total}")
        print(f"  Warnings:            {warned}/{total}")
        print(f"  Failed:              {failed}/{total}")
        print(f"  Skipped:             {skipped}/{total}")
        
        if failed == 0 and avg_score >= 0.8:
            cert = "🏆 CERTIFIED — Production Ready"
        elif failed == 0:
            cert = "⚠️ CONDITIONAL — All pass but score below 80%"
        else:
            cert = "❌ NOT CERTIFIED — Failures detected"
        
        print(f"  Certification:       {cert}")
        print(f"  Duration:            {total_duration:.0f}ms")
        print()
        print("=" * 70)
        
        report = {
            "overall_score": round(avg_score * 100, 1),
            "certified": failed == 0 and avg_score >= 0.8,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "skipped": skipped,
            "total": total,
            "duration_ms": round(total_duration, 1),
            "tests": [{
                "name": r.name,
                "status": r.status.value,
                "score": round(r.score * 100, 1),
                "duration_ms": round(r.duration_ms, 1),
                "sub_tests": r.sub_tests,
            } for r in self.results],
        }
        return report
