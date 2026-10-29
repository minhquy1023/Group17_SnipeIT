"""
ASM7 - Automation test 3 chuc nang: Categories, Manufacturers, Suppliers - Snipe-IT
Nhom 17 - 21130507 - Trinh Minh Quy
Website: https://demo.snipeitapp.com (Snipe-IT v8.8.3)
Cong cu: Python 3.12 + pytest + Playwright

Cach chay (Terminal phai hien (.venv)):
    python -m pytest 21130507_TrinhMinhQuy_ASM7.py --headed --slowmo 500 -v
Chay rieng 1 chuc nang:
    python -m pytest 21130507_TrinhMinhQuy_ASM7.py -k manufacturer -v
Chay rieng 1 test case, vi du [Supplier-3]:
    python -m pytest 21130507_TrinhMinhQuy_ASM7.py -k supplier_03 --headed -v

Moi ham test ung voi 1 test case trong file Group17_21130507_TrinhMinhQuy.xlsx
(test_category_03_... = [Category-3], test_manufacturer_03_... = [Manufacturer-3]).
Moi test tu tao du lieu ten G17_... va tu xoa sau khi chay, nen cac test khong phu
thuoc nhau va chay duoc theo thu tu bat ky.
Test case giao dien ([...-1], [...-2]) kiem tra bang mat nen thuc hien thu cong.
"""

import base64
import re
import time
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect

# =====================================================================
# 1. CAU HINH MOI TRUONG (giong Profile trong Katalon)
# =====================================================================
BASE_URL = "https://demo.snipeitapp.com"
USERNAME = "admin"
PASSWORD = "password"
LIST_URL = f"{BASE_URL}/categories"
MODELS_URL = f"{BASE_URL}/models"

# Demo phan hoi cham: cho toi da 10 giay cho moi buoc kiem tra
expect.set_options(timeout=10_000)

# =====================================================================
# 2. CAU THONG BAO DA XAC NHAN TREN TRANG THAT
# =====================================================================
MSG_CREATED = "Category created successfully."
MSG_UPDATED = "Category updated successfully."
MSG_DELETED = "Category was deleted successfully."
MSG_FORM_ERROR = "Please check the form below for errors"
MSG_REQUIRED = "This field is required"
MSG_TYPE_REQUIRED = "The category type field is required."
MSG_UNIQUE = "The name must be unique across categories and category type."
MSG_TYPE_LOCKED = "You cannot change the category type once it has been created"
MSG_NO_RECORDS = "No matching records found"
MSG_MODEL_CREATED = "Model created successfully."
MSG_MODEL_DELETED = "The model was deleted successfully."
MSG_MAX_LENGTH = "Please enter no more than 255 characters."
MSG_IMAGE_TYPE = "The image field must be a file of type"

# Tep test tao ngay trong code (khong can file di kem, giu dung quy dinh 1 file script)
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
PDF_MINI = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


# =====================================================================
# 3. FIXTURE: phan Pre-condition va don dep viet thanh code
# =====================================================================
@pytest.fixture(autouse=True)
def logged_in(page: Page):
    """Pre-condition chung: dang nhap thanh cong bang admin/password."""
    page.set_default_timeout(15_000)
    page.goto(f"{BASE_URL}/login")
    page.get_by_role("textbox", name="Username").fill(USERNAME)
    page.get_by_role("textbox", name="Password").fill(PASSWORD)
    page.get_by_role("textbox", name="Password").press("Enter")
    expect(page.get_by_role("link", name="Admin Settings")).to_be_visible()


@pytest.fixture
def created(page: Page):
    """Danh sach ten danh muc test da tao. Sau khi test ket thuc (ke ca khi
    that bai), moi ten trong danh sach deu duoc tim va xoa."""
    names: list[str] = []
    yield names
    for name in names:
        try:
            delete_all_matching(page, name)
        except Exception as error:  # don dep loi khong duoc che mat ket qua test
            print(f"\n[Don dep] Khong xoa duoc {name}: {error}")


@pytest.fixture
def created_models(page: Page, created):
    """Danh sach ten Asset Model da tao. Fixture nay phu thuoc created nen duoc
    don TRUOC: phai xoa model truoc thi danh muc chua no moi xoa duoc."""
    names: list[str] = []
    yield names
    for name in names:
        try:
            delete_all_matching(page, name, MODELS_URL, MSG_MODEL_DELETED)
        except Exception as error:  # don dep loi khong duoc che mat ket qua test
            print(f"\n[Don dep] Khong xoa duoc model {name}: {error}")


# =====================================================================
# 4. HAM DUNG CHUNG
# =====================================================================
def unique_name(label: str) -> str:
    """Ten khong trung: G17_<nhan>_<so mili giay hien tai>."""
    return f"G17_{label}_{time.time_ns() // 1_000_000}"


def name_box(page: Page):
    return page.get_by_role("textbox", name="name")


def type_select(page: Page):
    # O Type dung Select2: thao tac tren the <select> that
    return page.locator("select[name='category_type']")


def success_alert(page: Page):
    return page.locator("div.alert.alert-success")


def error_alert(page: Page):
    return page.locator("div.alert.alert-danger")


def no_records(page: Page):
    return page.locator("tr.no-records-found")


def visible_text(page: Page, text: str):
    """Phan tu dang hien thi co chua doan chu text."""
    return page.get_by_text(text).filter(visible=True).first


def open_create_form(page: Page) -> None:
    page.goto(LIST_URL)
    page.get_by_role("button", name="+").click()
    # Cho trang tai xong (su kien load): o Name hien ra khi HTML con dang tai, truoc
    # khi JavaScript cua trang chay; thao tac som (vd chon tep) se khong duoc xu ly
    page.wait_for_url(f"{LIST_URL}/create")
    expect(name_box(page)).to_be_visible()


def fill_form(page: Page, name: str, cat_type: str | None = None) -> None:
    name_box(page).fill(name)
    if cat_type:
        type_select(page).select_option(cat_type)


def save(page: Page) -> None:
    page.locator("#submit_button").click()


def create_category(page: Page, created: list, name: str, cat_type: str = "asset") -> None:
    """Tao danh muc va kiem tra tao thanh cong. Ghi ten vao danh sach don dep
    TRUOC khi bam Save, de du test hong giua chung van don duoc."""
    created.append(name)
    open_create_form(page)
    fill_form(page, name, cat_type)
    save(page)
    page.wait_for_url(LIST_URL)
    expect(success_alert(page)).to_contain_text(MSG_CREATED)


def create_model(page: Page, created_models: list, name: str, category: str) -> None:
    """Tao Asset Model thuoc danh muc category va kiem tra tao thanh cong."""
    created_models.append(name)
    page.goto(f"{MODELS_URL}/create")
    name_box(page).fill(name)
    # O Category dung Select2 tai du lieu qua API: the <select> chua co lua chon
    # nao truoc khi tim, nen phai mo o chon, go ten roi bam vao ket qua
    page.locator("select[name='category_id'] + .select2").click()
    page.locator(".select2-container--open .select2-search__field").fill(category)
    page.locator(".select2-results__option", has_text=category).click()
    save(page)
    page.wait_for_url(MODELS_URL)
    expect(success_alert(page)).to_contain_text(MSG_MODEL_CREATED)


def search_current(page: Page, text: str):
    """Tim kiem text tren bang dang mo (khong tai lai trang), tra ve cac dong chua text."""
    box = page.get_by_role("searchbox", name="Search")
    box.fill(text)
    # Bang tai du lieu qua API. Truoc khi ket qua cua LAN TIM NAY ve, bang hien tam
    # "No matching records found" hoac ket qua cua tu khoa cu (bang nho tu khoa bang
    # cookie), nen phai cho dung phan hoi co search == text roi cho lop phu "dang tai" tat
    with page.expect_response(
        lambda r: "/api/v1/" in r.url and parse_qs(urlparse(r.url).query).get("search") == [text]
    ):
        box.press("Enter")  # bat buoc: fill() khong phat su kien phim nen bang khong loc
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    return page.get_by_role("row").filter(has_text=text)


