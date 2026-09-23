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
