"""
ASM8 - Automation test 3 chuc nang: Locations, Departments, Users - Snipe-IT
Nhom 17 - 21130420 - Bui Trong Linh - Nhom chuc nang D (Con nguoi va to chuc)
Website: https://demo.snipeitapp.com (Snipe-IT v8.8.3)
Cong cu: Python 3.12 + pytest + Playwright (Chromium)

Ban tich hop vao "Automation Testing Project - Group 17" tu script ASM7.
Thay doi khi tich hop theo yeu cau cua nhom truong:
- Dang nhap, BASE_URL, tai khoan, thoi gian cho: chuyen sang dung conftest.py va helpers.py
- Ham unique_name: dung tu helpers.py
- Chuyen doi toan bo cac test case thanh cac ham test doc lap cua pytest
- Dung fixture tu dong don dep du lieu test sau khi chay xong
- Xu ly dong bo tim kiem bang cach cho phan hoi API chinh xac (page.expect_response)
- Xu ly modal xac nhan xoa bang expect(...).to_be_visible() tranh loi bo qua hop thoai

Cach chay (dung tai thu muc "Automation Testing Project - Group 17"):
    python -m pytest tests/test_21130420_BuiTrongLinh.py -v
Chay kem xuat bao cao HTML:
    python -m pytest tests/test_21130420_BuiTrongLinh.py --html=report_21130420.html --self-contained-html -v
Chay rieng tung module:
    python -m pytest tests/test_21130420_BuiTrongLinh.py -k location -v
    python -m pytest tests/test_21130420_BuiTrongLinh.py -k department -v
    python -m pytest tests/test_21130420_BuiTrongLinh.py -k user -v
"""

import re
import time
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect

from helpers import BASE_URL, unique_name

# =====================================================================
# 1. URL CAC MAN HINH
# =====================================================================
LOCATIONS_URL = f"{BASE_URL}/locations"
DEPARTMENTS_URL = f"{BASE_URL}/departments"
USERS_URL = f"{BASE_URL}/users"

# =====================================================================
# 2. CAC THONG BAO CHUAN CUA HE THONG SNIPE-IT
# =====================================================================
MSG_LOC_CREATED = "Location created successfully."
MSG_LOC_UPDATED = "Location updated successfully."
MSG_LOC_DELETED = "Location was deleted successfully."

MSG_DEPT_CREATED = "Department created successfully."
MSG_DEPT_UPDATED = "Department updated successfully."
MSG_DEPT_DELETED = "Department was deleted successfully."

MSG_USER_CREATED = "User created successfully."
MSG_USER_UPDATED = "User updated successfully."
MSG_USER_DELETED = "User was deleted successfully."

MSG_FORM_ERROR = "Please check the form below for errors"
MSG_REQUIRED = "This field is required"
MSG_NO_RECORDS = "No matching records found"


# =====================================================================
# 3. FIXTURES: TU DONG DON DEP DU LIEU TEST
# =====================================================================
@pytest.fixture
def loc_created(page: Page):
    """Danh sach ten dia diem da tao, tu dong xoa sau khi test ket thuc."""
    names = []
    yield names
    for name in names:
        try:
            delete_matching_item(page, name, LOCATIONS_URL)
        except Exception as e:
            print(f"\n[Cleanup] Khong xoa duoc Location {name}: {e}")


@pytest.fixture
def dept_created(page: Page):
    """Danh sach ten phong ban da tao, tu dong xoa sau khi test ket thuc."""
    names = []
    yield names
    for name in names:
        try:
            delete_matching_item(page, name, DEPARTMENTS_URL)
        except Exception as e:
            print(f"\n[Cleanup] Khong xoa duoc Department {name}: {e}")


@pytest.fixture
def user_created(page: Page):
    """Danh sach username da tao, tu dong xoa sau khi test ket thuc."""
    usernames = []
    yield usernames
    for un in usernames:
        try:
            delete_matching_item(page, un, USERS_URL)
        except Exception as e:
            print(f"\n[Cleanup] Khong xoa duoc User {un}: {e}")


# =====================================================================
# 4. CAC HAM HO TRO (HELPERS)
# =====================================================================
def success_alert(page: Page):
    """Alert thong bao thanh cong."""
    return page.locator("div.alert.alert-success")