def find_in_list(page: Page, text: str, url: str = LIST_URL):
    """Mo danh sach url, tim kiem text, tra ve cac dong chua text."""
    page.goto(url)
    return search_current(page, text)


def open_edit_form(page: Page, name: str) -> None:
    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    rows.get_by_role("link", name="Update").click()
    expect(name_box(page)).to_have_value(name)


def delete_all_matching(page: Page, name: str, url: str = LIST_URL, msg: str = MSG_DELETED) -> None:
    """Xoa moi dong co chua name (toi da 5 dong) o danh sach url."""
    for _ in range(5):
        rows = find_in_list(page, name, url)
        expect(rows.first.or_(no_records(page))).to_be_visible()
        if rows.count() == 0:
            return
        # exact=True: ten ban ghi co the chua chu "Delete" (vd G17_Delete_...), khop ca link ten
        rows.first.get_by_role("link", name="Delete", exact=True).click()
        page.get_by_role("button", name="Yes").click()
        expect(success_alert(page)).to_contain_text(msg)


# =====================================================================
# 5. TEST CASE - THEM MOI
# =====================================================================
def test_category_03_create_required_fields_only(page: Page, created):
    """[Category-3] Them moi danh muc chi nhap truong bat buoc."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")

    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text("Asset")


def test_category_04_create_all_fields(page: Page, created):
    """[Category-4] Them moi danh muc nhap day du cac truong.
    Thay vi quan sat dau tich xanh (kiem tra bang mat), script mo lai form sua
    de xac nhan tung truong da duoc luu dung."""
    name = unique_name("Monitor")
    eula = "Điều khoản sử dụng màn hình"
    notes = "Danh mục test nhóm 17"
    created.append(name)

    open_create_form(page)
    fill_form(page, name, "asset")
    page.locator("[name='eula_text']").fill(eula)
    page.locator("input[type='checkbox'][name='require_acceptance']").check()
    page.locator("input[type='checkbox'][name='checkin_email']").check()
    page.locator("[name='notes']").fill(notes)
    save(page)
    page.wait_for_url(LIST_URL)
    expect(success_alert(page)).to_contain_text(MSG_CREATED)

    open_edit_form(page, name)
    expect(page.locator("[name='eula_text']")).to_have_value(eula)
    expect(page.locator("input[type='checkbox'][name='require_acceptance']")).to_be_checked()
    expect(page.locator("input[type='checkbox'][name='checkin_email']")).to_be_checked()
    expect(page.locator("[name='notes']")).to_have_value(notes)


def test_category_05_empty_name(page: Page):
    """[Category-5] Bo trong truong Name."""
    open_create_form(page)
    type_select(page).select_option("asset")
    save(page)

    expect(visible_text(page, MSG_REQUIRED)).to_be_visible()
    expect(page).to_have_url(re.compile(r"/categories/create"))


def test_category_06_empty_type(page: Page, created):
    """[Category-6] Bo trong truong Type (kiem tra phia may chu)."""
    name = unique_name("NoType")
    created.append(name)  # phong khi he thong tao nham
    open_create_form(page)
    fill_form(page, name)
    save(page)

    expect(visible_text(page, MSG_TYPE_REQUIRED)).to_be_visible()
    find_in_list(page, name)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_category_07_all_fields_empty(page: Page):
    """[Category-7] Bo trong tat ca cac truong."""
    open_create_form(page)
    save(page)

    expect(visible_text(page, MSG_REQUIRED)).to_be_visible()
    expect(page).to_have_url(re.compile(r"/categories/create"))


def test_category_08_name_only_spaces(page: Page):
    """[Category-8] Name chi chua khoang trang."""
    open_create_form(page)
    fill_form(page, "     ", "asset")
    save(page)

    # Khoang trang khong bi trinh duyet coi la rong: may chu kiem tra va bao loi (test thu cong 29/10)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    expect(visible_text(page, MSG_NAME_REQUIRED_SERVER)).to_be_visible()
    expect(page).to_have_url(re.compile(r"/categories/create"))


def test_category_09_duplicate_name_same_type(page: Page, created):
    """[Category-9] Them moi trung ten voi danh muc cung loai."""
    name = unique_name("Dup")
    create_category(page, created, name, "asset")

    open_create_form(page)
    fill_form(page, name, "asset")
    save(page)

    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    expect(visible_text(page, MSG_UNIQUE)).to_be_visible()
    expect(find_in_list(page, name)).to_have_count(1)


def test_category_10_duplicate_name_other_type(page: Page, created):
    """[Category-10] Them moi trung ten voi danh muc khac loai."""
    name = unique_name("SameName")
    create_category(page, created, name, "asset")
    create_category(page, created, name, "accessory")

    rows = find_in_list(page, name)
    expect(rows).to_have_count(2)
    expect(rows.filter(has_text="Asset")).to_have_count(1)
    expect(rows.filter(has_text="Accessory")).to_have_count(1)


def test_category_11_duplicate_name_different_case(page: Page, created):
    """[Category-11] Trung ten khac chu hoa/thuong voi danh muc cung loai."""
    name = unique_name("Case")
    create_category(page, created, name, "asset")

    lower_name = name.lower()
    created.append(lower_name)  # phong khi he thong tao nham
    open_create_form(page)
    fill_form(page, lower_name, "asset")
    save(page)

    expect(visible_text(page, MSG_UNIQUE)).to_be_visible()
    # Bo loc has_text khong phan biet hoa/thuong: neu he thong tao nham se ra 2 dong
    expect(find_in_list(page, name)).to_have_count(1)


def test_category_14_vietnamese_and_special_chars(page: Page, created):
    """[Category-14] Name chua tieng Viet co dau va ky tu dac biet."""
    name = f"G17_Máy tính #1 @& {time.time_ns() // 1_000_000}"
    create_category(page, created, name, "asset")

    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text(name)


def test_category_18_cancel_create(page: Page, created):
    """[Category-18] Huy thao tac tao moi."""
    name = unique_name("Cancel")
    created.append(name)  # phong khi he thong tao nham
    open_create_form(page)
    fill_form(page, name, "asset")
    page.get_by_role("link", name="Cancel").click()

    page.wait_for_url(LIST_URL)
    find_in_list(page, name)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 6. TEST CASE - SUA
# =====================================================================
def test_category_19_open_edit_form(page: Page, created):
    """[Category-19] Mo form sua danh muc."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")

    open_edit_form(page, name)  # da kiem tra o Name hien dung ten da luu
    expect(type_select(page)).to_have_value("asset")
    expect(type_select(page)).to_be_disabled()
    expect(visible_text(page, MSG_TYPE_LOCKED)).to_be_visible()


def test_category_20_edit_name_valid(page: Page, created):
    """[Category-20] Sua Name hop le."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")
    new_name = unique_name("LaptopEdit")
    created.append(new_name)

    open_edit_form(page, name)
    name_box(page).fill(new_name)
    save(page)

    page.wait_for_url(LIST_URL)
    expect(success_alert(page)).to_contain_text(MSG_UPDATED)
    rows = find_in_list(page, new_name)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text("Asset")


def test_category_22_edit_name_empty(page: Page, created):
    """[Category-22] Sua Name thanh rong."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")

    open_edit_form(page, name)
    name_box(page).fill("")
    save(page)

    expect(visible_text(page, MSG_REQUIRED)).to_be_visible()
    expect(page).to_have_url(re.compile(r"/categories/\d+/edit"))
    expect(find_in_list(page, name)).to_have_count(1)


