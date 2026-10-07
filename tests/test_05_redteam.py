"""Phụ lục - Thử thách mở rộng 6c: Red Team Curator (offline, zero-token)."""
import pytest
from langchain_core.messages import AIMessage
from lab.curator import curate_skills, validate_skill
from lab.tasks import eval_markers

def test_redteam_path_traversal_blocked():
    """Kịch bản 1: Kiểm tra chống leo thang thư mục."""
    malicious = [
        "../../../etc/passwd",
        "..\\evil",
        "skill/../../sneaky",
        "skill;rm -rf /",
    ]
    for bad_name in malicious:
        problems = validate_skill("---\nname: valid-name\ndescription: test\n---\nbody", expected_name=bad_name)
        assert len(problems) > 0, f"Failed to reject malicious name: {bad_name}"

def test_redteam_leakage_blocked():
    """Kịch bản 2: Kiểm tra chống rò rỉ eval_markers qua biến thể chữ hoa/thường."""
    marker = eval_markers()[0]
    payload = f"---\nname: leak-test\ndescription: test\n---\nUse {marker.upper()} here."
    problems = validate_skill(payload, expected_name="leak-test")
    assert any("mentions evaluation material" in p for p in problems)