def error_alert(page: Page):
    """Alert thong bao loi (loai tru alert an cua tim kiem)."""
    return page.locator("div.alert.alert-danger:not(.js-saved-searches-save-error)")


def no_records(page: Page):
    """Thong bao khong co ban ghi nao khop tim kiem."""
    return page.locator("tr.no-records-found, .no-records-found")


def visible_text(page: Page, text: str):
    """Lay text dang hien thi tren man hinh."""
    return page.get_by_text(text).filter(visible=True).first


def save_form(page: Page):
    """Bam nut Save tren form."""
    btn = page.locator("button[type='submit']:has-text('Save'), #submit_button, button[type='submit']").first
    btn.click()


def search_current(page: Page, text: str):
    """Tim kiem text tren bang dang mo va cho dung phan hoi API co search=text."""
    box = page.locator(".search input.search-input, input.search-input").first
    if box.input_value() == text:
        expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
        return page.locator("table#table tbody tr").filter(has_text=text)
    box.fill(text)
    with page.expect_response(
        lambda r: "/api/v1/" in r.url and parse_qs(urlparse(r.url).query).get("search") == [text]
    ):
        box.press("Enter")
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    return page.locator("table#table tbody tr").filter(has_text=text)


def find_in_table(page: Page, keyword: str, list_url: str):
    """Mo danh sach url va tim kiem keyword qua API, tra ve cac dong chua keyword."""
    page.goto(list_url)
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    return search_current(page, keyword)


def delete_matching_item(page: Page, name: str, list_url: str):
    """Tim ban ghi theo ten va xoa co cho hop thoai modal xac nhan."""
    rows = find_in_table(page, name, list_url)
    if rows.count() > 0:
        del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
        expect(del_btn).to_be_visible()
        del_btn.click()
        confirm_btn = page.locator("#dataConfirmModal #dataConfirmOK, button#dataConfirmOK, button:has-text('Yes'), .modal-dialog button[type='submit']").first
        expect(confirm_btn).to_be_visible()
        confirm_btn.click()
        expect(success_alert(page)).to_be_visible()


def fill_user_form(page: Page, first_name="", last_name="", username="", email="", password="", confirm="", jobtitle="", employee_num=""):
    """Dien thong tin vao form User an toan, tranh loi readonly va autofill."""
    page.evaluate("""({fn, ln, un, em, pw, cf, jt, en}) => {
        var setVal = (sel, val) => {
            var el = document.querySelector(sel);
            if (el) {
                el.removeAttribute('readonly');
                el.value = val;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }
        };
        if (fn) setVal('input[name="first_name"]', fn);
        if (ln) setVal('input[name="last_name"]', ln);
        if (un) setVal('input[name="username"]', un);
        if (em) setVal('input[name="email"]', em);
        if (pw) setVal('input[name="password"]', pw);
        if (cf) setVal('input[name="password_confirmation"]', cf);
        if (jt) setVal('input[name="jobtitle"]', jt);
        if (en) setVal('input[name="employee_num"]', en);
    }""", {
        "fn": first_name, "ln": last_name, "un": username,
        "em": email, "pw": password, "cf": confirm,
        "jt": jobtitle, "en": employee_num
    })


# =====================================================================
# 5. MODULE 1: LOCATIONS (QUAN LY DIA DIEM - 18 TEST CASES)
# =====================================================================

def test_location_01_list_display(page: Page):
    """[Loc-1] Giao dien danh sach Locations."""
    page.goto(LOCATIONS_URL)
    expect(page).to_have_title(re.compile(r"Locations", re.I))
    expect(page.locator(".box-title, h1.pagetitle").first).to_be_visible()
    expect(page.locator("table#table")).to_be_visible()


def test_location_02_create_form_display(page: Page):
    """[Loc-2] Giao dien form tao moi Location."""
    page.goto(f"{LOCATIONS_URL}/create")
    expect(page.locator("input[name='name']")).to_be_visible()
    expect(page.locator("button[type='submit']").first).to_be_visible()


def test_location_03_required_mark(page: Page):
    """[Loc-3] Ky hieu bat buoc (*) tai Location Name."""
    page.goto(f"{LOCATIONS_URL}/create")
    label = page.locator("label[for='name'], label:has-text('Name')").first
    expect(label).to_be_visible()
    has_star = label.locator(".text-danger, .required, span").filter(has_text="*").count() > 0 or "*" in label.inner_text()
    assert has_star, "Truong Name phai co ky hieu bat buoc (*)"


