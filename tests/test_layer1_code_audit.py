from tools.layer1_code_audit import audit

def test_layer1_complete_static_inventory():
    report = audit()
    summary = report["summary"]
    assert summary["module_count"] == 38
    assert summary["class_count"] >= 165
    assert summary["function_method_count"] >= 743
    assert summary["syntax_errors"] == 0
    # Duplicate/orphan results are evidence for review; they must never be
    # silently ignored by the gate.
    assert "duplicate_body_groups" in report
    assert "orphan_candidates" in report