# =====================================================================
# 7. TEST CASE - XOA
# =====================================================================
def test_category_24_delete_unused(page: Page, created):
    """[Category-24] Xoa danh muc chua duoc su dung."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")

    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    rows.get_by_role("link", name="Delete").click()
    expect(visible_text(page, f"Are you sure you wish to delete: {name}")).to_be_visible()
    page.get_by_role("button", name="Yes").click()

    expect(success_alert(page)).to_contain_text(MSG_DELETED)
    find_in_list(page, name)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_category_25_cancel_delete(page: Page, created):
    """[Category-25] Huy thao tac xoa."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")

    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    rows.get_by_role("link", name="Delete").click()
    confirm_text = page.get_by_text(f"Are you sure you wish to delete: {name}")
    expect(confirm_text.filter(visible=True).first).to_be_visible()
    page.get_by_role("button", name="Cancel").click()

    expect(confirm_text.filter(visible=True)).to_have_count(0)
    expect(find_in_list(page, name)).to_have_count(1)


# =====================================================================
# 8. TEST CASE - DANH SACH VA TIM KIEM
# =====================================================================
def test_category_27_search_partial_name(page: Page, created):
    """[Category-27] Tim kiem theo mot phan ten.
    Tim bang phan duoi rieng cua ten vua tao (khong tim 'G17' vi ca nhom
    cung dung tien to nay, ket qua phu thuoc du lieu nguoi khac)."""
    name = unique_name("Search")
    create_category(page, created, name, "asset")

    partial = name[len("G17_"):]
    rows = find_in_list(page, partial)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text(name)


def test_category_28_search_no_result(page: Page):
    """[Category-28] Tim kiem khong co ket qua."""
    keyword = unique_name("KhongTonTai")
    find_in_list(page, keyword)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 9. DOT 2 - DO DAI TOI DA
# =====================================================================
def long_name(length: int) -> str:
    """Ten dai dung length ky tu: G17_ + so mili giay + _ + chu A cho du do dai."""
    prefix = f"G17_{time.time_ns() // 1_000_000}_"
    return prefix + "A" * (length - len(prefix))


def test_category_12_name_max_length_255(page: Page, created):
    """[Category-12] Name co do dai toi da 255 ky tu."""
    name = long_name(255)
    created.append(name[:191])  # phong khi he thong cat ten (da quan sat: chi luu 191 ky tu)
    create_category(page, created, name, "asset")

    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text(name)


def test_category_13_type_over_max_length(page: Page, created):
    """[Category-13] Go vuot do dai toi da (256 ky tu) vao truong Name.
    Dan 255 ky tu bang fill(), sau do GO them 1 phim that bang press_sequentially()."""
    name = long_name(255)
    created.append(name)
    created.append(name[:191])  # phong khi he thong cat ten (da quan sat o Category-12: chi luu 191 ky tu)
    open_create_form(page)
    name_box(page).fill(name)
    name_box(page).press_sequentially("B")

    # O Name co maxlength=255: phim thu 256 bi chan, gia tri giu nguyen (test thu cong 29/10)
    expect(name_box(page)).to_have_value(name)
    name_box(page).press("Tab")  # roi khoi truong Name
    expect(name_box(page)).to_have_value(name)  # ky tu vuot qua bi loai bo

    type_select(page).select_option("asset")
    save(page)
    page.wait_for_url(LIST_URL)
    expect(success_alert(page)).to_contain_text(MSG_CREATED)
    expect(find_in_list(page, name)).to_have_count(1)


def test_category_31_paste_over_max_length(page: Page, created):
    """[Category-31] Dan chuoi vuot do dai toi da (256 ky tu) vao truong Name.
    Ky vong FAILED: he thong cat con 255 ky tu ma khong thong bao (#G17-BUG-03)."""
    name = long_name(256)
    created.append(name)
    created.append(name[:255])  # phong khi he thong luu ban bi cat
    open_create_form(page)
    name_box(page).fill(name)  # fill() dua ca chuoi vao mot lan, giong thao tac dan

    expect(visible_text(page, MSG_MAX_LENGTH)).to_be_visible()


# =====================================================================
# 10. DOT 2 - BAO MAT VA TAI TEP
# =====================================================================
def test_category_15_name_with_html_script(page: Page, created):
    """[Category-15] Name chua ma HTML/JavaScript (kiem tra XSS).
    Moi hop thoai alert bat len deu bi ghi lai; co bat ky hop thoai nao la FAILED."""
    alerts: list[str] = []

    def on_dialog(dialog):
        alerts.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", on_dialog)

    name = f"G17_<script>alert({time.time_ns() // 1_000_000})</script>"
    created.append(name)
    open_create_form(page)
    fill_form(page, name, "asset")
    save(page)
    page.wait_for_load_state()

    rows = find_in_list(page, name)
    expect(rows.first.or_(no_records(page))).to_be_visible()
    if rows.count() > 0:
        expect(rows.first).to_contain_text(name)  # hien thi dang chu, khong thuc thi
    assert alerts == [], f"Ma JavaScript da duoc thuc thi, hop thoai: {alerts}"


def test_category_16_upload_valid_image(page: Page, created):
    """[Category-16] Tai anh dung dinh dang."""
    name = unique_name("Tablet")
    created.append(name)
    open_create_form(page)
    fill_form(page, name, "asset")
    page.locator("#uploadFile").set_input_files(
        {"name": "g17.png", "mimeType": "image/png", "buffer": PNG_1PX}
    )
    expect(page.locator("#uploadFile-info")).to_contain_text("g17.png")

    save(page)
    page.wait_for_url(LIST_URL)
    expect(success_alert(page)).to_contain_text(MSG_CREATED)
    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    expect(rows.locator("img")).to_have_count(1)  # cot Image co anh thu nho


def test_category_17_upload_invalid_file(page: Page, created):
    """[Category-17] Tai tep sai dinh dang (PDF)."""
    name = unique_name("Phone")
    created.append(name)
    open_create_form(page)
    fill_form(page, name, "asset")
    page.locator("#uploadFile").set_input_files(
        {"name": "g17.pdf", "mimeType": "application/pdf", "buffer": PDF_MINI}
    )
    expect(page.locator("#uploadFile-info")).to_contain_text("g17.pdf")

    save(page)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    expect(page.locator("span.alert-msg")).to_contain_text(MSG_IMAGE_TYPE)
    find_in_list(page, name)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 11. DOT 2 - RANG BUOC KHI SUA
# =====================================================================
def test_category_21_cannot_change_type(page: Page, created):
    """[Category-21] Khong the thay doi Type khi sua."""
    name = unique_name("Laptop")
    create_category(page, created, name, "asset")

    open_edit_form(page, name)
    expect(type_select(page)).to_be_disabled()
    expect(type_select(page)).to_have_value("asset")

    # Luu lai form, Type van phai la Asset
    save(page)
    page.wait_for_url(LIST_URL)
    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text("Asset")


def test_category_23_edit_name_duplicate_same_type(page: Page, created):
    """[Category-23] Sua Name trung voi danh muc khac cung loai."""
    laptop = unique_name("Laptop")
    monitor = unique_name("Monitor")
    create_category(page, created, laptop, "asset")
    create_category(page, created, monitor, "asset")

    open_edit_form(page, monitor)
    name_box(page).fill(laptop)
    save(page)

    expect(visible_text(page, MSG_UNIQUE)).to_be_visible()
    expect(find_in_list(page, monitor)).to_have_count(1)  # ten Monitor khong doi