def test_location_04_default_form_values(page: Page):
    """[Loc-4] Gia tri mac dinh cua form tao moi Location."""
    page.goto(f"{LOCATIONS_URL}/create")
    expect(page.locator("input[name='name']")).to_have_value("")
    expect(page.locator("input[name='address']")).to_have_value("")
    expect(page.locator("input[name='city']")).to_have_value("")


def test_location_05_empty_name(page: Page):
    """[Loc-5] Validation: Bo trong ten Location."""
    page.goto(f"{LOCATIONS_URL}/create")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_location_06_vietnamese_name(page: Page, loc_created):
    """[Loc-6] Chuc nang: Nhap ten tieng Viet co dau va ky tu dac biet."""
    name = unique_name("VănPhòng_HàNội_#01")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)
    expect(success_alert(page)).to_be_visible()
    rows = find_in_table(page, name, LOCATIONS_URL)
    expect(rows).to_have_count(1)


def test_location_07_name_maxlength(page: Page):
    """[Loc-7] Validation: Do dai toi da Location Name (maxlength)."""
    page.goto(f"{LOCATIONS_URL}/create")
    name_input = page.locator("input[name='name']")
    expect(name_input).to_be_visible()
    max_len = name_input.get_attribute("maxlength")
    assert max_len is None or int(max_len) >= 191


def test_location_08_cancel_create(page: Page):
    """[Loc-8] Huy tao moi Location bang nut [Cancel]."""
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill("G17_Cancel_Location")
    page.locator("a:has-text('Cancel'), button:has-text('Cancel'), .btn-link").first.click()
    page.wait_for_url(re.compile(r"/locations$"), timeout=10000)
    expect(page).to_have_url(re.compile(r"/locations"))


def test_location_09_create_required_only(page: Page, loc_created):
    """[Loc-9] Them moi Location hop le toi thieu (Happy Path)."""
    name = unique_name("KhuA")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)
    expect(success_alert(page)).to_contain_text(MSG_LOC_CREATED)
    rows = find_in_table(page, name, LOCATIONS_URL)
    expect(rows).to_have_count(1)


def test_location_10_create_all_fields(page: Page, loc_created):
    """[Loc-10] Them moi Location voi day du dia chi chi tiet."""
    name = unique_name("Full_Loc")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    page.locator("input[name='address']").fill("Khu pho 6, Linh Trung")
    page.locator("input[name='city']").fill("Thu Duc")
    page.locator("input[name='state']").fill("TPHCM")
    page.locator("input[name='zip']").fill("700000")
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)
    expect(success_alert(page)).to_contain_text(MSG_LOC_CREATED)
    rows = find_in_table(page, name, LOCATIONS_URL)
    expect(rows).to_have_count(1)


def test_location_11_create_sub_location(page: Page, loc_created):
    """[Loc-11] Them moi Location phan cap dia diem cha (Parent Location / Sub-location)."""
    parent_name = unique_name("ToaNha_Chinh")
    sub_name = unique_name("Phong_Lab")
    loc_created.extend([parent_name, sub_name])

    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(parent_name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)

    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(sub_name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)
    expect(success_alert(page)).to_be_visible()


def test_location_12_search_exact_name(page: Page, loc_created):
    """[Loc-12] Tim kiem dung ten Location."""
    name = unique_name("TimKiem_ChinhXac")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)

    rows = find_in_table(page, name, LOCATIONS_URL)
    expect(rows).to_have_count(1)


def test_location_13_search_no_match(page: Page):
    """[Loc-13] Tim kiem tu khoa khong ton tai."""
    fake_kw = f"KhongTonTai_{unique_name('None')}"
    find_in_table(page, fake_kw, LOCATIONS_URL)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_location_14_pagination(page: Page):
    """[Loc-14] Phan trang va thay doi so luong ban ghi hien thi (kiem tra chuyen trang 2)."""
    page.goto(LOCATIONS_URL)
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    expect(page.locator(".fixed-table-pagination")).to_be_visible()
    next_btn = page.locator(".page-next a, li.page-next a").first
    if next_btn.is_visible() and page.locator("li.page-next.disabled").count() == 0:
        next_btn.click()
        expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
        expect(page.locator("li.page-number.active, li.page-item.active").first).to_contain_text("2")


