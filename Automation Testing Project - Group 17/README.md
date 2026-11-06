# Automation Testing Project - Group 17

Project automation test hệ thống **Snipe-IT** (https://demo.snipeitapp.com, phiên bản v8.8.3) của Nhóm 17, môn Kiểm thử phần mềm – Trường ĐH Nông Lâm TP.HCM. Project tích hợp script của 5 thành viên thành một Test Suite chạy được bằng một lệnh.

Công cụ: Python 3.12 + pytest + Playwright (trình duyệt Chromium).

## Cấu trúc

```
Automation Testing Project - Group 17/
├── README.md            hướng dẫn này
├── requirements.txt     thư viện cần cài
├── pytest.ini           cấu hình pytest (thư mục test, đường dẫn import)
├── conftest.py          fixture dùng chung: đăng nhập trước mỗi test, thời gian chờ
├── helpers.py           cấu hình môi trường (BASE_URL, tài khoản) và hàm dùng chung
└── tests/               mỗi thành viên một file test_MaSV_HoTen.py
```

| File test | Thành viên | Chức năng |
|---|---|---|
| `test_23130303_NguyenHuuThanh.py` | Nguyễn Hữu Thanh | Asset, Checkout, Model |
| (chưa tích hợp) | Phạm Hữu Đạt | License, Kit, Field |
| `test_23130138_TaVanHuy.py` | Tạ Văn Huy | Accessory, Consumable, Component |
| `test_21130420_BuiTrongLinh.py` | Bùi Trọng Linh | User, Department, Location |
| `test_21130507_TrinhMinhQuy.py` | Trịnh Minh Quý | Category, Manufacturer, Supplier |

## Cài đặt (làm một lần)

Yêu cầu: Python 3.12 trở lên, Git. Mở PowerShell tại thư mục gốc của repo:

```powershell
cd "Automation Testing Project - Group 17"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

Mỗi lần mở Terminal mới, kích hoạt lại môi trường bằng `.venv\Scripts\Activate.ps1` (dòng lệnh phải hiện `(.venv)`). Tên thư mục có khoảng trắng nên luôn đặt trong ngoặc kép.

## Cấu hình

Cấu hình nằm ở `helpers.py`: địa chỉ website `BASE_URL` và tài khoản `admin` / `password` (tài khoản công khai của demo). Thời gian chờ nằm ở `conftest.py`: mỗi bước kiểm tra chờ tối đa 10 giây, mỗi thao tác chờ tối đa 15 giây.

## Chạy test

```powershell
# Toàn bộ Test Suite của nhóm
python -m pytest -v

# Toàn bộ, kèm báo cáo HTML, ảnh và trace khi test hỏng
python -m pytest -v --html=TestReport_Group17.html --self-contained-html --junitxml=TestReport_Group17.xml --screenshot only-on-failure --tracing retain-on-failure

# Riêng phần của một thành viên
python -m pytest tests/test_21130507_TrinhMinhQuy.py -v

# Riêng một chức năng hoặc một test case
python -m pytest -k manufacturer -v
python -m pytest -k supplier_03 -v

# Xem trình duyệt thao tác (chậm lại 0,5 giây mỗi bước)
python -m pytest -k category_03 --headed --slowmo 500 -v

# Chỉ chạy lại các test hỏng ở lần trước (tìm test không ổn định)
python -m pytest --lf -v
```

Mở trace của test hỏng: `python -m playwright show-trace test-results/<tên test>/trace.zip`.

## Quy ước

- Tên hàm test gắn với mã test case trong file Excel: `test_category_03_...` là [Category-3].
- Dữ liệu test có tiền tố `G17_` và mốc thời gian; mỗi test tự tạo và tự xóa dữ liệu, nên các test chạy độc lập, theo thứ tự bất kỳ.
- Test case giao diện ([...-1], [...-2]) kiểm tra bằng mắt, thực hiện thủ công, không có trong script.
- Test Failed do hệ thống khác Expected Output được giữ nguyên và ghi mã lỗi `#G17-BUG-xx` trong file Excel.

## Lưu ý về môi trường demo

- Demo reset dữ liệu nhiều lần mỗi ngày ("Resetting the database") và đôi khi báo 503. Nếu mọi test lỗi ở bước đăng nhập, chờ 3–5 phút rồi chạy lại.
- Nhiều người dùng chung demo, nên số bản ghi thay đổi liên tục; một số test thỉnh thoảng không ổn định (flaky). Dùng `--lf` để chạy lại và xác định.
- Chạy toàn bộ Test Suite mất nhiều thời gian (riêng phần của Quý khoảng 30 phút).
