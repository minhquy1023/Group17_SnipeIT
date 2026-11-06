# Group 17 – Kiểm thử phần mềm Snipe-IT

Đồ án môn Kiểm thử phần mềm (Software Testing 2027) – Trường ĐH Nông Lâm TP.HCM.

## Hệ thống được kiểm thử

| Thông tin | Chi tiết |
|---|---|
| Hệ thống | Snipe-IT – phần mềm mã nguồn mở quản lý tài sản CNTT |
| Phiên bản | v8.8.1 (ASM6, test ngày 22/10/2026); v8.8.3 build 26143 (ASM7, ASM8, từ ngày 28/10/2026) |
| Website test | https://demo.snipeitapp.com |
| Tài liệu tham chiếu | https://snipe-it.readme.io |
| Trình duyệt | Google Chrome (bản mới nhất), Firefox; Chromium (khi chạy automation) |
| Công cụ automation | Playwright (Python) + pytest |

## Thành viên

| STT | MSSV | Họ tên | Vai trò | GitHub | Nhóm chức năng |
|---|---|---|---|---|---|
| 1 | 21130507 | Trịnh Minh Quý | Nhóm trưởng | @minhquy1023 | E – Danh mục nền |
| 2 | 23130056 | Phạm Hữu Đạt | Thành viên | @phamdat12345 | B – Phần mềm và cấu hình |
| 3 | 23130303 | Nguyễn Hữu Thanh | Thành viên | @H-thanh0603 | A – Tài sản |
| 4 | 23130138 | Tạ Văn Huy | Thành viên | @23130138 | C – Vật tư |
| 5 | 21130420 | Bùi Trọng Linh | Thành viên | @linhbuitrong | D – Con người và tổ chức |

## Phân công chức năng

| Nhóm | Người phụ trách | Chức năng 1 | Chức năng 2 | Chức năng 3 |
|---|---|---|---|---|
| A – Tài sản | Nguyễn Hữu Thanh | Quản lý tài sản (Asset) | Cấp phát và thu hồi (Checkout) | Mẫu tài sản (Model) |
| B – Phần mềm và cấu hình | Phạm Hữu Đạt | Bản quyền phần mềm (License) | Bộ tài sản định sẵn (Kit) | Trường tùy chỉnh (Field) |
| C – Vật tư | Tạ Văn Huy | Phụ kiện (Accessory) | Vật tư tiêu hao (Consumable) | Linh kiện (Component) |
| D – Con người và tổ chức | Bùi Trọng Linh | Người dùng (User) | Phòng ban (Department) | Địa điểm (Location) |
| E – Danh mục nền | Trịnh Minh Quý | Danh mục (Category) | Nhà sản xuất (Manufacturer) | Nhà cung cấp (Supplier) |

## Cấu trúc thư mục

| Thư mục / File | Nội dung |
|---|---|
| `Automation Testing Project - Group 17/` | Project automation đã tích hợp script của các thành viên thành một Test Suite (ASM8). Hướng dẫn cài đặt, cấu hình và chạy: xem `README.md` trong thư mục này |
| `Test Report - Group 17/` | Báo cáo kết quả chạy toàn bộ Test Suite (HTML, XML) và bản tóm tắt kết quả |
| `Envidence - Group17/` | Minh chứng quá trình thực thi: log, ảnh chụp, trace của các test hỏng |
| `Automation/MaSV_HoTen_ASM7.py` | Script automation 3 chức năng của từng thành viên, bản nộp ASM7 (giữ nguyên để đối chiếu) |
| `TestCases/Group17_MaSV_HoTen.xlsx` | Test design và test case 3 chức năng của từng thành viên |
| `TestCases/Group17_SnipeIT.xlsx` | Tài liệu test case gộp của cả nhóm (đang cập nhật) |
| `AutomationPlan/` |    Kế hoạch automation test: công cụ, tiêu chí chọn test case, quy trình chạy và phân loại lỗi (sơ đồ và checklist) |

## Chạy Test Suite của nhóm

Yêu cầu: Python 3.12 trở lên. Mở PowerShell tại thư mục gốc repo:

```powershell
cd "Automation Testing Project - Group 17"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

# Toàn bộ Test Suite
python -m pytest -v

# Riêng phần của một thành viên
python -m pytest tests/test_21130507_TrinhMinhQuy.py -v
```

Tên thư mục có khoảng trắng nên luôn đặt trong ngoặc kép. Các tùy chọn xuất báo cáo, chạy có trình duyệt và chạy lại test hỏng được hướng dẫn trong `Automation Testing Project - Group 17/README.md`. Mỗi hàm test ứng với một test case trong file Excel của thành viên (ví dụ `test_category_03_...` là [Category-3]). Dữ liệu test có tiền tố `G17_` và được script tự xóa sau khi chạy.

## Trạng thái tích hợp ASM8

| Thành viên | File trong `tests/` | Số test | Pull Request |
|---|---|---|---|
| Trịnh Minh Quý | `test_21130507_TrinhMinhQuy.py` | 86 | #20, #21, #25 |
| Tạ Văn Huy | `test_23130138_TaVanHuy.py` | 74 | #23 |
| Bùi Trọng Linh | `test_21130420_BuiTrongLinh.py` | 66 | #22 |
| Nguyễn Hữu Thanh | `test_23130303_NguyenHuuThanh.py` | 46 | #27 |
| Phạm Hữu Đạt | Chưa tích hợp (script ASM7 có trong `Automation/`) | – | – |
| **Tổng** | | **272** | |

## Quy trình làm việc với Git

- `main`: bản hoàn chỉnh của đồ án
- `dev`: bản tích hợp của nhóm
- Mỗi thành viên làm trên nhánh riêng `MaSV-HoTen` (tạo từ `dev`), tạo Pull Request vào `dev`, nhóm trưởng duyệt code và merge. Sau đó nhóm trưởng merge `dev` vào `main`.
- `main` và `dev` được bảo vệ bằng ruleset: mọi thay đổi phải đi qua Pull Request.
- Tiêu đề Pull Request: `[ASMx] Họ tên – Nội dung`. Commit message bằng tiếng Anh, bắt đầu bằng động từ (Add, Update, Fix).
- Tên file không dấu, không khoảng trắng. Mỗi thành viên chỉ sửa file của mình; `conftest.py`, `helpers.py`, `pytest.ini`, `requirements.txt` do nhóm trưởng quản lý.

## Tiến độ

| Tuần | Nội dung | Trạng thái |
|---|---|---|
| ASM6 (19/10 – 23/10) | Test design 3 chức năng, test case chức năng đầu tiên của mỗi thành viên | Hoàn thành |
| ASM7 (24/10 – 30/10) | Script automation 3 chức năng của mỗi thành viên | Hoàn thành |
| ASM8 (31/10 – 06/11) | Tích hợp script thành một project, chạy toàn bộ Test Suite, Test Report | Tích hợp 4/5 thành viên; Test Report cập nhật trong `Test Report - Group 17/` |