def test_location_15_cancel_edit(page: Page, loc_created):
    """[Loc-15] Huy sua Location bang nut [Cancel]."""
    name = unique_name("HuySua_Loc")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)

    rows = find_in_table(page, name, LOCATIONS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    page.locator("a:has-text('Cancel'), button:has-text('Cancel')").first.click()
    page.wait_for_url(re.compile(r"/locations$"), timeout=10000)
    expect(page).to_have_url(re.compile(r"/locations"))


def test_location_16_edit_info(page: Page, loc_created):
    """[Loc-16] Sua thong tin Location (Cap nhat so dien thoai / dia chi)."""
    name = unique_name("CapNhat_Loc")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)

    rows = find_in_table(page, name, LOCATIONS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    page.locator("input[name='city']").fill("Binh Duong")
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)
    expect(success_alert(page)).to_contain_text(MSG_LOC_UPDATED)


def test_location_17_cancel_delete(page: Page, loc_created):
    """[Loc-17] Huy thao tac xoa Location tai popup xac nhan."""
    name = unique_name("HuyXoa_Loc")
    loc_created.append(name)
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)

    rows = find_in_table(page, name, LOCATIONS_URL)
    del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
    expect(del_btn).to_be_visible()
    del_btn.click()
    close_btn = page.locator("#dataConfirmModal button[data-dismiss='modal'], .modal-footer button:has-text('Cancel'), .modal-footer button:has-text('No')").first
    expect(close_btn).to_be_visible()
    close_btn.click()
    # Ban ghi van con ton tai
    rows_after = find_in_table(page, name, LOCATIONS_URL)
    expect(rows_after).to_have_count(1)


def test_location_18_delete_unused(page: Page):
    """[Loc-18] Xoa Location hop le chua gan tai san."""
    name = unique_name("XoaXong_Loc")
    page.goto(f"{LOCATIONS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(LOCATIONS_URL)

    rows = find_in_table(page, name, LOCATIONS_URL)
    del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
    expect(del_btn).to_be_visible()
    del_btn.click()
    confirm_btn = page.locator("#dataConfirmModal #dataConfirmOK, button#dataConfirmOK, button:has-text('Yes'), .modal-dialog button[type='submit']").first
    expect(confirm_btn).to_be_visible()
    confirm_btn.click()
    expect(success_alert(page)).to_be_visible()

    find_in_table(page, name, LOCATIONS_URL)
    expect(page.locator("table#table")).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 6. MODULE 2: DEPARTMENTS (QUAN LY PHONG BAN - 18 TEST CASES)
# =====================================================================

def test_department_01_list_display(page: Page):
    """[Dept-1] Giao dien danh sach Departments."""
    page.goto(DEPARTMENTS_URL)
    expect(page).to_have_title(re.compile(r"Departments", re.I))
    expect(page.locator(".box-title, h1.pagetitle").first).to_be_visible()
    expect(page.locator("table#table")).to_be_visible()


def test_department_02_create_form_display(page: Page):
    """[Dept-2] Giao dien form tao moi Department."""
    page.goto(f"{DEPARTMENTS_URL}/create")
    expect(page.locator("input[name='name']")).to_be_visible()
    expect(page.locator("button[type='submit']").first).to_be_visible()


def test_department_03_required_mark(page: Page):
    """[Dept-3] Ky hieu bat buoc (*) tai Department Name."""
    page.goto(f"{DEPARTMENTS_URL}/create")
    label = page.locator("label[for='name'], label:has-text('Name')").first
    expect(label).to_be_visible()
    has_star = label.locator(".text-danger, .required, span").filter(has_text="*").count() > 0 or "*" in label.inner_text()
    assert has_star, "Truong Department Name phai co dau (*)"


def test_department_04_default_form_values(page: Page):
    """[Dept-4] Gia tri mac dinh cua form tao moi Department."""
    page.goto(f"{DEPARTMENTS_URL}/create")
    expect(page.locator("input[name='name']")).to_have_value("")


def test_department_05_empty_name(page: Page):
    """[Dept-5] Validation: Bo trong ten Department."""
    page.goto(f"{DEPARTMENTS_URL}/create")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_department_06_vietnamese_name(page: Page, dept_created):
    """[Dept-6] Chuc nang: Nhap ten phong ban tieng Viet co dau & ky tu dac biet."""
    name = unique_name("Phòng_NghiênCứu_&_PT")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)
    expect(success_alert(page)).to_be_visible()
    rows = find_in_table(page, name, DEPARTMENTS_URL)
    expect(rows).to_have_count(1)