# =====================================================================
# 12. XOA DANH MUC DANG DUOC SU DUNG
# =====================================================================
def test_category_26_delete_used_category(page: Page, created, created_models):
    """[Category-26] Xoa danh muc dang duoc su dung (co Asset Model thuoc no).
    DU KIEN FAILED do loi #G17-BUG-01: thong bao hien "Category_name" thay vi ten
    that cua danh muc. KHONG sua cau ky vong de test Passed."""
    name = unique_name("Used")
    create_category(page, created, name, "asset")
    create_model(page, created_models, unique_name("Model"), name)

    rows = find_in_list(page, name)
    expect(rows).to_have_count(1)
    rows.get_by_role("link", name="Delete").click()
    page.get_by_role("button", name="Yes").click()

    # Doc thong bao truoc, kiem tra sau: neu kiem tra cau thong bao truoc ma
    # sai thi test dung luon, khong bao gio kiem tra duoc danh muc con hay mat
    expect(error_alert(page)).to_be_visible()
    alert_text = error_alert(page).inner_text()
    expect(find_in_list(page, name)).to_have_count(1)

    expected_msg = f"{name} still has associated items. Please remove them before deleting this Category."
    assert expected_msg in alert_text, f"Thong bao thuc te: {alert_text!r}"


# #####################################################################
#            PHAN 2 - MANUFACTURERS VA SUPPLIERS (dung chung)
# #####################################################################
# Cau thong bao va dia chi lay tu ban kham pha ngay 28/10/2026 (v8.8.3)
class Module:
    """Thong tin rieng cua tung man hinh, de cac ham dung chung cho ca 2 chuc nang."""

    def __init__(self, label, url, created, updated, deleted, unique, not_found):
        self.label = label          # ten hien thi trong thong bao, vd "Manufacturer"
        self.url = url              # dia chi danh sach
        self.created = created
        self.updated = updated
        self.deleted = deleted
        self.unique = unique        # cau bao trung ten (khac nhau giua 2 man hinh)
        self.not_found = not_found  # cau bao khi mo ban ghi da xoa


MAN = Module(
    "Manufacturer", f"{BASE_URL}/manufacturers",
    "Manufacturer created successfully.", "Manufacturer updated successfully.",
    "Manufacturer deleted successfully.", "The name has already been taken.",
    "That Manufacturer was not found or you do not have permission to access it",
)
SUP = Module(
    "Supplier", f"{BASE_URL}/suppliers",
    "Supplier created successfully.", "Supplier updated successfully.",
    "Supplier was deleted successfully.", "The name must be unique.",
    "That Supplier was not found or you do not have permission to access it",
)
ACCESSORIES_URL = f"{BASE_URL}/accessories"
MSG_ACC_CREATED = "The accessory was successfully created."
MSG_ACC_DELETED = "The accessory was deleted successfully."
MSG_NAME_REQUIRED_SERVER = "The name field is required."
MSG_INVALID_URL = "Please enter a valid URL."
MSG_INVALID_EMAIL = "Please enter a valid email address"


def _cleanup(page: Page, names: list, url: str, msg: str, label: str) -> None:
    for name in names:
        try:
            delete_all_matching(page, name, url, msg)
        except Exception as error:  # don dep loi khong duoc che mat ket qua test
            print(f"\n[Don dep] Khong xoa duoc {label} {name}: {error}")


@pytest.fixture
def man_created(page: Page):
    names: list[str] = []
    yield names
    _cleanup(page, names, MAN.url, MAN.deleted, "Manufacturer")


@pytest.fixture
def sup_created(page: Page):
    names: list[str] = []
    yield names
    _cleanup(page, names, SUP.url, SUP.deleted, "Supplier")


@pytest.fixture
def acc_created(page: Page, man_created, sup_created):
    """Phu kien phu tro. Phu thuoc man_created va sup_created nen duoc don TRUOC:
    xoa phu kien truoc thi nha san xuat / nha cung cap moi xoa duoc."""
    names: list[str] = []
    yield names
    _cleanup(page, names, ACCESSORIES_URL, MSG_ACC_DELETED, "Accessory")


@pytest.fixture
def man_models(page: Page, man_created):
    """Asset Model phu tro, duoc don truoc nha san xuat."""
    names: list[str] = []
    yield names
    _cleanup(page, names, MODELS_URL, MSG_MODEL_DELETED, "Model")


def m_name(page: Page):
    # Dung id: o Supplier co ca "Supplier Name" va "Contact Name", tim theo nhan "name" se trung
    return page.locator("input#name")


def m_open_create(page: Page, mod: Module) -> None:
    page.goto(f"{mod.url}/create")  # goto cho su kien load, JavaScript cua trang da san sang
    expect(m_name(page)).to_be_visible()


def m_fill(page: Page, fields: dict) -> None:
    """Dien cac o theo id, vd {"url": "https://g17.vn"}."""
    for field_id, value in fields.items():
        page.locator(f"#{field_id}").fill(value)


def m_create(page: Page, cleanup: list, mod: Module, name: str, fields: dict | None = None) -> None:
    """Tao ban ghi va kiem tra tao thanh cong. Ghi ten de don TRUOC khi bam Save."""
    cleanup.append(name)
    m_open_create(page, mod)
    m_name(page).fill(name)
    m_fill(page, fields or {})
    save(page)
    page.wait_for_url(mod.url)
    expect(success_alert(page)).to_contain_text(mod.created)


def m_open_edit(page: Page, mod: Module, search: str):
    """Tim ban ghi theo search, mo form sua cua dong tim duoc."""
    rows = find_in_list(page, search, mod.url)
    expect(rows).to_have_count(1)
    rows.get_by_role("link", name="Update").click()
    expect(m_name(page)).to_be_visible()


def select2_pick(page: Page, select_name: str, search_text: str | None = None) -> None:
    """Chon trong o Select2 tai du lieu qua API: mo o, (go tu khoa), bam ket qua."""
    page.locator(f"select[name='{select_name}'] + .select2").click()
    if search_text:
        page.locator(".select2-container--open .select2-search__field").fill(search_text)
        option = page.locator(".select2-results__option", has_text=search_text)
    else:
        option = page.locator(".select2-results__option:not(.loading-results)")
    option.first.click()


def create_accessory(page: Page, acc_created: list, name: str,
                     manufacturer: str | None = None, supplier: str | None = None) -> None:
    """Tao phu kien (Category: muc dau tien co san, Qty = 1) gan voi nha san xuat / nha cung cap."""
    acc_created.append(name)
    page.goto(f"{ACCESSORIES_URL}/create")
    page.locator("input[name='name']").fill(name)
    select2_pick(page, "category_id")
    if manufacturer:
        select2_pick(page, "manufacturer_id", manufacturer)
    if supplier:
        select2_pick(page, "supplier_id", supplier)
    page.locator("input[name='qty']").fill("1")
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_ACC_CREATED)


def delete_row(page: Page, rows) -> None:
    rows.first.get_by_role("link", name="Delete", exact=True).click()
    page.get_by_role("button", name="Yes").click()


def watch_dialogs(page: Page) -> list:
    """Ghi lai moi hop thoai alert bat len (dau hieu ma JavaScript da chay)."""
    alerts: list[str] = []

    def on_dialog(dialog):
        alerts.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", on_dialog)
    return alerts


def first_column_names(page: Page) -> list[str]:
    """Doc cot Name (cot thu 2, sau o checkbox) cua cac dong dang hien thi."""
    cells = page.locator("table tbody tr:not(.no-records-found) td:nth-child(2)")
    return [t.strip() for t in cells.all_inner_texts()]


def sort_key(text: str) -> str:
    # Chi so sanh chu va so, khong phan biet hoa/thuong: cach sap xep ky tu dac biet
    # cua co so du lieu co the khac Python, so sanh ca ky tu dac biet de bao sai
    return re.sub(r"[^0-9a-z]", "", text.casefold())


