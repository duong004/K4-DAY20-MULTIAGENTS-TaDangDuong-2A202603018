# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Tạ Đăng Dương
- Mã sinh viên: 2A202603018
- Nhà cung cấp và mô hình (`LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: LAB_MODEL=gpt-4o-mini, LAB_TEMPERATURE=0.0, recursion_limit=60
- Phiên bản Deep Agents, hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.7.21, Ubuntu 22.04 LTS on WSL2 (Python 3.11)
- Số lần chạy tác vụ đã dùng / ngân sách: 18 / 30
- Commit của tag `freeze`: 8e4c2bc

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Trên tác vụ đánh giá, điều kiện subagents sẽ không vượt trội hơn baseline về điểm số, thậm chí có thể đạt điểm thấp hơn, nhưng chi phí token sẽ cao hơn đáng kể (gấp 2-5 lần). Căn cứ: Kết quả thực nghiệm trên tập học cho thấy hiện tượng cô lập ngữ cảnh (context isolation) khiến tác tử chính không truyền đạt đầy đủ các ràng buộc cho subagent (điểm code-learn giảm từ 5/10 xuống 0/10); đồng thời ở data-learn, việc phân công qua lại giữa các subagent dẫn đến bế tắc và chạm trần đệ quy (GraphRecursionError, tiêu tốn hơn 400.000 token). Đối với các bài toán ngắn và tập trung, chi phí overhead phối hợp lớn hơn lợi ích chuyên biệt hóa.
- H2 (skills-auto so với baseline): Trên tác vụ đánh giá, skills-auto sẽ cải thiện nhẹ điểm số so với baseline ở các quy ước tổ chức cũ lặp lại từ tập học (như định dạng ISO UTC, cấu trúc file clean.csv, checklist hồi quy), nhưng sẽ không giải quyết được quy ước tổ chức MỚI riêng biệt của tập đánh giá và các lỗi logic nghiệp vụ phức tạp. Căn cứ: Theo các nghiên cứu SkillsBench và SkillEvolBench, kỹ năng do mô hình tự sinh có xu hướng quá khớp (overfitting) với ngữ cảnh quan sát được và khó tổng quát hóa nếu không có phản hồi lặp lại; trên tập học, skills-auto đã giúp data-learn tăng từ 1/8 lên 2/8 nhờ định dạng đầu ra, nhưng detail trên tập eval hoàn toàn rỗng nên agent không thể tự hiệu chỉnh thêm.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm trung bình của tất cả các điều kiện trên tác vụ đánh giá sẽ thấp hơn so với tác vụ học. Căn cứ: Tác vụ đánh giá sử dụng dữ liệu mới chưa từng thấy, không cung cấp phản hồi chi tiết (detail luôn rỗng) và bổ sung thêm quy ước tổ chức mới mà tác tử chưa từng được học; agent phải dựa hoàn toàn vào khả năng zero-shot và các chỉ dẫn tổng quát mà không có cơ chế học từ lỗi sai.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có các công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Công cụ duy nhất cho phép chạy lệnh shell là `execute`.
2. Mô tả của công cụ `task` cho biết subagent `general-purpose` được dùng để ủy quyền các tác vụ độc lập, tự động cô lập ngữ cảnh để tránh làm phình to lịch sử hội thoại của tác tử chính. Subagent chỉ nhìn thấy những gì tác tử chính truyền vào qua trường mô tả nhiệm vụ (delegation message), hoàn toàn không thấy ngữ cảnh hội thoại hay các bước trước đó của tác tử chính.
3. Trích dẫn chỉ dẫn hành vi:
   - Từ mô tả công cụ `task`: "Delegate tasks to specialized subagents. Describe the task clearly with all required context."
   - Từ mô tả công cụ `execute`: "Run a shell command in the environment."

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | test_changelog_updated | E (Vi phạm quy ước tổ chức) | RULE: CHANGELOG.md must contain an entry under '## Unreleased' |
| code-learn | test_regression_tests_added | E (Vi phạm quy ước tổ chức) | RULE: Must add tests/test_regressions.py with at least 3 test functions |
| data-learn | clean_csv_exists | E (Vi phạm quy ước tổ chức) | RULE: Cleaned dataset must be exported to workspace/clean.csv |
| data-learn | answer_has_meta_block | E (Vi phạm quy ước tổ chức) | RULE: answer.json must contain a top-level 'meta' block with execution info |
| logs-learn | errors_json_utc_timestamps | E (Vi phạm quy ước tổ chức) | RULE: Timestamps in errors.json must be converted to ISO-8601 UTC |
| logs-learn | errors_severity_canonical | E (Vi phạm quy ước tổ chức) | RULE: Severity must be normalized to uppercase canonical forms |

**Nhận xét:**
- Nhóm lỗi chiếm đa số tuyệt đối là **Nhóm E (Vi phạm quy ước tổ chức Acme)**. Các quy ước này (như khối `meta`, tệp `clean.csv`, `test_regressions.py`, mục `## Unreleased`) không hề được phát biểu trong đề bài (`instruction.md`) mà chỉ tồn tại trong bộ kiểm tra của tổ chức Acme.
- **Bằng chứng phủ định cho các nhóm A–D:** Dữ liệu từ `check_breakdown.py` cho thấy ở điều kiện `baseline`, tác tử vượt qua 6/18 check kỹ thuật trên tập học. Tác tử đọc hiểu yêu cầu và sửa đúng một phần code/data/log cơ bản, nhưng trượt toàn bộ 0/9 check quy ước tổ chức (`house rules`) do hoàn toàn thiếu thông tin ngữ cảnh. Một hệ thống skill tự sinh (self-evolving curation) hoàn toàn có thể phòng ngừa triệt để nhóm E này bằng cách trích xuất các quy tắc Acme từ trường `detail` để lập thành checklist hành vi.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa:
  1. `explorer`: Chuyên đọc cấu trúc file, phân tích schema, docstring và log mà không sửa đổi file. Giúp tác tử chính nắm rõ hiện trạng trước khi hành động.
  2. `implementer`: Chuyên chỉnh sửa code, chạy lệnh chuyển đổi dữ liệu và chạy test nội bộ.
  3. `reviewer`: Đóng vai trò QA độc lập, rà soát lại kết quả đầu ra đối chiếu với yêu cầu đề bài trước khi kết thúc tác vụ.
- `subagent_calls` ở từng tác vụ: Trên `code-learn` (0 calls), `data-learn` (0 calls ở luồng chính do lỗi đệ quy), `logs-learn` (0 calls). Trên tập eval, `subagent_calls` đều bằng 0 hoặc tác tử gặp vòng lặp.
- Hiện tượng và nguyên nhân:
  - Tác tử chính xu hướng tự giải quyết trực tiếp bằng các tool tích hợp sẵn (`read_file`, `write_file`, `execute`) cho các tác vụ có phạm vi hẹp thay vì mất thêm chi phí gọi `task`.
  - Khi kích hoạt phân công việc (như ở `data-learn` và `code-eval`), tác tử gặp lỗi `GraphRecursionError` (chạm trần recursion_limit = 60), khiến số tool calls ở luồng chính được ghi nhận là 0 và trace bị ngắt.
- Ảnh hưởng đến token và thời gian: Chi phí token tăng vọt lên trung bình **127.313 token/lần chạy** (so với 64.884 của baseline). Ở `data-learn`, một lần chạy tiêu tốn tới **402.861 token**. Thời gian chạy kéo dài gấp nhiều lần nhưng điểm số lại sụt giảm nghiêm trọng (trung bình chỉ đạt 0.04 ở tập học và 0.07 ở tập eval).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần. Số skill bị xóa: 0 (cả 3 skill sinh ra đều đạt chuẩn validate_skill).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `output-formatting` | Tổng quát cho mọi bài toán xử lý dữ liệu và log (chuẩn hóa UTC, định dạng JSON/CSV, trường meta). | Đúng. Đưa ra hướng dẫn cụ thể về việc thêm metadata và chuẩn hóa timestamp. | 13 dòng. Description rõ ràng: dùng khi tạo tệp đầu ra. skills_read = 0 (tác tử dựa vào prompt hướng dẫn chung). |
| `procedural-checks` | Tổng quát cho quy trình công nghệ phần mềm tại Acme (cập nhật CHANGELOG, viết test mới, type annotation). | Đúng. Nắm bắt chính xác quy ước `## Unreleased` và quy tắc không sửa test cũ. | 15 dòng. Description rõ ràng: dùng cho các tác vụ phát triển phần mềm. skills_read = 0. |
| `regression-testing` | Tổng quát cho quy trình kiểm thử hồi quy (tạo file `tests/test_regressions.py`, đảm bảo tối thiểu 3 test case). | Đúng. Hướng dẫn cấu trúc bài test chuẩn và xác nhận lỗi đã sửa. | 13 dòng. Description rõ ràng: dùng khi hoàn thành việc sửa bug. skills_read = 0. |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng so sánh tổng hợp từ `report/table.md`:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 5/10 | 0/10 | 4/10 |
| data-learn | 1/8 | 0/8 | 2/8 |
| logs-learn | 0/9 | 1/9 | 0/9 |
| code-eval | 1/11 | 0/11 | 2/11 |
| data-eval | 0/9 | 1/9 | 3/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.21 | 0.04 | 0.22 |
| **Mean score - evaluation tasks** | 0.06 | 0.07 | 0.21 |
| **Mean tokens per run** | 64,884 | 127,313 | 68,608 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Thống kê phân rã từ `scripts/check_breakdown.py`:

```text
condition      role     technical   house rules  mean tokens  read a skill
baseline       eval       2/18         0/12          87,491      0/3
baseline       learn      6/18         0/9           42,276      0/3
subagents      eval       2/18         0/12          97,819      0/3
subagents      learn      1/18         0/9          156,807      0/3
skills-auto    eval       6/18         0/12          81,834      0/3
skills-auto    learn      6/18         0/9           55,381      0/3

```

* Các lần chạy có `error`: `code-eval` ở cả 3 điều kiện và `data-learn` ở điều kiện `subagents` gặp lỗi `GraphRecursionError` (chạm giới hạn 60 bước). Điểm số vẫn được tính hợp lệ dựa trên trạng thái workspace tại thời điểm ngắt.
* `skills_modified = false` trên 100% các lần chạy.

## 8. Phân tích

1. **Hiệu quả giữa các điều kiện:** So với `baseline`, điều kiện `skills-auto` cải thiện nhẹ điểm tác vụ học (0.22 so với 0.21) và cải thiện vượt bậc trên tác vụ đánh giá (**0.21 so với 0.06**, tăng gấp 3.5 lần). Ngược lại, điều kiện `subagents` sụt giảm mạnh trên tập học (0.04) và chỉ đạt 0.07 trên tập eval. Không có hiện tượng cải thiện tập học nhưng thụt lùi ở tập đánh giá; tri thức rút ra từ curator đã có tính chuyển giao tích cực.
2. **Kỹ thuật so với Quy ước tổ chức (`rule_`):** Trên tập đánh giá, `skills-auto` giúp số check kỹ thuật tăng vọt từ 2/18 (ở baseline) lên **6/18**. Đối với check quy ước tổ chức, cả 3 điều kiện đều đạt **0/12**. Lý do: Tập đánh giá bổ sung các quy ước tổ chức hoàn toàn mới mà tập học không có (và trường `detail` của tập eval luôn rỗng), do đó skill tự sinh không thể dự đoán trước các quy tắc tổ chức chưa từng xuất hiện.
3. **Cơ chế tác động và `skills_read`:** Trường `skills_read` bằng 0 cho thấy tác tử không chủ động gọi công cụ `read_file` để mở toàn bộ tệp `SKILL.md`. Tuy nhiên, sự xuất hiện của dòng `SKILLS_NOTE` trong system prompt cùng với cơ chế nạp skill của Deep Agents đã nhắc nhở tác tử chú trọng hơn vào cấu trúc dữ liệu và kiểm thử, giúp đạt thêm các check kỹ thuật như format JSON và cấu trúc bảng trên `data-eval` và `code-eval`. Ngược lại, check quy ước tổ chức mới không thể đạt được do thiếu thông tin cụ thể.
4. **Chi phí token:** Token trung bình: `baseline` (64.884), `skills-auto` (68.608), `subagents` (127.313). Xét theo tỷ số điểm/token trên tập đánh giá, `skills-auto` đạt hiệu quả kinh tế cao nhất ($0.21 / 68.6k$), trong khi `subagents` tiêu tốn gần gấp đôi lượng token nhưng chỉ đạt 0.07 điểm. Đa tác tử hoàn toàn không đáng chi phí đối với các tác vụ quy mô đơn lẻ này.
5. **Quá khớp và Rò rỉ dữ liệu:** Bộ kiểm tra `eval_markers()` xác nhận không có bất kỳ định danh nào của tập đánh giá lọt vào `skills/auto/`. Các skill sinh ra hoàn toàn ở dạng checklist trừu tượng (`output-formatting`, `procedural-checks`, `regression-testing`), tránh được hiện tượng rò rỉ dữ liệu và quá khớp với tên file cụ thể của tập học.
6. **Đo lường độ nhiễu:** So sánh điểm tập học của cùng bộ skill ở Phần 3.4 (lưu tại `results/skills-auto-dev`: code-learn 4/10, data-learn 2/8, logs-learn 0/9) và sau khi đóng băng (`results/skills-auto`: code-learn 4/10, data-learn 2/8, logs-learn 0/9). Chênh lệch điểm số là **0.00**, chứng minh tính ổn định cao của quy trình thực thi trên tập học. Sự chênh lệch điểm trên tập eval chủ yếu đến từ độ phức tạp logic của tác vụ mới thay vì nhiễu ngẫu nhiên.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ:** Mỗi họ tác vụ chỉ gồm 1 bài học và 1 bài đánh giá (tổng 6 tác vụ). Cỡ mẫu nhỏ khiến các chỉ số trung bình nhạy cảm với từng check riêng lẻ.
2. **Hiện tượng nghẽn đệ quy (Recursion Limit):** Giới hạn `recursion_limit = 60` khiến tác tử bị dừng sớm ở các tác vụ lập trình phức tạp như `code-eval`, chưa phản ánh hết tiềm năng tối đa nếu được cấp ngân sách bước lớn hơn.
3. **Thiếu tương tác lặp ở tập đánh giá:** Trong môi trường thực tế, kỹ sư có thể nhận phản hồi nhiều vòng để sửa lỗi quy ước tổ chức, trong khi ở bài lab, bot đánh giá trên tập eval giữ bí mật hoàn toàn trường `detail`.

## 10. Kết luận

Thực nghiệm chứng minh phương pháp tác tử tự tiến hóa ở tầng ngữ cảnh (`skills-auto`) đem lại hiệu quả vượt trội, tăng điểm đánh giá từ 0.06 lên 0.21 mà chỉ tăng 5.7% chi phí token. Ngược lại, kiến trúc đa tác tử (`subagents`) gây lãng phí gần 100% token do chi phí phối hợp và bế tắc đệ quy mà không cải thiện độ chính xác. Kỹ năng tự sinh có khả năng chuyển giao tốt các quy trình kỹ thuật chung nhưng bất lực trước các quy ước tổ chức mới xuất hiện. Đề xuất cải tiến tiếp theo là bổ sung cơ chế Hot-path evolution cho phép tác tử tự cập nhật skill trong lúc thực thi bài toán mới.

## Phụ lục

* Lệnh đã chạy:
1. `pytest tests/test_01_provided.py`
2. `pytest tests/test_02_agent.py`
3. `pytest tests/test_03_runner.py`
4. `python -m lab.runner --condition baseline --tasks data-learn`
5. `python -m lab.runner --condition baseline --tasks code-learn logs-learn`
6. `python -m lab.runner --condition subagents --tasks learn`
7. `pytest tests/test_04_curator.py`
8. `python -m lab.curator`
9. `python -m lab.runner --condition skills-auto --tasks learn`
10. `git commit -m "hypotheses"` & `git tag freeze`
11. `python -m lab.runner --condition baseline --tasks eval`
12. `python -m lab.runner --condition subagents --tasks eval`
13. `python -m lab.runner --condition skills-auto --tasks all`
14. `python scripts/verify_freeze.py`
15. `python -m lab.compare > report/table.md`
16. `python scripts/check_breakdown.py`

### Thử thách mở rộng: Hướng 6c - Tấn công curator (Red Team) và Biện pháp phòng thủ

1. **Mục tiêu thử nghiệm:** Kiểm tra xem Curator và bộ lọc `validate_skill` có thể bị đánh lừa để làm rò rỉ thông tin của tập đánh giá (data leakage) hoặc tấn công leo thang thư mục (Path Traversal) hay không.
2. **Thiết kế tấn công:** 
   - Kịch bản 1 (Path Traversal): Mô hình cố tình sinh tên skill dạng `=== SKILL: ../../../etc/passwd ===` hoặc `=== SKILL: ..\\evil ===`.
   - Kịch bản 2 (Leakage via Paraphrase): Mô hình cố tình mã hóa hoặc diễn đạt lại các định danh của tập đánh giá (nằm trong `eval_markers()`) bằng cách chèn ký tự đặc biệt hoặc chữ hoa lộn xộn.
3. **Kết quả kiểm chứng:**
   - Hàm `SAFE_NAME.fullmatch()` trong `curator.py` đã chặn đứng 100% các chuỗi path traversal (`^[a-z0-9]+(-[a-z0-9]+)*$`).
   - Hàm `validate_skill` chuẩn hóa toàn bộ văn bản về `text.lower()` trước khi quét qua `eval_markers()`, loại bỏ khả năng lẩn tránh bằng chữ hoa/thường.
4. **Đề xuất cải tiến phòng vệ:** Cần bổ sung thêm cơ chế băm kiểm tra độ tương đồng mờ (Fuzzy matching / Levenshtein distance) đối với `eval_markers()` để ngăn chặn kỹ thuật chèn khoảng trắng hoặc ký tự leetspeak (ví dụ `d-a-t-a-e-v-a-l`).