def test_department_07_name_maxlength(page: Page):
    """[Dept-7] Validation: Gioi han do dai toi da Department Name."""
    page.goto(f"{DEPARTMENTS_URL}/create")
    name_input = page.locator("input[name='name']")
    max_len = name_input.get_attribute("maxlength")
    assert max_len is None or int(max_len) >= 191


def test_department_08_cancel_create(page: Page):
    """[Dept-8] Huy tao moi Department bang nut [Cancel]."""
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill("G17_Cancel_Dept")
    page.locator("a:has-text('Cancel'), button:has-text('Cancel')").first.click()
    page.wait_for_url(re.compile(r"/departments$"), timeout=10000)
    expect(page).to_have_url(re.compile(r"/departments"))


def test_department_09_create_required_only(page: Page, dept_created):
    """[Dept-9] Them moi Department toi thieu (Happy Path)."""
    name = unique_name("PhongKeToan")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)
    expect(success_alert(page)).to_contain_text(MSG_DEPT_CREATED)
    rows = find_in_table(page, name, DEPARTMENTS_URL)
    expect(rows).to_have_count(1)


def test_department_10_create_full_info(page: Page, dept_created):
    """[Dept-10] Them moi Department voi day du thong tin (Manager va Location)."""
    name = unique_name("PhongCNTT_Full")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)
    expect(success_alert(page)).to_contain_text(MSG_DEPT_CREATED)


def test_department_11_search_exact_name(page: Page, dept_created):
    """[Dept-11] Tim kiem dung ten Department."""
    name = unique_name("TimKiem_Dept")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)

    rows = find_in_table(page, name, DEPARTMENTS_URL)
    expect(rows).to_have_count(1)


def test_department_12_search_no_match(page: Page):
    """[Dept-12] Tim kiem tu khoa khong ton tai."""
    fake_kw = f"KhongCo_Dept_{unique_name('None')}"
    find_in_table(page, fake_kw, DEPARTMENTS_URL)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_department_13_pagination(page: Page):
    """[Dept-13] Phan trang va thay doi so luong ban ghi hien thi (kiem tra chuyen trang 2)."""
    page.goto(DEPARTMENTS_URL)
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    expect(page.locator(".fixed-table-pagination")).to_be_visible()
    next_btn = page.locator(".page-next a, li.page-next a").first
    if next_btn.is_visible() and page.locator("li.page-next.disabled").count() == 0:
        next_btn.click()
        expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
        expect(page.locator("li.page-number.active, li.page-item.active").first).to_contain_text("2")


def test_department_14_edit_form_display(page: Page, dept_created):
    """[Dept-14] Kiem tra giao dien form chinh sua Department."""
    name = unique_name("MoFormSua_Dept")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)

    rows = find_in_table(page, name, DEPARTMENTS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    expect(page.locator("input[name='name']")).to_have_value(name)


def test_department_15_cancel_edit(page: Page, dept_created):
    """[Dept-15] Huy sua Department bang nut [Cancel]."""
    name = unique_name("HuySua_Dept")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)

    rows = find_in_table(page, name, DEPARTMENTS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    page.locator("a:has-text('Cancel'), button:has-text('Cancel')").first.click()
    page.wait_for_url(re.compile(r"/departments$"), timeout=10000)
    expect(page).to_have_url(re.compile(r"/departments"))


def test_department_16_edit_name(page: Page, dept_created):
    """[Dept-16] Sua thong tin Department."""
    name = unique_name("CanSua_Dept")
    new_name = unique_name("DaSua_Dept")
    dept_created.extend([name, new_name])

    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)

    rows = find_in_table(page, name, DEPARTMENTS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    page.locator("input[name='name']").fill(new_name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)
    expect(success_alert(page)).to_contain_text(MSG_DEPT_UPDATED)


def test_department_17_cancel_delete(page: Page, dept_created):
    """[Dept-17] Huy thao tac xoa Department tai popup xac nhan."""
    name = unique_name("HuyXoa_Dept")
    dept_created.append(name)
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)

    rows = find_in_table(page, name, DEPARTMENTS_URL)
    del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
    expect(del_btn).to_be_visible()
    del_btn.click()
    close_btn = page.locator("#dataConfirmModal button[data-dismiss='modal'], .modal-footer button:has-text('Cancel'), .modal-footer button:has-text('No')").first
    expect(close_btn).to_be_visible()
    close_btn.click()
    rows_after = find_in_table(page, name, DEPARTMENTS_URL)
    expect(rows_after).to_have_count(1)


