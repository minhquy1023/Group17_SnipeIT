# Test Report - Group 17

Báo cáo kết quả chạy toàn bộ Test Suite của **Automation Testing Project - Group 17** (ASM8), kiểm thử Snipe-IT trên https://demo.snipeitapp.com.

## 1. Thông tin lần chạy

| Mục | Chi tiết |
|---|---|
| Mã commit | `99a4bd4` (nhánh `dev`, sau khi merge Pull Request #27) |
| Thời gian | 06/11/2026 22:32 – 07/11/2026 khoảng 02:28 (gồm 2 lần chạy lại) |
| Hệ thống được test | Snipe-IT v8.8.3 build 26143, bản demo online dùng chung |
| Môi trường | Windows 11, Python 3.12.10, pytest 9.1.1, pytest-playwright 0.10.0, Chromium; mạng Wi-Fi |
| Số test | 272: Trịnh Minh Quý 86, Tạ Văn Huy 74, Bùi Trọng Linh 66, Nguyễn Hữu Thanh 46 |
| Chưa tích hợp | Phạm Hữu Đạt (script ASM7 có trong `Automation/`, chưa chuyển sang `tests/`) |

Lệnh chạy (trong thư mục `Automation Testing Project - Group 17`):

```powershell
python -m pytest -v --html="../Test Report - Group 17/TestReport_Group17.html" --self-contained-html --junitxml="../Test Report - Group 17/TestReport_Group17.xml" --screenshot only-on-failure --tracing retain-on-failure --output results_group
```

Sau lần chạy đầu, các test hỏng được chạy lại bằng `--lf` (lần 2), rồi chạy lại riêng các test hỏng vì môi trường (lần 3).

## 2. Kết quả từng lần chạy

| Lần chạy | Số test | Passed | Failed | Skipped | xfailed | Error | Thời gian | Báo cáo |
|---|---|---|---|---|---|---|---|---|
| Lần 1: toàn bộ | 272 | 177 | 62 | 18 | 1 | 15 | 1 giờ 41 phút 16 giây | `TestReport_Group17.html` |
| Lần 2: chạy lại test hỏng | 76 | 6 | 55 | 0 | – | 15 | 33 phút 55 giây | `TestReport_Group17_rerun.html` |
| Lần 3: chạy lại test lỗi môi trường | 33 | 20 | 13 | 0 | – | 1 | 18 phút 24 giây | `TestReport_Group17_rerun2.html` |

Ở lần 1 và lần 2, demo bị reset dữ liệu giữa chừng ("Resetting the Database", HTTP 503): các test đang chạy lúc đó hỏng ngay ở bước đăng nhập (Error) hoặc tự bỏ qua (Skipped, ở file của Huy). Các test này được chạy lại khi demo hoạt động ổn định.

## 3. Kết quả cuối theo thành viên

Kết quả cuối lấy kết quả của lần chạy gần nhất cho mỗi test.

| Thành viên | Chức năng | Số test | Passed | Failed | xfailed | Error | Thời gian lần 1 |
|---|---|---|---|---|---|---|---|
| Trịnh Minh Quý | Category, Manufacturer, Supplier | 86 | 72 | 13 | 1 | 0 | 25 phút 57 giây |
| Tạ Văn Huy | Accessory, Consumable, Component | 74 | 66 | 7 | 0 | 1 | 34 phút 33 giây |
| Bùi Trọng Linh | Location, Department, User | 66 | 24 | 42 | 0 | 0 | 22 phút 34 giây |
| Nguyễn Hữu Thanh | Asset, Checkout, Model | 46 | 40 | 6 | 0 | 0 | 17 phút 52 giây |
| **Tổng** | | **272** | **202** | **68** | **1** | **1** | |

Phân loại 69 test hỏng ở kết quả cuối (68 Failed, 1 Error):

| Loại | Ý nghĩa | Số test |
|---|---|---|
| (b) Lỗi hệ thống, đã xác nhận | Hệ thống chạy khác Expected Output, tái hiện được | 16 (Quý 13, Thanh 3) |
| (b) Đề xuất, chờ thành viên xác nhận | Có dấu hiệu lỗi hệ thống, cần đối chiếu Expected Output | 4 (Huy 3, Thanh 1) |
| (a) Lỗi của script | Locator hoặc cách chờ của script sai, cần sửa script | 46 (Linh 41, Huy 4, Thanh 1) |
| Chưa kết luận | Cần thêm bằng chứng | 3 (Linh 1, Huy 1, Thanh 1) |
| (c) Môi trường | Demo reset, quá tải | 0 (đã chạy lại hết) |

## 4. Danh sách test thất bại và nguyên nhân

Mã lỗi `#G17-BUG-xx` do từng thành viên tự quản lý trong file test case của mình, nên được ghi kèm tên thành viên.

### 4.1 Trịnh Minh Quý: 13 Failed, đều là lỗi hệ thống (b), tái hiện ổn định

| Test | Mã lỗi (Quý) | Nguyên nhân |
|---|---|---|
| category_12, category_13, manufacturer_09, supplier_09 | BUG-05 | Tên 255 ký tự được báo lưu thành công nhưng chỉ lưu 191 ký tự |
| category_26, manufacturer_24, supplier_27 | BUG-01 | Thông báo chặn xóa không thay tên thật ("Category_name", "Supplier_name", ":accessory_count") |
| category_31, manufacturer_10, supplier_10 | BUG-03 | Dán chuỗi quá 255 ký tự bị cắt âm thầm, không có thông báo |
| manufacturer_23, supplier_26 | BUG-08 | Xóa hàng loạt không có hộp xác nhận |
| manufacturer_26 | BUG-06 | Nút Deleted không lọc được nhà sản xuất đã xóa mềm |

[Manufacturer-25] là xfailed: đang chờ trả lời Q&A (hệ thống cho xóa nhà sản xuất đang được Asset Model sử dụng). 13 test trên cũng hỏng đúng dòng, đúng thông báo ở 4 lần chạy cá nhân trước đó (v3 đến v6).

### 4.2 Nguyễn Hữu Thanh: 6 Failed (chờ Thanh xác nhận)

| Test | Phân loại | Nguyên nhân | Hướng khắc phục |
|---|---|---|---|
| asset_09 | (b) | Asset Tag 192 ký tự vẫn được lưu (Thanh BUG-02) | Giữ Failed, ghi mã lỗi |
| asset_15 | (b) | Ngày không tồn tại 30/02/2026 vẫn được lưu (Thanh BUG-03) | Giữ Failed, ghi mã lỗi |
| asset_27 | (b) | Xóa được tài sản đang cấp phát (Thanh BUG-01) | Giữ Failed, ghi mã lỗi |
| asset_23 | (b) đề xuất | Hệ thống báo "The asset tag must be unique.", script mong đợi "The Asset Tag must be unique." (khác chữ hoa) | Thanh đối chiếu Expected Output trong file test case |
| asset_05 | Chưa kết luận | Asset Tag tự sinh dạng `B&S-CPU-133205`, không phải dãy số | Kiểm tra cấu hình tiền tố Asset Tag của demo trước khi kết luận |
| checkout_09 | (a), chưa chắc | Mất thông báo thành công khi request nền còn chạy (cùng cơ chế đã gặp ở phần của Quý) | Chờ request nền xong trước khi gửi form |

### 4.3 Tạ Văn Huy: 7 Failed, 1 Error (chờ Huy xác nhận)

| Test | Phân loại | Nguyên nhân | Hướng khắc phục |
|---|---|---|---|
| accessory_11, consumable_10, component_09 | (b) đề xuất | Số lượng thập phân vẫn được lưu | Huy đối chiếu Expected Output |
| accessory_28, accessory_29, consumable_22, consumable_24 | (a) | Script tìm người dùng "Admin User", nhưng demo hiển thị "User Admin (admin)" | Sửa tên người dùng trong script |
| component_20 (Error) | Chưa kết luận | Thân test Passed; bước dọn dữ liệu không xóa được danh mục vì còn liên kết | Kiểm tra thứ tự dọn dữ liệu (xóa linh kiện trước danh mục) |

### 4.4 Bùi Trọng Linh: 42 Failed (chờ Linh xác nhận)

| Nhóm test | Số test | Phân loại | Nguyên nhân | Hướng khắc phục |
|---|---|---|---|---|
| Các test thêm, sửa, xóa của Location, Department, User | 29 | (a) | Hàm `save_form` lấy phần tử đầu tiên trong mọi nút submit, trúng nút tìm kiếm trên thanh đầu trang thay vì nút Save của form; form không được gửi | Chọn nút submit nằm trong form (`#submit_button` hoặc giới hạn trong `form`) |
| location_01, department_01, user_01, user_22 | 4 | (a) | Locator `table#table` không còn đúng: bảng của v8.8.3 không có id | Đổi locator bảng |
| location_14, department_13, user_25 | 3 | (a) | Locator thanh phân trang khớp 2 phần tử (strict mode) | Giới hạn locator, ví dụ `.first` hoặc phạm vi cụ thể |
| user_02, user_11 | 2 | (a) | Locator ô username khớp 2 phần tử (có 1 ô ẩn) | Loại trừ ô `type=hidden` |
| location_08 | 1 | (a) | Locator trúng nút Dark Mode đang ẩn | Sửa locator |
| location_03, department_03 | 2 | (a), chưa chắc | Không đọc được dấu `*` bắt buộc bằng chữ; dấu này có thể được vẽ bằng CSS | Kiểm tra cách hiển thị dấu bắt buộc |
| department_08 | 1 | Chưa kết luận | Bấm Cancel xong không về đúng trang danh sách trong 10 giây | Xem trace |

## 5. Ổn định và test không ổn định (flaky)

- Phần của Quý cho kết quả giống hệt nhau ở lần chạy nhóm và 4 lần chạy cá nhân trước đó (v3 đến v6), sau khi chạy lại các test lỗi môi trường.
- Thanh: checkout_04 và checkout_08 hỏng ở lần 1 nhưng đạt ở lần 2 (flaky, nghi cùng nguyên nhân với checkout_09).
- Mọi test Error ở lần 1, 2 đều do demo reset, và đã có kết quả thật sau khi chạy lại.

## 6. Ghi chú

- **Error và Skipped khi demo bảo trì:** file của Huy có fixture riêng kiểm tra demo trước mỗi test; gặp 503 thì báo **Skipped** kèm lý do. Các file khác dùng đăng nhập chung trong `conftest.py`, gặp 503 thì báo **Error** ở bước chuẩn bị. Cả hai đều là lỗi môi trường, không phải kết quả kiểm thử.
- `--lf` không chạy lại test vừa Failed vừa Skipped ở bước dọn dữ liệu (component_07) và các test Skipped, nên lần 3 chỉ định các test này thủ công.
- Các test case giao diện kiểm tra bằng mắt được thực hiện thủ công, không có trong Test Suite.

## 7. Việc tiếp theo

1. Linh, Huy, Thanh xác nhận phân loại ở mục 4 và sửa các lỗi (a) trong script của mình.
2. Đạt chuyển script ASM7 sang dạng pytest và tích hợp vào `tests/`.
3. Sau khi các bản sửa được merge, chạy lại toàn bộ Test Suite theo cùng quy trình và cập nhật báo cáo này.

## 8. Danh sách file

| File | Nội dung |
|---|---|
| `TestReport_Group17.html`, `.xml` | Lần 1: toàn bộ 272 test |
| `TestReport_Group17_rerun.html`, `.xml` | Lần 2: chạy lại test hỏng |
| `TestReport_Group17_rerun2.html`, `.xml` | Lần 3: chạy lại test lỗi môi trường |
| `../Envidence - Group17/` | Log 3 lần chạy, 69 ảnh chụp test hỏng, 8 trace tiêu biểu |
