# Group 17 – Kiểm thử phần mềm Snipe-IT

Đồ án môn Kiểm thử phần mềm (Software Testing 2027) – Trường ĐH Nông Lâm TP.HCM.

## Hệ thống được kiểm thử

| Thông tin | Chi tiết |
|---|---|
| Hệ thống | Snipe-IT – phần mềm mã nguồn mở quản lý tài sản CNTT |
| Phiên bản | v8.8.1 (ASM6, test ngày 22/10/2026); v8.8.3 build 26143 (ASM7, từ ngày 28/10/2026) |
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
| `TestCases/Group17_MaSV_HoTen.xlsx` | Test design và test case 3 chức năng của từng thành viên |
| `TestCases/Group17_SnipeIT.xlsx` | Tài liệu test case đã gộp của cả nhóm (nhóm trưởng cập nhật) |
| `Automation/MaSV_HoTen_ASM7.*` | Script automation 3 chức năng của từng thành viên (ASM7) |
| `AutomationPlan/` | Kế hoạch automation test (đang cập nhật) |

## Chạy script automation

Yêu cầu: Python 3.12 trở lên. Cách chạy chi tiết của từng script được ghi ở đầu mỗi file.

```
pip install pytest-playwright
playwright install chromium
python -m pytest Automation/21130507_TrinhMinhQuy_ASM7.py -v
```

Thêm `--headed --slowmo 500` để xem trình duyệt thao tác. Mỗi hàm test ứng với một test case trong file Excel (ví dụ `test_category_03_...` là [Category-3]). Mọi dữ liệu test có tiền tố `G17_` và được script tự xóa sau khi chạy.

## Quy trình làm việc với Git

- `main`: bản hoàn chỉnh của đồ án
- `dev`: bản tích hợp của nhóm
- Mỗi thành viên làm trên nhánh riêng `MaSV-HoTen` (tạo từ `dev`), tạo Pull Request vào `dev`, nhóm trưởng duyệt và merge. Sau đó nhóm trưởng merge `dev` vào `main`.
- Tiêu đề Pull Request: `[ASMx] Họ tên – Nội dung`. Commit message bằng tiếng Anh, bắt đầu bằng động từ (Add, Update, Fix).
- Tên file không dấu, không khoảng trắng. Mỗi thành viên chỉ sửa file của mình.

## Tiến độ

| Tuần | Nội dung | Trạng thái |
|---|---|---|
| ASM6 (19/10 – 23/10) | Test design 3 chức năng, test case chức năng đầu tiên của mỗi thành viên | Hoàn thành |
| ASM7 (24/10 – 30/10) | Script automation 3 chức năng của mỗi thành viên | Đang thực hiện |