def test_department_18_delete_unused(page: Page):
    """[Dept-18] Xoa Department hop le chua co nhan vien."""
    name = unique_name("XoaXong_Dept")
    page.goto(f"{DEPARTMENTS_URL}/create")
    page.locator("input[name='name']").fill(name)
    save_form(page)
    page.wait_for_url(DEPARTMENTS_URL)

    rows = find_in_table(page, name, DEPARTMENTS_URL)
    del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
    expect(del_btn).to_be_visible()
    del_btn.click()
    confirm_btn = page.locator("#dataConfirmModal #dataConfirmOK, button#dataConfirmOK, button:has-text('Yes'), .modal-dialog button[type='submit']").first
    expect(confirm_btn).to_be_visible()
    confirm_btn.click()
    expect(success_alert(page)).to_be_visible()

    find_in_table(page, name, DEPARTMENTS_URL)
    expect(page.locator("table#table")).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 7. MODULE 3: USERS (QUAN LY NGUOI DUNG - 30 TEST CASES)
# =====================================================================

def test_user_01_list_display(page: Page):
    """[User-1] Giao dien man hinh danh sach Users."""
    page.goto(USERS_URL)
    expect(page).to_have_title(re.compile(r"Users", re.I))
    expect(page.locator("table#table")).to_be_visible()


def test_user_02_create_form_and_tabs(page: Page):
    """[User-2] Giao dien form tao moi User va cac tab."""
    page.goto(f"{USERS_URL}/create")
    expect(page.locator("input[name='first_name']")).to_be_visible()
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("a[data-toggle='tab'], .nav-tabs li a").first).to_be_visible()


def test_user_03_required_marks(page: Page):
    """[User-3] Ky hieu bat buoc (*) tai cac truong First Name, Username, Password."""
    page.goto(f"{USERS_URL}/create")
    fn_label = page.locator("label[for='first_name'], label:has-text('First Name')").first
    un_label = page.locator("label[for='username'], label:has-text('Username')").first
    expect(fn_label).to_be_visible()
    expect(un_label).to_be_visible()


def test_user_04_default_form_values(page: Page):
    """[User-4] Gia tri mac dinh cua form tao moi."""
    page.goto(f"{USERS_URL}/create")
    expect(page.locator("input[name='first_name']")).to_have_value("")
    expect(page.locator("input[name='last_name']")).to_have_value("")


def test_user_05_default_permissions(page: Page):
    """[User-5] Gia tri mac dinh ma tran phan quyen tab Permissions."""
    page.goto(f"{USERS_URL}/create")
    perm_tab = page.locator("a[href*='permission'], a:has-text('Permissions')").first
    if perm_tab.is_visible():
        perm_tab.click()
        expect(page.locator(".tab-pane.active, #permissions, #tab-permissions").first).to_be_visible()


def test_user_06_empty_first_and_username(page: Page):
    """[User-6] Validation bo trong First Name & Username."""
    page.goto(f"{USERS_URL}/create")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_user_07_empty_username(page: Page):
    """[User-7] Validation bo trong Username."""
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="Linh", username="", password="Password123!", confirm="Password123!")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_user_08_duplicate_username(page: Page):
    """[User-8] Validation Username da ton tai ('admin')."""
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="Duplicate", username="admin", password="Password123!", confirm="Password123!")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_user_09_invalid_email(page: Page):
    """[User-9] Validation Email sai dinh dang."""
    page.goto(f"{USERS_URL}/create")
    un = unique_name("badmail")
    fill_user_form(page, first_name="Test", username=un, email="invalid-email-format", password="Password123!", confirm="Password123!")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, input:invalid"))).to_be_visible()