def check_sort_by_name(page: Page, mod: Module) -> None:
    """Bam tieu de cot Name 2 lan, moi lan kiem tra thu tu khop voi chieu sap xep."""
    page.goto(mod.url)
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    orders = []
    for _ in range(2):
        with page.expect_response(
            lambda r: "/api/v1/" in r.url and parse_qs(urlparse(r.url).query).get("sort") == ["name"]
        ) as info:
            page.locator("th[data-field='name'] .sortable").click()
        expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
        order = parse_qs(urlparse(info.value.url).query).get("order", ["asc"])[0]
        keys = [sort_key(n) for n in first_column_names(page)]
        expected = sorted(keys, reverse=(order == "desc"))
        assert keys == expected, f"Thu tu cot Name khong dung chieu {order}: {keys}"
        orders.append(order)
    assert sorted(orders) == ["asc", "desc"], f"Hai lan bam phai doi chieu sap xep: {orders}"


def pagination_info(page: Page):
    return page.locator(".pagination-info").first


def check_paging(page: Page, mod: Module, page_size: str | None) -> None:
    page.goto(mod.url)
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    size = 20
    if page_size:
        page.locator(".page-list").first.get_by_role("button").click()
        page.locator(".page-list").first.get_by_text(page_size, exact=True).click()
        size = int(page_size)
    expect(pagination_info(page)).to_contain_text(f"Showing 1 to {size} of")
    page.locator(".page-next a").first.click()
    expect(pagination_info(page)).to_contain_text(f"Showing {size + 1} to")
    page.locator(".page-pre a").first.click()
    expect(pagination_info(page)).to_contain_text(f"Showing 1 to {size} of")


def check_bulk_delete(page: Page, mod: Module, cleanup: list) -> None:
    token = unique_name("Bulk")
    for i in (1, 2):
        m_create(page, cleanup, mod, f"{token}_{i}")
    rows = find_in_list(page, token, mod.url)
    expect(rows).to_have_count(2)
    for i in range(2):
        rows.nth(i).locator("input[type='checkbox']").check()
    expect(page.get_by_text("2 selected")).to_be_visible()
    # Lua chon "Delete" chi xuat hien khi cac dong da chon xoa duoc (ban ghi chua duoc su dung)
    page.locator("select[name='bulk_actions']").select_option(label="Delete")
    page.get_by_role("button", name="Go").click()
    # Excel ky vong co hop xac nhan: cho toi da 3 giay, co thi bam Yes, khong co thi ghi nhan
    yes = page.get_by_role("button", name="Yes")
    try:
        yes.wait_for(state="visible", timeout=3_000)
        confirm_shown = True
    except PlaywrightTimeout:
        confirm_shown = False
    if confirm_shown:
        yes.click()
    expect(success_alert(page)).to_be_visible()
    find_in_list(page, token, mod.url)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)
    # Kiem tra cuoi cung, de phan xoa hang loat van duoc kiem tra truoc
    assert confirm_shown, "Xoa hang loat khong co hop xac nhan"


def check_delete_unused(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("Delete")
    m_create(page, cleanup, mod, name)
    rows = find_in_list(page, name, mod.url)
    expect(rows).to_have_count(1)
    detail_url = rows.get_by_role("link", name=name).first.get_attribute("href")

    rows.get_by_role("link", name="Delete", exact=True).click()
    expect(visible_text(page, f"Are you sure you wish to delete: {name}")).to_be_visible()
    page.get_by_role("button", name="Yes").click()
    expect(success_alert(page)).to_contain_text(mod.deleted)
    find_in_list(page, name, mod.url)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)

    page.goto(detail_url)
    expect(error_alert(page)).to_contain_text(mod.not_found)


