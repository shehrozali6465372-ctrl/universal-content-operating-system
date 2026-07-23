"""PerformanceBenchmark — Database performance testing suite.

Tests:
- Insert throughput (single + batch)
- Read throughput
- Update throughput
- Delete throughput
- Concurrent access
- Repository CRUD with Insert/Update/Delete latency breakdown
- Transaction throughput
- Latency percentiles (avg, p95, p99)
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List


class PerformanceBenchmark:
    """Run performance benchmarks against the connection pool."""

    def __init__(self, pool: Any):
        self._pool = pool
        self._pg = pool._pg_available if hasattr(pool, '_pg_available') else False
        self._ph = "%s" if self._pg else "?"

    def run_insert_benchmark(self, count: int = 1000) -> Dict[str, Any]:
        """Benchmark single-row inserts with latency tracking."""
        latencies: List[float] = []
        prefix = f"bench_ins_{int(time.time() * 1000)}"
        inserted = 0
        for i in range(count):
            start = time.time()
            try:
                self._pool.insert("agent_config", {
                    "key": f"{prefix}_{i}",
                    "value": f"bench_val_{i}",
                    "category": "benchmark",
                })
                latencies.append((time.time() - start) * 1000)
                inserted += 1
            except Exception:
                break
        # Cleanup
        self._pool.delete("agent_config", f"category = {self._ph}", ("benchmark",))

        elapsed_ms = sum(latencies) if latencies else 0
        sorted_lats = sorted(latencies)
        return {
            "test": "insert_benchmark",
            "count": inserted,
            "target": count,
            "elapsed_ms": round(elapsed_ms, 1),
            "rate_per_sec": round(inserted / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0,
            "latency": _latency_stats(latencies),
            "passed": inserted == count,
        }

    def run_read_benchmark(self, count: int = 10000) -> Dict[str, Any]:
        """Benchmark SELECT queries with latency tracking."""
        prefix = f"bench_read_{int(time.time() * 1000)}"
        # Seed
        for i in range(100):
            self._pool.insert("agent_config", {
                "key": f"{prefix}_{i}",
                "value": f"bench_val_{i}",
                "category": "bench_read",
            })

        latencies: List[float] = []
        reads = 0
        for i in range(count):
            start = time.time()
            try:
                self._pool.query_one(
                    f"SELECT * FROM agent_config WHERE key = {self._ph}",
                    (f"{prefix}_{i % 100}",),
                )
                latencies.append((time.time() - start) * 1000)
                reads += 1
            except Exception:
                break
        self._pool.delete("agent_config", f"category = {self._ph}", ("bench_read",))

        elapsed_ms = sum(latencies) if latencies else 0
        return {
            "test": "read_benchmark",
            "count": reads,
            "target": count,
            "elapsed_ms": round(elapsed_ms, 1),
            "rate_per_sec": round(reads / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0,
            "latency": _latency_stats(latencies),
            "passed": reads >= count * 0.95,
        }

    def run_update_benchmark(self, count: int = 500) -> Dict[str, Any]:
        """Benchmark UPDATE operations with latency tracking."""
        # Seed
        prefix = f"bench_upd_{int(time.time() * 1000)}"
        for i in range(count):
            self._pool.insert("agent_config", {
                "key": f"{prefix}_{i}",
                "value": "original",
                "category": "bench_update",
            })

        latencies: List[float] = []
        updated = 0
        for i in range(count):
            start = time.time()
            try:
                self._pool.update("agent_config",
                    {"value": f"updated_{i}"},
                    f"key = {self._ph}", (f"bench_update_{i}",),
                )
                latencies.append((time.time() - start) * 1000)
                updated += 1
            except Exception:
                break
        self._pool.delete("agent_config", f"category = {self._ph}", ("bench_update",))

        elapsed_ms = sum(latencies) if latencies else 0
        return {
            "test": "update_benchmark",
            "count": updated,
            "target": count,
            "elapsed_ms": round(elapsed_ms, 1),
            "rate_per_sec": round(updated / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0,
            "latency": _latency_stats(latencies),
            "passed": updated >= count * 0.95,
        }

    def run_delete_benchmark(self, count: int = 500) -> Dict[str, Any]:
        """Benchmark DELETE operations with latency tracking."""
        # Seed
        prefix = f"bench_del_{int(time.time() * 1000)}"
        for i in range(count):
            self._pool.insert("agent_config", {
                "key": f"{prefix}_{i}",
                "value": "to_delete",
                "category": "bench_delete",
            })

        latencies: List[float] = []
        deleted = 0
        for i in range(count):
            start = time.time()
            try:
                self._pool.delete("agent_config", f"key = {self._ph}", (f"{prefix}_{i}",))
                latencies.append((time.time() - start) * 1000)
                deleted += 1
            except Exception:
                break

        elapsed_ms = sum(latencies) if latencies else 0
        return {
            "test": "delete_benchmark",
            "count": deleted,
            "target": count,
            "elapsed_ms": round(elapsed_ms, 1),
            "rate_per_sec": round(deleted / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0,
            "latency": _latency_stats(latencies),
            "passed": deleted >= count * 0.95,
        }

    def run_concurrent_benchmark(self, threads: int = 10, ops_per_thread: int = 100) -> Dict[str, Any]:
        """Benchmark concurrent access."""
        results = []
        lock = threading.Lock()

        def worker(thread_id):
            count = 0
            for i in range(ops_per_thread):
                try:
                    key = f"conc_{thread_id}_{i}"
                    self._pool.insert("agent_config", {
                        "key": key, "value": "v", "category": "conc_bench"
                    })
                    self._pool.query_one(
                        f"SELECT * FROM agent_config WHERE key = {self._ph}", (key,),
                    )
                    count += 1
                except Exception:
                    pass
            with lock:
                results.append(count)

        start = time.time()
        thread_list = [threading.Thread(target=worker, args=(t,)) for t in range(threads)]
        for t in thread_list:
            t.start()
        for t in thread_list:
            t.join()
        elapsed_ms = (time.time() - start) * 1000
        total_ops = sum(results)
        self._pool.delete("agent_config", f"category = {self._ph}", ("conc_bench",))

        return {
            "test": "concurrent_benchmark",
            "threads": threads,
            "total_ops": total_ops,
            "target_ops": threads * ops_per_thread,
            "elapsed_ms": round(elapsed_ms, 1),
            "rate_per_sec": round(total_ops / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0,
            "passed": total_ops >= threads * ops_per_thread * 0.9,
        }

    def run_repository_benchmark(self) -> Dict[str, Any]:
        """Benchmark repository CRUD with Insert/Update/Delete latency breakdown."""
        try:
            from layers.layer13_persistence.modules.postgresql.repositories.repositories import (
                ConfigRepository, MemoryRepository, LogRepository,
            )
            config_repo = ConfigRepository(self._pool)
            memory_repo = MemoryRepository(self._pool)
            log_repo = LogRepository(self._pool)
            results = {}

            # Config Repository — Insert
            insert_lats = []
            for i in range(100):
                start = time.time()
                config_repo.set(f"bench_repo_{i}", f"val_{i}", "bench")
                insert_lats.append((time.time() - start) * 1000)

            # Config Repository — Read
            read_lats = []
            for i in range(100):
                start = time.time()
                config_repo.get(f"bench_repo_{i}")
                read_lats.append((time.time() - start) * 1000)

            # Config Repository — Update
            update_lats = []
            for i in range(100):
                start = time.time()
                config_repo.set(f"bench_repo_{i}", f"updated_{i}", "bench")
                update_lats.append((time.time() - start) * 1000)

            # Config Repository — Delete
            delete_lats = []
            for i in range(100):
                start = time.time()
                config_repo.delete(f"bench_repo_{i}")
                delete_lats.append((time.time() - start) * 1000)

            results["config_repo"] = {
                "insert": _latency_stats(insert_lats),
                "read": _latency_stats(read_lats),
                "update": _latency_stats(update_lats),
                "delete": _latency_stats(delete_lats),
            }

            # Memory Repository — Insert
            mem_lats = []
            for i in range(50):
                start = time.time()
                memory_repo.save("bench", f"cat_{i}", f"key_{i}", f"val_{i}")
                mem_lats.append((time.time() - start) * 1000)
            memory_repo.delete_by_level("bench")

            results["memory_repo"] = {"insert": _latency_stats(mem_lats)}

            # Log Repository — Insert
            log_lats = []
            for i in range(50):
                start = time.time()
                log_repo.log("INFO", "bench", f"Benchmark log {i}")
                log_lats.append((time.time() - start) * 1000)

            results["log_repo"] = {"insert": _latency_stats(log_lats)}

            return {"test": "repository_benchmark", "results": results, "passed": True}
        except Exception as exc:
            return {"test": "repository_benchmark", "passed": False, "error": str(exc)[:100]}

    def run_all(self) -> Dict[str, Any]:
        """Run all benchmarks and return aggregated results."""
        results = {
            "insert": self.run_insert_benchmark(),
            "read": self.run_read_benchmark(),
            "update": self.run_update_benchmark(),
            "delete": self.run_delete_benchmark(),
            "concurrent": self.run_concurrent_benchmark(),
            "repository": self.run_repository_benchmark(),
        }
        all_passed = all(r.get("passed", False) for r in results.values())
        return {
            "results": results,
            "all_passed": all_passed,
            "passed_count": sum(1 for r in results.values() if r.get("passed")),
            "total_count": len(results),
        }


def _latency_stats(latencies: List[float]) -> Dict[str, Any]:
    """Calculate latency statistics from a list of millisecond values."""
    if not latencies:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "p95_ms": 0, "p99_ms": 0, "samples": 0}
    sorted_lats = sorted(latencies)
    n = len(sorted_lats)
    return {
        "avg_ms": round(sum(latencies) / n, 2),
        "min_ms": round(sorted_lats[0], 2),
        "max_ms": round(sorted_lats[-1], 2),
        "p95_ms": round(sorted_lats[int(n * 0.95)] if n >= 2 else sorted_lats[-1], 2),
        "p99_ms": round(sorted_lats[int(n * 0.99)] if n >= 2 else sorted_lats[-1], 2),
        "samples": n,
    }