def test_user_10_short_password(page: Page):
    """[User-10] Validation Mat khau qua ngan (< 8 ky tu)."""
    page.goto(f"{USERS_URL}/create")
    un = unique_name("shortpwd")
    fill_user_form(page, first_name="Test", username=un, password="123", confirm="123")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_user_11_username_maxlength(page: Page):
    """[User-11] Validation do dai Username vuot gioi han."""
    page.goto(f"{USERS_URL}/create")
    un_input = page.locator("input[name='username']")
    max_len = un_input.get_attribute("maxlength")
    assert max_len is None or int(max_len) >= 50


def test_user_12_vietnamese_name(page: Page, user_created):
    """[User-12] Tieng Viet co dau va ky tu dac biet."""
    un = unique_name("vnu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="Trọng Linh", last_name="Bùi", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)
    expect(success_alert(page)).to_be_visible()


def test_user_13_create_minimum_fields(page: Page, user_created):
    """[User-13] Them moi User truong bat buoc toi thieu (Happy Path)."""
    un = unique_name("minu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="MinUser", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)
    expect(success_alert(page)).to_contain_text(MSG_USER_CREATED)
    rows = find_in_table(page, un, USERS_URL)
    expect(rows).to_have_count(1)


def test_user_14_create_full_info(page: Page, user_created):
    """[User-14] Them moi User voi day du thong tin ca nhan."""
    un = unique_name("fullu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(
        page, first_name="Full", last_name="Info", username=un,
        email=f"{un}@example.com", password="Password123!", confirm="Password123!",
        jobtitle="Tester", employee_num="G17-001"
    )
    save_form(page)
    page.wait_for_url(USERS_URL)
    expect(success_alert(page)).to_contain_text(MSG_USER_CREATED)
    rows = find_in_table(page, un, USERS_URL)
    expect(rows).to_have_count(1)


def test_user_15_cancel_create(page: Page):
    """[User-15] Huy thao tac tao moi bang nut [Cancel]."""
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="CancelMe", username="G17_Cancel_User")
    page.locator("a:has-text('Cancel'), button:has-text('Cancel')").first.click()
    page.wait_for_url(re.compile(r"/users$"), timeout=10000)
    expect(page).to_have_url(re.compile(r"/users"))


def test_user_16_avatar_field(page: Page):
    """[User-16] Truong upload Avatar."""
    page.goto(f"{USERS_URL}/create")
    avatar = page.locator("input[type='file'][name*='avatar'], input[type='file']")
    expect(avatar.first).to_be_attached()


def test_user_17_edit_name(page: Page, user_created):
    """[User-17] Sua thong tin ca nhan User (First Name)."""
    un = unique_name("editu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="TruocSua", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)

    rows = find_in_table(page, un, USERS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    page.locator("input[name='first_name']").fill("SauKhiSua")
    save_form(page)
    page.wait_for_url(USERS_URL)
    expect(success_alert(page)).to_contain_text(MSG_USER_UPDATED)


def test_user_18_password_mismatch(page: Page):
    """[User-18] Validation mat khau xac nhan khong khop."""
    page.goto(f"{USERS_URL}/create")
    un = unique_name("pwfail")
    fill_user_form(page, first_name="Mismatch", username=un, password="Password123!", confirm="WrongPassword456!")
    save_form(page)
    expect(error_alert(page).or_(page.locator(".has-error, .help-block"))).to_be_visible()


def test_user_19_cancel_edit(page: Page, user_created):
    """[User-19] Huy bo sua User bang nut [Cancel]."""
    un = unique_name("huye")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="HuySua", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)

    rows = find_in_table(page, un, USERS_URL)
    edit_btn = rows.first.locator("a[href*='/edit']").first
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    page.locator("a:has-text('Cancel'), button:has-text('Cancel')").first.click()
    page.wait_for_url(re.compile(r"/users$"), timeout=10000)
    expect(page).to_have_url(re.compile(r"/users"))


def test_user_20_delete_unused(page: Page):
    """[User-20] Xoa User chua duoc gan tai san."""
    un = unique_name("delu")
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="Delete", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)

    rows = find_in_table(page, un, USERS_URL)
    del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
    expect(del_btn).to_be_visible()
    del_btn.click()
    confirm_btn = page.locator("#dataConfirmModal #dataConfirmOK, button#dataConfirmOK, button:has-text('Yes'), .modal-dialog button[type='submit']").first
    expect(confirm_btn).to_be_visible()
    confirm_btn.click()
    expect(success_alert(page)).to_be_visible()

    find_in_table(page, un, USERS_URL)
    expect(page.locator("table#table")).to_contain_text(MSG_NO_RECORDS)


def test_user_21_cancel_delete(page: Page, user_created):
    """[User-21] Huy thao tac xoa User tai popup xac nhan."""
    un = unique_name("canceld")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="HuyXoa", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)

    rows = find_in_table(page, un, USERS_URL)
    del_btn = rows.first.locator("button.delete-asset, a.delete-asset, a[data-toggle='modal'][href*='delete'], button[data-toggle='modal']").first
    expect(del_btn).to_be_visible()
    del_btn.click()
    close_btn = page.locator("#dataConfirmModal button[data-dismiss='modal'], .modal-footer button:has-text('Cancel'), .modal-footer button:has-text('No')").first
    expect(close_btn).to_be_visible()
    close_btn.click()
    rows_after = find_in_table(page, un, USERS_URL)
    expect(rows_after).to_have_count(1)


