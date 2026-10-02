"""Static contract checks for the CI-only DeepSeek credential smoke test."""

from pathlib import Path


def test_deepseek_smoke_workflow_uses_secret_and_does_not_echo_it() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "secrets.DEEPSEEK_API_KEY" in workflow
    assert "Authorization: Bearer \${DEEPSEEK_API_KEY}" in workflow
    assert "DEEPSEEK_API_TEST=PASS" in workflow
    assert "echo \${DEEPSEEK_API_KEY}" not in workflow
