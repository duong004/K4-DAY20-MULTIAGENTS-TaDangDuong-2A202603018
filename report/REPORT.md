# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên:
- Mã sinh viên:

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`:
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker:
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag freeze, Phần 4.0)

- H1 (subagents so với baseline): Trên tác vụ đánh giá, điều kiện subagents sẽ không vượt trội hơn baseline về điểm số, thậm chí có thể đạt điểm thấp hơn, nhưng chi phí token sẽ cao hơn đáng kể (gấp 2-5 lần). Căn cứ: Kết quả thực nghiệm trên tập học cho thấy hiện tượng cô lập ngữ cảnh (context isolation) khiến tác tử chính không truyền đạt đầy đủ các ràng buộc cho subagent (điểm code-learn giảm từ 5/10 xuống 0/10); đồng thời ở data-learn, việc phân công qua lại giữa các subagent dẫn đến bế tắc và chạm trần đệ quy (GraphRecursionError, tiêu tốn hơn 400.000 token). Đối với các bài toán ngắn và tập trung, chi phí overhead phối hợp lớn hơn lợi ích chuyên biệt hóa.
- H2 (skills-auto so với baseline): Trên tác vụ đánh giá, skills-auto sẽ cải thiện nhẹ điểm số so với baseline ở các quy ước tổ chức cũ lặp lại từ tập học (như định dạng ISO UTC, cấu trúc file clean.csv, checklist hồi quy), nhưng sẽ không giải quyết được quy ước tổ chức MỚI riêng biệt của tập đánh giá và các lỗi logic nghiệp vụ phức tạp. Căn cứ: Theo các nghiên cứu SkillsBench và SkillEvolBench, kỹ năng do mô hình tự sinh có xu hướng quá khớp (overfitting) với ngữ cảnh quan sát được và khó tổng quát hóa nếu không có phản hồi lặp lại; trên tập học, skills-auto đã giúp data-learn tăng từ 1/8 lên 2/8 nhờ định dạng đầu ra, nhưng detail trên tập eval hoàn toàn rỗng nên agent không thể tự hiệu chỉnh thêm.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm trung bình của tất cả các điều kiện trên tác vụ đánh giá sẽ thấp hơn so với tác vụ học. Căn cứ: Tác vụ đánh giá sử dụng dữ liệu mới chưa từng thấy, không cung cấp phản hồi chi tiết (detail luôn rỗng) và bổ sung thêm quy ước tổ chức mới mà tác tử chưa từng được học; agent phải dựa hoàn toàn vào khả năng zero-shot và các chỉ dẫn tổng quát mà không có cơ chế học từ lỗi sai.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ:
   - Nhóm thao tác tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
   - Nhóm thực thi shell: `execute`.
   - Nhóm đa tác tử: `task`.
   Công cụ cho phép chạy lệnh là `execute`.

2. Mô tả của công cụ `task` về subagent `general-purpose`:
   - Đây là tác tử đa năng dùng để nghiên cứu các câu hỏi phức tạp, tìm kiếm file/nội dung, và thực thi các chuỗi nhiệm vụ nhiều bước ("General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks"). Nó có đầy đủ công cụ như tác tử chính.
   - Về ngữ cảnh: Subagent hoạt động ở chế độ phi trạng thái (stateless); nó chỉ nhìn thấy prompt cụ thể được giao trong lượt gọi đó và trả về báo cáo cuối cùng ("the agent sees only the prompt you give it and returns a single final report"), hoàn toàn không nhìn thấy lịch sử hội thoại trước đó của tác tử chính (context isolation).

3. Trích dẫn câu hướng dẫn hành vi:
   - Từ mô tả công cụ `task`: *"Tell the agent whether to create content, analyze, or only research, since it can't necessarily see the user's intent unless it inherits your conversation, as noted per agent type below."*
   - Từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| | | | |

Nhận xét: nhóm lỗi nào chiếm đa số? Skill có thể phòng ngừa nhóm đó không?

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):
- Ảnh hưởng đến token và thời gian:

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do:

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| | | | |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Bạn đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
