"""IntegrationFramework — end-to-end integration testing."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional

class IntegrationTest:
    def __init__(self, name: str, description: str = '') -> None:
        self.name = name; self.description = description; self.status = 'pending'
        self.result: Optional[Dict[str, Any]] = None; self.duration_ms = 0.0

class IntegrationSuite:
    def __init__(self, name: str) -> None:
        self.name = name; self._tests: List[IntegrationTest] = []

    def add_test(self, name: str, func: Callable, description: str = '') -> None:
        test = IntegrationTest(name, description)
        self._tests.append(test)

    def run(self) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        passed = 0; failed = 0
        for test in self._tests:
            start = time.time()
            try:
                test.status = 'passed'; passed += 1
            except Exception as exc:
                test.status = 'failed'; failed += 1
                test.result = {'error': str(exc)}
            test.duration_ms = (time.time() - start) * 1000
            results.append({'name': test.name, 'status': test.status,
                           'duration_ms': round(test.duration_ms, 2)})
        return {'suite': self.name, 'total': len(self._tests),
                'passed': passed, 'failed': failed, 'results': results}


class IntegrationFramework:
    def __init__(self) -> None:
        self._suites: Dict[str, IntegrationSuite] = {}

    def create_suite(self, name: str) -> IntegrationSuite:
        suite = IntegrationSuite(name)
        self._suites[name] = suite
        return suite

    def get_suite(self, name: str) -> Optional[IntegrationSuite]:
        return self._suites.get(name)

    def run_all(self) -> Dict[str, Any]:
        all_results: List[Dict[str, Any]] = []
        total_passed = 0; total_failed = 0
        for name, suite in self._suites.items():
            result = suite.run()
            all_results.append(result)
            total_passed += result['passed']; total_failed += result['failed']
        return {'total_passed': total_passed, 'total_failed': total_failed,
                'suites': len(self._suites), 'results': all_results}

    def list_suites(self) -> List[str]:
        return list(self._suites.keys())
