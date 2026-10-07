"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use this agent at the beginning of a task to inspect the workspace, read instructions, "
                "documentation, sample data, and logs without making changes. Pass the specific files or "
                "questions to investigate. The agent inspects and returns a factual report of schemas, "
                "file structures, or bug locations."
            ),
            "system_prompt": (
                "You are a dedicated workspace explorer. Your sole responsibility is to inspect files, "
                "read documentation, explore logs, and analyze schemas. Do NOT modify, create, or delete "
                "any files. Provide clear, objective, and structured findings so the primary agent can plan actions."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use this agent to carry out concrete code modifications, data processing scripts, or file "
                "transformations once requirements and root causes are established. Pass complete context, "
                "target files, and required outcomes. The agent executes edits and tests locally."
            ),
            "system_prompt": (
                "You are an implementation specialist. Your role is to write clean, correct code, apply file "
                "modifications, run tests, and execute scripts to resolve task requirements. Verify your work "
                "locally and return a concise summary of changes made and test execution results."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use this agent before finalizing a task to independently verify that all requirements, "
                "expected output files, schema specifications, and edge cases have been satisfied. "
                "Pass the task instructions and output file paths. The agent checks correctness without modifying files."
            ),
            "system_prompt": (
                "You are an independent reviewer and QA inspector. Your role is to rigorously check output files, "
                "verify data formats, run regression tests, and ensure adherence to all explicit rules and specifications. "
                "Do NOT modify any files. Report whether all requirements are satisfied or identify specific defects."
            ),
        },
    ]