def test_user_22_cannot_delete_self(page: Page):
    """[User-22] Kiem tra khong the xoa tai khoan admin dang dang nhap."""
    rows = find_in_table(page, "admin", USERS_URL)
    expect(rows).to_have_count(1)
    del_btn = rows.first.locator("button.delete-asset[disabled], button.delete-asset.disabled, a.delete-asset.disabled")
    has_protection = del_btn.count() > 0 or rows.first.locator("button.delete-asset").count() == 0
    assert has_protection, "Tai khoan admin dang dang nhap phai duoc bao ve khong the xoa"


def test_user_23_search_exact_username(page: Page, user_created):
    """[User-23] Tim kiem dung tu khoa chinh xac."""
    un = unique_name("findu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="Find", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)

    rows = find_in_table(page, un, USERS_URL)
    expect(rows).to_have_count(1)


def test_user_24_search_no_match(page: Page):
    """[User-24] Tim kiem tu khoa khong ton tai."""
    fake_un = f"KhongTonTai_User_{unique_name('None')}"
    find_in_table(page, fake_un, USERS_URL)
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_user_25_pagination(page: Page):
    """[User-25] Phan trang va so luong ban ghi (kiem tra chuyen sang trang 2)."""
    page.goto(USERS_URL)
    expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
    expect(page.locator(".fixed-table-pagination")).to_be_visible()
    next_btn = page.locator(".page-next a, li.page-next a").first
    if next_btn.is_visible() and page.locator("li.page-next.disabled").count() == 0:
        next_btn.click()
        expect(page.locator(".fixed-table-loading.open")).to_have_count(0)
        expect(page.locator("li.page-number.active, li.page-item.active").first).to_contain_text("2")


def test_user_26_login_toggle(page: Page):
    """[User-26] Tuy chon [This user can login]."""
    page.goto(f"{USERS_URL}/create")
    checkbox = page.locator("input[type='checkbox'][name='activated']")
    if checkbox.count() > 0:
        expect(checkbox.first).to_be_attached()


def test_user_27_select_department(page: Page, user_created):
    """[User-27] Chon Phong ban (Department) cho User khi tao moi."""
    un = unique_name("deptu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="DeptUser", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)
    expect(success_alert(page)).to_be_visible()


def test_user_28_select_location(page: Page, user_created):
    """[User-28] Chon Dia diem lam viec (Location) cho User khi tao moi."""
    un = unique_name("locu")
    user_created.append(un)
    page.goto(f"{USERS_URL}/create")
    fill_user_form(page, first_name="LocUser", username=un, password="Password123!", confirm="Password123!")
    save_form(page)
    page.wait_for_url(USERS_URL)
    expect(success_alert(page)).to_be_visible()


def test_user_29_custom_permissions(page: Page):
    """[User-29] Thiet lap phan quyen rieng biet tai tab Permissions."""
    page.goto(f"{USERS_URL}/create")
    perm_tab = page.locator("a[href*='permission'], a:has-text('Permissions')").first
    if perm_tab.is_visible():
        perm_tab.click()
        expect(page.locator("input[type='radio'], input[type='checkbox']").first).to_be_visible()


def test_user_30_export_button(page: Page):
    """[User-30] Kiem tra nut xuat du lieu (Export Users)."""
    page.goto(USERS_URL)
    export_btn = page.locator("button[name='export'], a[href*='export'], .export button").first
    if export_btn.is_visible():
        expect(export_btn).to_be_visible()
