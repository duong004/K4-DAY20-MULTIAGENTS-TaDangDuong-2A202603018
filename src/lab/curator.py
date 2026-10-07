"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(
    results_dir="results",
    source_condition="baseline",
    out_dir=None,
    model=None,
    max_skills: int = 3,
) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    source_dir = Path(results_dir) / source_condition
    if not source_dir.exists():
        return []

    target_dir = Path(out_dir) if out_dir is not None else (ROOT / "skills" / "auto")
    runs = []
    has_failed_check = False

    for run_dir in sorted(source_dir.iterdir()):
        run_file = run_dir / "run.json"
        if not run_file.is_file():
            continue

        try:
            data = json.loads(run_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Tuyệt đối không dùng dữ liệu của tác vụ đánh giá
        if data.get("role") != "learn":
            continue

        checks = data.get("checks", [])
        failed = [
            (c.get("name", ""), c.get("detail", ""))
            for c in checks
            if not c.get("passed", False)
        ]

        if failed:
            has_failed_check = True

        trace_file = run_dir / "trace.md"
        trace_tail = ""
        if trace_file.is_file():
            trace_content = trace_file.read_text(encoding="utf-8")
            trace_tail = trace_content[-6000:] if len(trace_content) > 6000 else trace_content

        runs.append({
            "task": data.get("task", run_dir.name),
            "failed": failed,
            "trace": trace_tail,
        })

    # Nếu không có run nào có check thất bại: in cảnh báo và không gọi LLM
    if not has_failed_check or not runs:
        print("không có check thất bại ở tác vụ học")
        return []

    # Xây dựng nội dung các lần chạy thất bại cho prompt
    runs_descriptions = []
    for r in runs:
        if not r["failed"]:
            continue
        lines = [f"### Learning Task: {r['task']}"]
        lines.append("Failed checks and review bot feedback (house rule violations):")
        for name, detail in r["failed"]:
            if detail:
                lines.append(f"- Check '{name}': {detail}")
            else:
                lines.append(f"- Check '{name}': (Failed without detail)")
        if r["trace"]:
            lines.append("Execution trace excerpt:")
            lines.append(r["trace"])
        runs_descriptions.append("\n".join(lines))

    runs_text = "\n\n".join(runs_descriptions)

    prompt = (
        f"You are an expert software and data engineering curator. You design reusable, highly focused SKILL modules "
        f"for an AI engineering agent.\n"
        f"Below are the failed checks (check names and reviewer feedback) and execution traces of previous learning runs.\n"
        f"Identify common PROCEDURAL mistakes and organizational conventions (such as output formats, cleaning steps, "
        f"regression testing, house rules) and write up to {max_skills} concise skills to prevent these mistakes on NEW tasks.\n\n"
        f"Strict rules for skills:\n"
        f"1. Skills must be general: do NOT mention task ids (like code-learn), do NOT mention task-specific filenames, "
        f"and do NOT hardcode answers or solutions.\n"
        f"2. Each skill must have YAML frontmatter containing `name` (lowercase letters, digits, and single hyphens only, e.g. acme-conventions) "
        f"and `description` (one clear sentence: WHEN to trigger and use this skill).\n"
        f"3. The body must be an actionable, imperative procedural checklist (under 40 lines).\n"
        f"4. Format EACH skill EXACTLY as follows:\n"
        f"=== SKILL: <name> ===\n"
        f"---\n"
        f"name: <name>\n"
        f"description: <when to use this skill>\n"
        f"---\n"
        f"<body checklist>\n"
        f"=== END ===\n\n"
        f"Failed learning runs:\n"
        f"{runs_text}\n"
    )

    active_model = model if model is not None else make_model()
    response = active_model.invoke(prompt)
    reply_content = getattr(response, "content", response)
    if isinstance(reply_content, list):
        reply_content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in reply_content
        )
    reply_content = str(reply_content)

    written_paths = []
    blocks = parse_skill_blocks(reply_content)

    for name, text in blocks:
        if len(written_paths) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue

        skill_file = target_dir / name / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(text.strip() + "\n", encoding="utf-8")
        written_paths.append(skill_file)

    return written_paths


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)