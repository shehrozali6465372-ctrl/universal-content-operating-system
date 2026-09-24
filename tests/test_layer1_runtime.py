from layers.layer01_core import Layer1Runtime

def test_layer1_runtime_start_health_shutdown(tmp_path, monkeypatch):
    runtime = Layer1Runtime(project_root=str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    runtime.start(profile="development", master_key="runtime-test-master-key")
    report = runtime.health_check()
    assert report["liveness"] is True
    assert report["ready"] is True
    assert report["overall"] == "PASS"
    runtime.shutdown()
    assert runtime.is_ready is False


class _Backend:
    def health_check(self):
        return {"overall": "PASS", "checks": {}}
    def close(self):
        self.closed = True


def test_production_requires_layer13_backends(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "test-page")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "test-token")
    runtime = Layer1Runtime(project_root=str(tmp_path))
    import pytest
    with pytest.raises(RuntimeError, match="Layer 13 PostgreSQL"):
        runtime.start(profile="production", master_key="runtime-test-master-key")


def test_production_accepts_explicit_persistence_backends(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "test-page")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "test-token")
    runtime = Layer1Runtime(project_root=str(tmp_path))
    db = _Backend()
    memory = _Backend()
    runtime.start(
        profile="production",
        master_key="runtime-test-master-key",
        database_backend=db,
        memory_backend=memory,
    )
    assert runtime.health_check()["ready"] is True
    runtime.shutdown()


def test_production_runtime_contracts_with_real_layer13_postgresql(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "test-page")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "test-token")
    from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager

    pg = PostgreSQLManager()
    assert pg.initialize() is True

    class _L13MemoryLifecycle:
        """Layer 1 lifecycle adapter over the real Layer 13 memory repository."""
        def health_check(self):
            return pg.health_check()

        def save(self, *args, **kwargs):
            return pg.memory.save(*args, **kwargs)

        def load(self, *args, **kwargs):
            return pg.memory.load(*args, **kwargs)

        def search(self, *args, **kwargs):
            return pg.memory.search(*args, **kwargs)

        def increment_access(self, *args, **kwargs):
            return pg.memory.increment_access(*args, **kwargs)

        def get_by_level(self, *args, **kwargs):
            return pg.memory.get_by_level(*args, **kwargs)

        def delete_by_level(self, *args, **kwargs):
            return pg.memory.delete_by_level(*args, **kwargs)

        def close(self):
            # PostgreSQLManager owns the shared pool lifecycle.
            return None

    runtime = Layer1Runtime(project_root=str(tmp_path))
    try:
        runtime.start(
            profile="production",
            master_key="runtime-test-master-key",
            database_backend=pg,
            memory_backend=_L13MemoryLifecycle(),
        )
        assert runtime.health_check()["ready"] is True
    finally:
        runtime.shutdown()


class _FailingBackend:
    def health_check(self):
        return {"overall": "FAIL", "checks": {"connection": {"status": "FAIL"}}}
    def close(self):
        self.closed = True


def test_production_start_fails_closed_on_unhealthy_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "test-page")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "test-token")
    runtime = Layer1Runtime(project_root=str(tmp_path))
    import pytest
    with pytest.raises(RuntimeError, match="startup health check"):
        runtime.start(
            profile="production",
            master_key="runtime-test-master-key",
            database_backend=_FailingBackend(),
            memory_backend=_FailingBackend(),
        )
    assert runtime.is_ready is False
