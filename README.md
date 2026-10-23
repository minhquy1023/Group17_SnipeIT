# Group 17 – Kiểm thử phần mềm Snipe-IT

Đồ án môn Kiểm thử phần mềm (Software Testing 2027) – Trường ĐH Nông Lâm TP.HCM.

## Hệ thống được kiểm thử

| Thông tin | Chi tiết |
|---|---|
| Hệ thống | Snipe-IT – phần mềm mã nguồn mở quản lý tài sản CNTT |
| Phiên bản | v8.8.1 (bản demo tại thời điểm test) |
| Website test | https://demo.snipeitapp.com |
| Tài liệu tham chiếu | https://snipe-it.readme.io |
| Trình duyệt | Google Chrome (bản mới nhất), Firefox |
| Công cụ automation | Katalon Studio |

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
| `AutomationPlan/` | Kế hoạch automation test |

## Quy trình làm việc với Git

- `main`: bản hoàn chỉnh của đồ án
- `dev`: bản tích hợp của nhóm
- Mỗi thành viên làm trên nhánh riêng `MaSV-HoTen`, tạo Pull Request vào `dev`, nhóm trưởng duyệt và merge.

## Tiến độ

| Tuần | Nội dung | Trạng thái |
|---|---|---|
| ASM6 (19/10 – 23/10) | Test design 3 chức năng, test case chức năng đầu tiên của mỗi thành viên | Đang thực hiện |