def check_cancel_delete(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("Keep")
    m_create(page, cleanup, mod, name)
    rows = find_in_list(page, name, mod.url)
    rows.get_by_role("link", name="Delete").click()
    confirm = page.get_by_text(f"Are you sure you wish to delete: {name}")
    expect(confirm.filter(visible=True).first).to_be_visible()
    page.get_by_role("button", name="Cancel").click()
    expect(confirm.filter(visible=True)).to_have_count(0)
    expect(find_in_list(page, name, mod.url)).to_have_count(1)


def check_name_255(page: Page, mod: Module, cleanup: list) -> None:
    """Luu ten 255 ky tu roi do lai trong form sua. Tim bang phan dau cua ten
    (neu he thong cat ten thi tim theo ten day du se khong ra)."""
    name = long_name(255)
    prefix = name[:30]
    cleanup.append(prefix)
    m_open_create(page, mod)
    m_name(page).fill(name)
    save(page)
    page.wait_for_url(mod.url)
    expect(success_alert(page)).to_contain_text(mod.created)

    m_open_edit(page, mod, prefix)
    saved = m_name(page).input_value()
    assert saved == name, f"Ten luu duoc {len(saved)} ky tu, ky vong 255 ky tu"


def check_paste_256(page: Page, mod: Module, cleanup: list) -> None:
    """Ky vong FAILED theo kieu #G17-BUG-03: dan vuot do dai bi cat am tham."""
    name = long_name(256)
    cleanup.append(name[:30])
    m_open_create(page, mod)
    m_name(page).fill(name)  # fill() dua ca chuoi vao mot lan, giong thao tac dan
    expect(visible_text(page, MSG_MAX_LENGTH)).to_be_visible()


def check_xss(page: Page, mod: Module, cleanup: list) -> None:
    alerts = watch_dialogs(page)
    name = f"G17_<script>alert({time.time_ns() // 1_000_000})</script>"
    m_create(page, cleanup, mod, name)
    rows = find_in_list(page, name, mod.url)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text(name)  # hien thi dang chu
    rows.get_by_role("link", name=name).first.click()
    expect(page).to_have_title(re.compile(re.escape(name)))
    assert alerts == [], f"Ma JavaScript da duoc thuc thi, hop thoai: {alerts}"


def check_upload(page: Page, mod: Module, cleanup: list, valid: bool) -> None:
    name = unique_name("Image" if valid else "Pdf")
    cleanup.append(name)
    m_open_create(page, mod)
    m_name(page).fill(name)
    file = ({"name": "g17.png", "mimeType": "image/png", "buffer": PNG_1PX} if valid
            else {"name": "g17.pdf", "mimeType": "application/pdf", "buffer": PDF_MINI})
    page.locator("#uploadFile").set_input_files(file)
    expect(page.locator("#uploadFile-info")).to_contain_text(file["name"])
    save(page)
    if valid:
        page.wait_for_url(mod.url)
        expect(success_alert(page)).to_contain_text(mod.created)
        rows = find_in_list(page, name, mod.url)
        expect(rows).to_have_count(1)
        expect(rows.locator("img")).to_have_count(1)
    else:
        expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
        expect(page.locator("span.alert-msg")).to_contain_text(MSG_IMAGE_TYPE)
        find_in_list(page, name, mod.url)
        expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def check_cancel_create(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("Cancel")
    cleanup.append(name)
    # Mo danh sach truoc nhu nguoi dung that: nut Cancel quay ve TRANG TRUOC DO,
    # neu mo thang /create ngay sau dang nhap thi Cancel se ve Dashboard
    page.goto(mod.url)
    m_open_create(page, mod)
    m_name(page).fill(name)
    page.get_by_role("link", name="Cancel").click()
    page.wait_for_url(mod.url)
    find_in_list(page, name, mod.url)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def check_empty_name(page: Page, mod: Module, other_field: dict) -> None:
    m_open_create(page, mod)
    m_fill(page, other_field)
    save(page)
    expect(page.locator("#name-error")).to_contain_text(MSG_REQUIRED)
    expect(page).to_have_url(re.compile(r"/create"))


def check_spaces_name(page: Page, mod: Module) -> None:
    m_open_create(page, mod)
    m_name(page).fill("     ")
    save(page)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    expect(visible_text(page, MSG_NAME_REQUIRED_SERVER)).to_be_visible()
    expect(page).to_have_url(re.compile(r"/create"))


def check_duplicate(page: Page, mod: Module, cleanup: list, lower: bool) -> None:
    name = unique_name("Dup")
    m_create(page, cleanup, mod, name)
    second = name.lower() if lower else name
    cleanup.append(second)  # phong khi he thong tao nham
    m_open_create(page, mod)
    m_name(page).fill(second)
    save(page)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    expect(visible_text(page, mod.unique)).to_be_visible()
    # Bo loc has_text khong phan biet hoa/thuong: neu he thong tao nham se ra 2 dong
    expect(find_in_list(page, name, mod.url)).to_have_count(1)


def check_create_required_only(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("Basic")
    m_create(page, cleanup, mod, name)
    expect(find_in_list(page, name, mod.url)).to_have_count(1)


def check_vietnamese(page: Page, mod: Module, cleanup: list, text: str) -> None:
    name = f"G17_{text} #1 @& {time.time_ns() // 1_000_000}"
    m_create(page, cleanup, mod, name)
    rows = find_in_list(page, name, mod.url)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text(name)


def check_edit_valid(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("Edit")
    new_name = unique_name("Edited")
    m_create(page, cleanup, mod, name)
    cleanup.append(new_name)
    m_open_edit(page, mod, name)
    expect(m_name(page)).to_have_value(name)
    m_name(page).fill(new_name)
    save(page)
    page.wait_for_url(mod.url)
    expect(success_alert(page)).to_contain_text(mod.updated)
    expect(find_in_list(page, new_name, mod.url)).to_have_count(1)
    find_in_list(page, name, mod.url)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def check_edit_empty(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("EditEmpty")
    m_create(page, cleanup, mod, name)
    m_open_edit(page, mod, name)
    m_name(page).fill("")
    save(page)
    expect(page.locator("#name-error")).to_contain_text(MSG_REQUIRED)
    expect(page).to_have_url(re.compile(r"/\d+/edit"))
    expect(find_in_list(page, name, mod.url)).to_have_count(1)


def check_edit_duplicate(page: Page, mod: Module, cleanup: list) -> None:
    first = unique_name("First")
    second = unique_name("Second")
    m_create(page, cleanup, mod, first)
    m_create(page, cleanup, mod, second)
    m_open_edit(page, mod, second)
    m_name(page).fill(first)
    save(page)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    expect(visible_text(page, mod.unique)).to_be_visible()
    expect(find_in_list(page, second, mod.url)).to_have_count(1)  # van giu ten cu


def check_search(page: Page, mod: Module, cleanup: list) -> None:
    name = unique_name("Search")
    m_create(page, cleanup, mod, name)
    partial = name[len("G17_"):]
    rows = find_in_list(page, partial, mod.url)
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text(name)
    expect(pagination_info(page)).to_contain_text("Showing 1 to 1 of 1 rows")
    search_current(page, unique_name("KhongTonTai"))
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 13. MANUFACTURERS ([Manufacturer-1], [Manufacturer-2]: kiem tra giao dien thu cong)
# =====================================================================
def test_manufacturer_03_create_required_only(page: Page, man_created):
    """[Manufacturer-3] Them moi nha san xuat chi nhap truong bat buoc."""
    check_create_required_only(page, MAN, man_created)


def test_manufacturer_04_create_all_fields(page: Page, man_created):
    """[Manufacturer-4] Them moi nha san xuat nhap day du cac truong."""
    name = unique_name("HP")
    fields = {
        "url": "https://g17.vn",
        "support_url": "https://g17.vn/support/{SERIAL}",
        "warranty_lookup_url": "https://g17.vn/warranty/{SERIAL}",
        "support_phone": "1-800-555-0177",
        "support_email": "support@g17.vn",
        "notes": "Nhà sản xuất test nhóm 17",
    }
    m_create(page, man_created, MAN, name, fields)
    m_open_edit(page, MAN, name)
    expect(m_name(page)).to_have_value(name)
    for field_id, value in fields.items():
        expect(page.locator(f"#{field_id}")).to_have_value(value)


def test_manufacturer_05_empty_name(page: Page):
    """[Manufacturer-5] Bo trong truong Name."""
    check_empty_name(page, MAN, {"url": "https://g17.vn"})


def test_manufacturer_06_name_only_spaces(page: Page):
    """[Manufacturer-6] Name chi chua khoang trang."""
    check_spaces_name(page, MAN)


def test_manufacturer_07_duplicate_name(page: Page, man_created):
    """[Manufacturer-7] Them moi trung ten nha san xuat da co."""
    check_duplicate(page, MAN, man_created, lower=False)


def test_manufacturer_08_duplicate_name_different_case(page: Page, man_created):
    """[Manufacturer-8] Trung ten khac chu hoa/thuong."""
    check_duplicate(page, MAN, man_created, lower=True)


def test_manufacturer_09_name_max_length_255(page: Page, man_created):
    """[Manufacturer-9] Name 255 ky tu. Khao sat ghi nhan chi luu 191 ky tu."""
    check_name_255(page, MAN, man_created)


def test_manufacturer_10_paste_over_max_length(page: Page, man_created):
    """[Manufacturer-10] Dan Name 256 ky tu: ky vong co canh bao."""
    check_paste_256(page, MAN, man_created)


def test_manufacturer_11_vietnamese_and_special_chars(page: Page, man_created):
    """[Manufacturer-11] Name chua tieng Viet co dau va ky tu dac biet."""
    check_vietnamese(page, MAN, man_created, "Hãng Điện Tử")


def test_manufacturer_12_name_with_html_script(page: Page, man_created):
    """[Manufacturer-12] Name chua ma HTML/JavaScript (danh sach va trang chi tiet)."""
    check_xss(page, MAN, man_created)


def test_manufacturer_13_invalid_url_fields(page: Page):
    """[Manufacturer-13] URL, Support URL, Warranty Lookup URL sai dinh dang.
    Nhieu bo du lieu trong 1 test case (data-driven)."""
    data = [("url", "abc"), ("url", "www.g17.vn"),
            ("support_url", "abc"), ("warranty_lookup_url", "abc")]
    for field_id, value in data:
        m_open_create(page, MAN)
        m_name(page).fill(unique_name("UrlSai"))
        page.locator(f"#{field_id}").fill(value)
        save(page)
        expect(page.locator(f"#{field_id}-error")).to_contain_text(MSG_INVALID_URL)
        expect(page).to_have_url(re.compile(r"/create"))


def test_manufacturer_14_invalid_support_email(page: Page):
    """[Manufacturer-14] Support Email sai dinh dang."""
    m_open_create(page, MAN)
    m_name(page).fill(unique_name("EmailSai"))
    page.locator("#support_email").fill("abc")
    save(page)
    expect(page.locator("#support_email-error")).to_contain_text(MSG_INVALID_EMAIL)
    expect(page).to_have_url(re.compile(r"/create"))


def test_manufacturer_15_upload_valid_image(page: Page, man_created):
    """[Manufacturer-15] Tai anh dung dinh dang."""
    check_upload(page, MAN, man_created, valid=True)


def test_manufacturer_16_upload_invalid_file(page: Page, man_created):
    """[Manufacturer-16] Tai tep sai dinh dang (PDF)."""
    check_upload(page, MAN, man_created, valid=False)


def test_manufacturer_17_cancel_create(page: Page, man_created):
    """[Manufacturer-17] Huy thao tac tao moi."""
    check_cancel_create(page, MAN, man_created)


def test_manufacturer_18_edit_name_valid(page: Page, man_created):
    """[Manufacturer-18] Mo form sua va sua Name hop le."""
    check_edit_valid(page, MAN, man_created)


def test_manufacturer_19_edit_name_empty(page: Page, man_created):
    """[Manufacturer-19] Sua Name thanh rong."""
    check_edit_empty(page, MAN, man_created)


def test_manufacturer_20_edit_name_duplicate(page: Page, man_created):
    """[Manufacturer-20] Sua Name trung voi nha san xuat khac."""
    check_edit_duplicate(page, MAN, man_created)


def test_manufacturer_21_delete_unused(page: Page, man_created):
    """[Manufacturer-21] Xoa nha san xuat chua su dung, mo lai trang chi tiet."""
    check_delete_unused(page, MAN, man_created)


def test_manufacturer_22_cancel_delete(page: Page, man_created):
    """[Manufacturer-22] Huy thao tac xoa."""
    check_cancel_delete(page, MAN, man_created)


def test_manufacturer_23_bulk_delete(page: Page, man_created):
    """[Manufacturer-23] Xoa hang loat 2 nha san xuat."""
    check_bulk_delete(page, MAN, man_created)


def test_manufacturer_24_delete_used_by_accessory(page: Page, man_created, acc_created):
    """[Manufacturer-24] Xoa nha san xuat dang duoc phu kien su dung.
    Ky vong FAILED: khao sat ghi nhan thong bao hien "Manufacturer_name" thay ten that."""
    name = unique_name("Logitech")
    m_create(page, man_created, MAN, name)
    create_accessory(page, acc_created, unique_name("Mouse"), manufacturer=name)

    rows = find_in_list(page, name, MAN.url)
    delete_row(page, rows)
    message = error_alert(page).inner_text()
    # Kiem tra "van con" TRUOC, de neu cau thong bao sai thi phan nay van duoc kiem tra
    expect(find_in_list(page, name, MAN.url)).to_have_count(1)
    expected = f"{name} still has associated items. Please remove them before deleting this Manufacturer."
    assert expected in message, f"Thong bao thuc te: {message}"


@pytest.mark.xfail(reason="Cho xac nhan o Q&A: khao sat ngay 28/10 he thong cho xoa duoc", strict=False)
def test_manufacturer_25_delete_used_by_asset_model(page: Page, man_created, man_models):
    """[Manufacturer-25] Xoa nha san xuat dang duoc mau tai san su dung (cho Q&A).
    Danh dau xfail: neu he thong cho xoa, pytest bao XFAIL (khong tinh la loi)."""
    name = unique_name("Lenovo")
    model = unique_name("ThinkPad")
    m_create(page, man_created, MAN, name)
    man_models.append(model)
    page.goto(f"{MODELS_URL}/create")
    page.locator("input[name='name']").fill(model)
    select2_pick(page, "category_id", "Desktops")
    select2_pick(page, "manufacturer_id", name)
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_MODEL_CREATED)

    rows = find_in_list(page, name, MAN.url)
    delete_row(page, rows)
    expect(error_alert(page)).to_be_visible()
    expect(find_in_list(page, name, MAN.url)).to_have_count(1)


def test_manufacturer_26_view_deleted(page: Page, man_created):
    """[Manufacturer-26] Xem nha san xuat da xoa bang nut Deleted.
    Ky vong FAILED: khao sat ghi nhan nut Deleted khong loc ban ghi da xoa."""
    name = unique_name("Deleted")
    m_create(page, man_created, MAN, name)
    rows = find_in_list(page, name, MAN.url)
    delete_row(page, rows)
    expect(success_alert(page)).to_contain_text(MAN.deleted)

    page.goto(MAN.url)
    page.locator("button[name='btnShowDeleted']").click()
    page.wait_for_url(re.compile(r"status=deleted"))
    expect(search_current(page, name)).to_have_count(1)


def test_manufacturer_27_search(page: Page, man_created):
    """[Manufacturer-27] Tim kiem theo mot phan ten va tim khong co ket qua."""
    check_search(page, MAN, man_created)


def test_manufacturer_28_detail_page(page: Page, man_created):
    """[Manufacturer-28] Trang chi tiet nha san xuat.
    Buoc 2 (email dai co tran khung khong) kiem tra bang mat, khong tu dong hoa."""
    name = unique_name("Detail")
    m_create(page, man_created, MAN, name, {
        "url": "https://g17.vn", "support_phone": "1-800-555-0177",
        "support_email": "support@g17.vn",
    })
    rows = find_in_list(page, name, MAN.url)
    rows.get_by_role("link", name=name).first.click()
    expect(page).to_have_title(re.compile(re.escape(name)))
    for text in ("support@g17.vn", "1-800-555-0177", "https://g17.vn"):
        expect(visible_text(page, text)).to_be_visible()


def test_manufacturer_29_sort_by_name(page: Page):
    """[Manufacturer-29] Sap xep danh sach theo cot Name."""
    check_sort_by_name(page, MAN)


def test_manufacturer_30_paging(page: Page):
    """[Manufacturer-30] Chuyen trang danh sach (chon 10 dong moi trang)."""
    check_paging(page, MAN, "10")


# =====================================================================
# 14. SUPPLIERS ([Supplier-1], [Supplier-2]: kiem tra giao dien thu cong)
# =====================================================================
def test_supplier_03_create_required_only(page: Page, sup_created):
    """[Supplier-3] Them moi nha cung cap chi nhap truong bat buoc."""
    check_create_required_only(page, SUP, sup_created)


def test_supplier_04_create_all_fields(page: Page, sup_created):
    """[Supplier-4] Them moi nha cung cap nhap day du cac truong."""
    name = unique_name("PhongVu")
    fields = {
        "address": "123 Võ Văn Ngân", "address2": "Phường Linh Chiểu",
        "city": "Thủ Đức", "state": "Hồ Chí Minh", "zip": "700000",
        "contact": "Nguyễn Văn A", "phone": "0281234567", "fax": "0287654321",
        "email": "sales@g17.vn", "url": "https://g17.vn", "notes": "Nhà cung cấp test nhóm 17",
    }
    sup_created.append(name)
    m_open_create(page, SUP)
    m_name(page).fill(name)
    m_fill(page, fields)
    page.locator("select[name='country']").select_option("VN")
    save(page)
    page.wait_for_url(SUP.url)
    expect(success_alert(page)).to_contain_text(SUP.created)

    m_open_edit(page, SUP, name)
    expect(m_name(page)).to_have_value(name)
    for field_id, value in fields.items():
        expect(page.locator(f"#{field_id}")).to_have_value(value)
    expect(page.locator("select[name='country']")).to_have_value("VN")


def test_supplier_05_empty_name(page: Page):
    """[Supplier-5] Bo trong truong Supplier Name."""
    check_empty_name(page, SUP, {"city": "Thủ Đức"})


def test_supplier_06_name_only_spaces(page: Page):
    """[Supplier-6] Supplier Name chi chua khoang trang."""
    check_spaces_name(page, SUP)


def test_supplier_07_duplicate_name(page: Page, sup_created):
    """[Supplier-7] Them moi trung ten nha cung cap da co."""
    check_duplicate(page, SUP, sup_created, lower=False)


def test_supplier_08_duplicate_name_different_case(page: Page, sup_created):
    """[Supplier-8] Trung ten khac chu hoa/thuong."""
    check_duplicate(page, SUP, sup_created, lower=True)


def test_supplier_09_name_max_length_255(page: Page, sup_created):
    """[Supplier-9] Supplier Name 255 ky tu. Khao sat ghi nhan chi luu 191 ky tu."""
    check_name_255(page, SUP, sup_created)


def test_supplier_10_paste_over_max_length(page: Page, sup_created):
    """[Supplier-10] Dan Supplier Name 256 ky tu: ky vong co canh bao."""
    check_paste_256(page, SUP, sup_created)


def test_supplier_11_vietnamese_and_special_chars(page: Page, sup_created):
    """[Supplier-11] Supplier Name chua tieng Viet co dau va ky tu dac biet."""
    check_vietnamese(page, SUP, sup_created, "Công ty Phong Vũ")


def test_supplier_12_name_with_html_script(page: Page, sup_created):
    """[Supplier-12] Supplier Name chua ma HTML/JavaScript."""
    check_xss(page, SUP, sup_created)


def test_supplier_13_zip_and_contact_boundary(page: Page, sup_created):
    """[Supplier-13] Gia tri bien Zip (10) va Contact Name (100)."""
    name = unique_name("Bien")
    zip_code, contact = "1234567890", "B" * 100
    sup_created.append(name)
    m_open_create(page, SUP)
    m_name(page).fill(name)
    page.locator("#zip").fill(zip_code)
    page.locator("#zip").press_sequentially("1")  # go them 1 phim that
    expect(page.locator("#zip")).to_have_value(zip_code)
    page.locator("#contact").fill(contact)
    page.locator("#contact").press_sequentially("B")
    expect(page.locator("#contact")).to_have_value(contact)
    save(page)
    page.wait_for_url(SUP.url)
    expect(success_alert(page)).to_contain_text(SUP.created)

    m_open_edit(page, SUP, name)
    expect(page.locator("#zip")).to_have_value(zip_code)
    expect(page.locator("#contact")).to_have_value(contact)


def test_supplier_14_invalid_email(page: Page):
    """[Supplier-14] Email sai dinh dang."""
    m_open_create(page, SUP)
    m_name(page).fill(unique_name("EmailSai"))
    page.locator("#email").fill("abc")
    save(page)
    expect(page.locator("#email-error")).to_contain_text(MSG_INVALID_EMAIL)
    expect(page).to_have_url(re.compile(r"/create"))


def test_supplier_15_invalid_url(page: Page):
    """[Supplier-15] URL sai dinh dang (2 bo du lieu)."""
    for value in ("abc", "www.g17.vn"):
        m_open_create(page, SUP)
        m_name(page).fill(unique_name("UrlSai"))
        page.locator("#url").fill(value)
        save(page)
        expect(page.locator("#url-error")).to_contain_text(MSG_INVALID_URL)
        expect(page).to_have_url(re.compile(r"/create"))


def test_supplier_16_phone_fax_min_length(page: Page, sup_created):
    """[Supplier-16] Phone, Fax: 6 ky tu bi chan, 7 ky tu duoc chap nhan."""
    for field_id, label in (("phone", "phone"), ("fax", "fax")):
        name = unique_name(f"Short{label}")
        sup_created.append(name)  # phong khi he thong tao nham
        m_open_create(page, SUP)
        m_name(page).fill(name)
        page.locator(f"#{field_id}").fill("123456")
        save(page)
        expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
        expect(visible_text(page, f"The {label} field must be at least 7 characters.")).to_be_visible()

    m_create(page, sup_created, SUP, unique_name("Phone7"), {"phone": "1234567", "fax": "1234567"})


def test_supplier_17_select_country(page: Page, sup_created):
    """[Supplier-17] Chon Country bang o tim kiem cua danh sach."""
    name = unique_name("Country")
    sup_created.append(name)
    m_open_create(page, SUP)
    m_name(page).fill(name)
    page.locator("select[name='country'] + .select2").click()
    page.locator(".select2-container--open .select2-search__field").fill("Viet")
    options = page.locator(".select2-results__option")
    expect(options.first).to_be_visible()  # cho co ket qua
    texts = [t.strip() for t in options.all_inner_texts()]
    assert all("viet" in t.casefold() for t in texts), f"Co muc khong chua 'viet': {texts}"
    assert sum("Viet Nam" in t for t in texts) == 1, f"Phai co dung 1 muc 'Viet Nam': {texts}"
    options.filter(has_text=re.compile(r"Viet ?Nam", re.I)).first.click()
    save(page)
    page.wait_for_url(SUP.url)
    expect(success_alert(page)).to_contain_text(SUP.created)

    m_open_edit(page, SUP, name)
    expect(page.locator("select[name='country']")).to_have_value("VN")


def test_supplier_18_upload_valid_image(page: Page, sup_created):
    """[Supplier-18] Tai anh dung dinh dang."""
    check_upload(page, SUP, sup_created, valid=True)


def test_supplier_19_upload_invalid_file(page: Page, sup_created):
    """[Supplier-19] Tai tep sai dinh dang (PDF)."""
    check_upload(page, SUP, sup_created, valid=False)


def test_supplier_20_cancel_create(page: Page, sup_created):
    """[Supplier-20] Huy thao tac tao moi."""
    check_cancel_create(page, SUP, sup_created)


def test_supplier_21_edit_name_valid(page: Page, sup_created):
    """[Supplier-21] Mo form sua va sua Supplier Name hop le."""
    check_edit_valid(page, SUP, sup_created)


def test_supplier_22_edit_name_empty(page: Page, sup_created):
    """[Supplier-22] Sua Supplier Name thanh rong."""
    check_edit_empty(page, SUP, sup_created)


def test_supplier_23_edit_name_duplicate(page: Page, sup_created):
    """[Supplier-23] Sua Supplier Name trung voi nha cung cap khac."""
    check_edit_duplicate(page, SUP, sup_created)


def test_supplier_24_delete_unused(page: Page, sup_created):
    """[Supplier-24] Xoa nha cung cap chua su dung, mo lai trang chi tiet."""
    check_delete_unused(page, SUP, sup_created)


def test_supplier_25_cancel_delete(page: Page, sup_created):
    """[Supplier-25] Huy thao tac xoa."""
    check_cancel_delete(page, SUP, sup_created)


def test_supplier_26_bulk_delete(page: Page, sup_created):
    """[Supplier-26] Xoa hang loat 2 nha cung cap."""
    check_bulk_delete(page, SUP, sup_created)


def test_supplier_27_delete_used_by_accessory(page: Page, sup_created, acc_created):
    """[Supplier-27] Xoa nha cung cap dang duoc phu kien su dung.
    Ky vong FAILED: khao sat ghi nhan "Supplier_name" va ":accessory_count" khong duoc thay."""
    name = unique_name("CellphoneS")
    m_create(page, sup_created, SUP, name)
    create_accessory(page, acc_created, unique_name("Keyboard"), supplier=name)

    rows = find_in_list(page, name, SUP.url)
    delete_row(page, rows)
    message = error_alert(page).inner_text()
    expect(find_in_list(page, name, SUP.url)).to_have_count(1)
    expected = (f"{name} is currently associated with 1 accessory(ies) and cannot be deleted. "
                "Please update your accessories to no longer reference this Supplier and try again.")
    assert expected in message, f"Thong bao thuc te: {message}"


def test_supplier_28_search(page: Page, sup_created):
    """[Supplier-28] Tim kiem theo mot phan ten va tim khong co ket qua."""
    check_search(page, SUP, sup_created)


def test_supplier_29_detail_page(page: Page, sup_created):
    """[Supplier-29] Trang chi tiet nha cung cap.
    Buoc 2 (email dai co tran khung khong) kiem tra bang mat, khong tu dong hoa."""
    name = unique_name("Detail")
    m_create(page, sup_created, SUP, name, {
        "address": "123 Võ Văn Ngân", "city": "Thủ Đức", "email": "sales@g17.vn",
        "phone": "0281234567", "url": "https://g17.vn",
    })
    rows = find_in_list(page, name, SUP.url)
    rows.get_by_role("link", name=name).first.click()
    expect(page).to_have_title(re.compile(re.escape(name)))
    for text in ("123 Võ Văn Ngân", "sales@g17.vn", "0281234567", "https://g17.vn"):
        expect(visible_text(page, text)).to_be_visible()


def test_supplier_30_sort_by_name(page: Page):
    """[Supplier-30] Sap xep danh sach theo cot Name."""
    check_sort_by_name(page, SUP)


def test_supplier_31_paging(page: Page):
    """[Supplier-31] Chuyen trang danh sach (mac dinh 20 dong moi trang)."""
    check_paging(page, SUP, None)
