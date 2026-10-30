"""
ASM7 - Automation test 3 chuc nang: Assets, Checkout/Checkin, Asset Models - Snipe-IT
Nhom 17 - 23130303 - Nguyen Huu Thanh
Website: https://demo.snipeitapp.com (Snipe-IT v8.8.3)
Cong cu: Python 3.12 + pytest + playwright

Cach chay (Terminal phai hien (.venv)):
    python -m pytest 23130303_NguyenHuuThanh_ASM7.py --headed --slowmo 500 -v
Chay rieng 1 chuc nang:
    python -m pytest 23130303_NguyenHuuThanh_ASM7.py -k asset -v
Chay rieng 1 test case, vi du [Asset-8]:
    python -m pytest 23130303_NguyenHuuThanh_ASM7.py -k asset_08 --headed -v

Moi ham test ung voi 1 test case trong file Group17_23130303_NguyenHuuThanh.xlsx
(test_asset_08_... = [Asset-8], test_checkout_03_... = [Checkout-3],
test_model_05_... = [Model-5]). Cac test case giao dien ([Asset-1..4]) kiem tra
bang mat nen thuc hien thu cong, khong dua vao script.

Moi test tu tao du lieu ten G17_... va tu xoa sau khi chay, nen cac test khong phu
thuoc nhau va chay duoc theo thu tu bat ky. Demo dung chung va hay bi reset nen
script khong bao gio assert tong so ban ghi toan he thong, chi tim theo tien to G17_.
"""

import base64
import re
import time

import pytest
from playwright.sync_api import Page, expect

# =====================================================================
# 1. CAU HINH MOI TRUONG (giong Profile trong Katalon)
# =====================================================================
BASE_URL = "https://demo.snipeitapp.com"
USERNAME = "admin"
PASSWORD = "password"
ASSETS_URL = f"{BASE_URL}/hardware"
MODELS_URL = f"{BASE_URL}/models"

# Demo phan hoi cham va thinh thoang tra 503: cho toi da 15 giay cho moi buoc kiem tra
expect.set_options(timeout=15_000)

# =====================================================================
# 2. CAU THONG BAO DA XAC NHAN TREN TRANG THAT (khao sat 30/10/2026)
# =====================================================================
MSG_ASSET_CREATED = "was created successfully"
MSG_ASSET_UPDATED = "Asset updated successfully"
MSG_ASSET_DELETED = "The asset was deleted successfully"
MSG_MODEL_CREATED = "Model created successfully."
MSG_MODEL_UPDATED = "Model updated successfully"
MSG_MODEL_DELETED = "The model was deleted successfully."
MSG_MODEL_USED = "This model is currently associated with one or more assets and cannot be deleted"
MSG_CHECKOUT_OK = "Asset checked out successfully"
MSG_CHECKIN_OK = "Asset checked in successfully"
MSG_FORM_ERROR = "Please check the form below for errors"
MSG_TAG_UNIQUE = "The Asset Tag must be unique."
MSG_MODEL_UNIQUE = "The name must be unique across models and model number."
MSG_REQUIRED_HTML = "Please fill out this field"
MSG_SELECT_HTML = "Please select an item in the list"
MSG_NO_RECORDS = "No matching records found"

# Tep test tao ngay trong code (khong can file di kem, giu dung quy dinh 1 file script)
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


# =====================================================================
# 3. FIXTURE: Pre-condition va don dep viet thanh code
# =====================================================================
@pytest.fixture(autouse=True)
def logged_in(page: Page):
    """Pre-condition chung: dang nhap thanh cong bang admin/password."""
    page.set_default_timeout(20_000)
    login(page)


@pytest.fixture
def created_assets(page: Page):
    """Danh sach Asset Tag da tao. Sau khi test ket thuc (ke ca khi that bai),
    moi tai san trong danh sach deu duoc tim va xoa."""
    tags: list[str] = []
    yield tags
    for tag in tags:
        try:
            delete_asset_by_tag(page, tag)
        except Exception as error:  # don dep loi khong duoc che mat ket qua test
            print(f"\n[Don dep] Khong xoa duoc tai san {tag}: {error}")


@pytest.fixture
def created_models(page: Page):
    """Danh sach Asset Model da tao. Fixture nay duoc don TRUOC created_assets
    vi model phai duoc xoa sau khi tai san cua no da bi xoa."""
    names: list[str] = []
    yield names
    for name in names:
        try:
            delete_model_by_name(page, name)
        except Exception as error:  # don dep loi khong duoc che mat ket qua test
            print(f"\n[Don dep] Khong xoa duoc model {name}: {error}")


# =====================================================================
# 4. HAM DUNG CHUNG
# =====================================================================
def goto(page: Page, path: str, tries: int = 4) -> None:
    """Mo trang (path tuong doi tinh tu BASE_URL), thu lai khi demo tra loi 503."""
    url = path if path.startswith("http") else BASE_URL + path
    last = None
    for _ in range(tries):
        try:
            page.goto(url, wait_until="domcontentloaded")
            return
        except Exception as error:
            last = error
            time.sleep(15)
    raise AssertionError(f"Khong mo duoc {url}: {last}")


def login(page: Page) -> None:
    """Dang nhap admin/password, thu lai khi trang login chua san sang."""
    for _ in range(4):
        goto(page, "/login")
        if page.locator('input[name="username"]').count():
            break
        time.sleep(15)
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.get_by_role("button", name="Login").click()
    page.wait_for_function("() => !location.pathname.startsWith('/login')")
    expect(page.get_by_role("link", name="Admin Settings")).to_be_visible()


def unique_name(label: str) -> str:
    """Ten khong trung: G17_<nhan>_<so mili giay hien tai>."""
    return f"G17_{label}_{time.time_ns() // 1_000_000}"


def long_text(length: int) -> str:
    """Chuoi dung length ky tu, bat dau bang G17_ de de tim va don dep."""
    prefix = f"G17_{time.time_ns() // 1_000_000}_"
    return prefix + "A" * (length - len(prefix))


def success_alert(page: Page):
    return page.locator("div.alert.alert-success")


def error_alert(page: Page):
    return page.locator("div.alert.alert-danger")


def no_records(page: Page):
    return page.locator("tr.no-records-found")


def field_errors(page: Page) -> list[str]:
    """Cac cau loi hien thi tai tung truong va loi tong quat cua form."""
    return page.eval_on_selector_all(
        ".has-error .help-block, div.alert.alert-danger, span.alert-msg, .help-block.with-errors li",
        "els => els.map(e => e.innerText.trim()).filter(Boolean)",
    )


def html5_state(page: Page, selector: str) -> dict:
    """Trang thai kiem tra cua trinh duyet doi voi 1 truong (required/pattern)."""
    return page.locator(selector).evaluate(
        "e => ({message: e.validationMessage, valid: e.checkValidity()})"
    )


def pick_select2(page: Page, select_name: str, text: str | None = None) -> None:
    """Chon trong o Select2 tai du lieu qua API: mo o, (go tu khoa), bam ket qua."""
    page.locator(f"select[name='{select_name}'] + .select2").click()
    if text:
        page.locator(".select2-container--open .select2-search__field").fill(text)
        option = page.locator(".select2-container--open .select2-results__option", has_text=text)
    else:
        option = page.locator(".select2-container--open .select2-results__option:not(.loading-results)")
    option.first.click()


def expand_optional_sections(page: Page) -> None:
    """Form Asset an 2 nhom truong sau the <legend>: Optional Information va
    Order Related Information. Phai mo ra truoc khi nhap Name/Purchase Cost."""
    for toggle, panel in (("#optional_info", "#optional_details"), ("#order_info", "#order_details")):
        if page.locator(toggle).count():
            if page.locator(panel).evaluate("e => getComputedStyle(e).display") == "none":
                page.locator(toggle).click()
                page.wait_for_timeout(300)


def save(page: Page) -> None:
    page.locator("#submit_button").click()


def create_model(page: Page, created_models: list, name: str, category: str = "Laptop",
                 manufacturer: str | None = None, **fields) -> str:
    """Tao Asset Model va tra ve id. Ghi ten vao danh sach don dep TRUOC khi bam Save."""
    created_models.append(name)
    goto(page, "/models/create")
    page.locator("#name").fill(name)
    pick_select2(page, "category_id", category)
    if manufacturer:
        pick_select2(page, "manufacturer_id", manufacturer)
    for field_id, value in fields.items():
        page.locator(f"#{field_id}").fill(str(value))
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_MODEL_CREATED)
    return model_id_by_name(page, name)


def model_id_by_name(page: Page, name: str) -> str:
    goto(page, f"/models?search={name}")
    row = page.locator("table tbody tr", has_text=name).first
    row.wait_for()
    href = row.locator(f"a[href*='/models/']", has_text=name).first.get_attribute("href")
    return re.search(r"/models/(\d+)", href).group(1)


def fill_asset_form(page: Page, tag: str | None, model: str, status: str = "Ready to Deploy",
                    **fields) -> None:
    """Dien form Create/Edit Asset. fields: {"#name": "...", "#serial_1": "..."}"""
    if tag is not None:
        page.locator('input[name="asset_tags[1]"]').fill(tag)
    if model:
        pick_select2(page, "model_id", model)
    if status:
        page.locator('select[name="status_id"]').select_option(label=status)
    if fields:
        expand_optional_sections(page)
    for selector, value in fields.items():
        page.locator(selector).fill(str(value))


def create_asset(page: Page, created_assets: list, tag: str, model: str, **fields) -> str:
    """Tao tai san va tra ve id. Ghi tag vao danh sach don dep TRUOC khi bam Save."""
    created_assets.append(tag)
    goto(page, "/hardware/create")
    fill_asset_form(page, tag, model, **fields)
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_ASSET_CREATED)
    href = success_alert(page).locator('a[href*="/hardware/"]').first.get_attribute("href")
    return re.search(r"/hardware/(\d+)", href).group(1)


def delete_asset_by_tag(page: Page, tag: str) -> None:
    """Tim tai san theo Asset Tag roi xoa (toi da 3 lan, phong khi con ban sao)."""
    for _ in range(3):
        goto(page, f"/hardware?search={tag}")
        row = page.locator("table tbody tr", has_text=tag).first
        if row.count() == 0:
            return
        row.locator(".delete-asset").first.click()
        page.locator("#dataConfirmModal").get_by_role("button", name="Yes").click()
        page.wait_for_timeout(500)


def delete_model_by_name(page: Page, name: str) -> None:
    """Tim Asset Model theo ten roi xoa (model con tai san se khong xoa duoc)."""
    for _ in range(3):
        goto(page, f"/models?search={name}")
        row = page.locator("table tbody tr", has_text=name).first
        if row.count() == 0:
            return
        row.locator(".delete-asset").first.click()
        page.locator("#dataConfirmModal").get_by_role("button", name="Yes").click()
        page.wait_for_timeout(500)


def checkout_asset(page: Page, asset_id: str, user: str = "admin") -> None:
    """Cap phat tai san cho User qua trang /hardware/{id}/checkout."""
    goto(page, f"/hardware/{asset_id}/checkout")
    page.locator("label", has_text="User").first.click()
    pick_select2(page, "assigned_user", user)
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_CHECKOUT_OK)


def checkin_asset(page: Page, asset_id: str) -> None:
    """Thu hoi tai san qua trang /hardware/{id}/checkin."""
    goto(page, f"/hardware/{asset_id}/checkin")
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_CHECKIN_OK)


# =====================================================================
# 5. ASSETS - TEST CASE THEM MOI
# =====================================================================
def test_asset_05_default_values(page: Page):
    """[Asset-5] Gia tri mac dinh cua form Create New Asset."""
    goto(page, "/hardware/create")
    tag = page.locator('input[name="asset_tags[1]"]').input_value()
    assert tag.isdigit() and len(tag) >= 6, f"Asset Tag tu sinh phai la day so duy nhat: {tag!r}"
    expect(page.locator('select[name="status_id"]')).to_have_value("")
    expect(page.locator('select[name="model_id"]')).to_have_value("")
    expect(page.locator('input[name="checkout_to_type"][value="user"]')).to_be_checked()
    expect(page.locator('input[name="requestable"]')).not_to_be_checked()


def test_asset_06_edit_form_prefilled(page: Page, created_models, created_assets):
    """[Asset-6] Form Edit hien dung du lieu da luu."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Pre_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model, **{"#name": "G17 Prefilled", "#serial_1": "SN-PRE-1"})

    goto(page, f"/hardware/{asset_id}/edit")
    expand_optional_sections(page)
    expect(page.locator('input[name="asset_tags[1]"]')).to_have_value(tag)
    expect(page.locator("#name")).to_have_value("G17 Prefilled")
    expect(page.locator("#serial_1")).to_have_value("SN-PRE-1")
    expect(page.locator('select[name="status_id"]')).not_to_have_value("")


def test_asset_07_empty_asset_tag(page: Page, created_models):
    """[Asset-7] Bo trong truong bat buoc Asset Tag."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    goto(page, "/hardware/create")
    fill_asset_form(page, "", model)
    save(page)
    state = html5_state(page, 'input[name="asset_tags[1]"]')
    assert not state["valid"] and MSG_REQUIRED_HTML in state["message"], state
    assert page.url.endswith("/hardware/create"), "Khong duoc tao tai san khi thieu Asset Tag"


def test_asset_08_duplicate_asset_tag(page: Page, created_models, created_assets):
    """[Asset-8] Them moi trung Asset Tag."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Dup_{time.time_ns() // 1_000_000}"
    create_asset(page, created_assets, tag, model)

    goto(page, "/hardware/create")
    fill_asset_form(page, tag, model)
    save(page)

    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    assert any(MSG_TAG_UNIQUE in text for text in field_errors(page)), field_errors(page)
    assert page.url.endswith("/hardware/create"), "Khong duoc tao ban ghi trung Asset Tag"
    goto(page, f"/hardware?search={tag}")
    expect(page.locator("table tbody tr", has_text=tag)).to_have_count(1)


def test_asset_09_asset_tag_boundary_191_192(page: Page, created_models, created_assets):
    """[Asset-9] Asset Tag o gia tri bien 191 va 192 ky tu.
    Ky vong cua test case: 191 ky tu luu duoc, 192 ky tu bi chan."""
    model = unique_name("Model")
    create_model(page, created_models, model)

    tag191 = long_text(191)
    create_asset(page, created_assets, tag191, model)
    goto(page, f"/hardware?search={tag191}")
    expect(page.locator("table tbody tr", has_text=tag191)).to_have_count(1)

    tag192 = long_text(191) + "B"
    created_assets.append(tag192)
    goto(page, "/hardware/create")
    fill_asset_form(page, tag192, model)
    save(page)
    page.wait_for_timeout(2_000)
    if success_alert(page).count():
        pytest.xfail("BUG #G17-BUG-02: Asset Tag 192 ky tu van duoc luu (gioi han CSDL 191 khong duoc kiem tra)")


def test_asset_10_name_max_length_and_html(page: Page, created_models, created_assets):
    """[Asset-10] Asset Name gioi han 191 ky tu va hien thi HTML nguyen van."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    goto(page, "/hardware/create")
    expand_optional_sections(page)
    assert page.locator("#name").get_attribute("maxlength") == "191"

    payload = f"G17_<script>alert({time.time_ns() // 1_000_000})</script>"
    tag = f"G17-Xss_{time.time_ns() // 1_000_000}"
    created_assets.append(tag)
    fill_asset_form(page, tag, model, **{"#name": payload})
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_ASSET_CREATED)
    href = success_alert(page).locator('a[href*="/hardware/"]').first.get_attribute("href")
    asset_id = re.search(r"/hardware/(\d+)", href).group(1)

    goto(page, f"/hardware/{asset_id}")
    assert payload in page.locator("body").inner_text(), "Chuoi HTML phai hien thi nguyen van, khong thuc thi"


def test_asset_11_empty_model(page: Page):
    """[Asset-11] Bo trong truong bat buoc Model."""
    goto(page, "/hardware/create")
    tag = f"G17-NoModel_{time.time_ns() // 1_000_000}"
    fill_asset_form(page, tag, model="")
    save(page)
    state = html5_state(page, 'select[name="model_id"]')
    assert not state["valid"] and MSG_SELECT_HTML in state["message"], state
    assert page.url.endswith("/hardware/create"), "Khong duoc tao tai san khi thieu Model"


def test_asset_12_empty_status(page: Page, created_models):
    """[Asset-12] Bo trong truong bat buoc Status."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    goto(page, "/hardware/create")
    tag = f"G17-NoStatus_{time.time_ns() // 1_000_000}"
    fill_asset_form(page, tag, model, status="")
    save(page)
    state = html5_state(page, 'select[name="status_id"]')
    assert not state["valid"] and MSG_SELECT_HTML in state["message"], state
    assert page.url.endswith("/hardware/create"), "Khong duoc tao tai san khi thieu Status"


def test_asset_13_serial_max_length(page: Page, created_models, created_assets):
    """[Asset-13] Serial o gia tri bien 191 ky tu."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    serial = long_text(191)
    tag = f"G17-Serial_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model, **{"#serial_1": serial})

    goto(page, f"/hardware/{asset_id}")
    assert serial in page.locator("body").inner_text(), "Serial 191 ky tu phai hien thi du"


def test_asset_14_purchase_cost_invalid(page: Page, created_models):
    """[Asset-14] Purchase Cost: so am va chu bi chan, so thap phan hop le."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    goto(page, "/hardware/create")
    expand_optional_sections(page)

    for bad in ("-100", "abc"):
        page.locator("#purchase_cost").fill(bad)
        state = html5_state(page, "#purchase_cost")
        assert not state["valid"], f"Purchase Cost {bad!r} phai bi chan: {state}"

    page.locator("#purchase_cost").fill("1999.99")
    assert html5_state(page, "#purchase_cost")["valid"], "So thap phan hop le phai duoc chap nhan"


def test_asset_15_purchase_date_invalid(page: Page, created_models, created_assets):
    """[Asset-15] Purchase Date khong ton tai (30/02) va sai dinh dang."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Date_{time.time_ns() // 1_000_000}"
    created_assets.append(tag)

    goto(page, "/hardware/create")
    fill_asset_form(page, tag, model, **{"#purchase_date": "30/02/2026"})
    save(page)
    page.wait_for_timeout(2_000)

    assert page.url.endswith("/hardware/create"), "Ngay khong ton tai khong duoc tao tai san"
    messages = " ".join(field_errors(page))
    assert re.search(r"date|ngay|valid", messages, re.I), f"Phai co thong bao ngay khong hop le: {messages!r}"


def test_asset_16_warranty_boundary(page: Page, created_models):
    """[Asset-16] Warranty gioi han 3 ky tu, so am bi chan."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    goto(page, "/hardware/create")
    expand_optional_sections(page)

    assert page.locator("#warranty_months").get_attribute("maxlength") == "3"
    page.locator("#warranty_months").fill("999")
    page.locator("#warranty_months").press_sequentially("9")
    expect(page.locator("#warranty_months")).to_have_value("999")  # ky tu thu 4 bi chan

    page.locator("#warranty_months").fill("-5")
    state = html5_state(page, "#warranty_months")
    assert not state["valid"], f"So am phai bi chan: {state}"


def test_asset_17_notes_xss(page: Page, created_models, created_assets):
    """[Asset-17] Notes chua ma script (kiem tra XSS)."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    payload = f"<script>alert({time.time_ns() // 1_000_000})</script>"
    tag = f"G17-Note_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model, **{"#notes": payload})

    goto(page, f"/hardware/{asset_id}")
    assert payload in page.locator("body").inner_text(), "Notes phai hien thi nguyen van chuoi script"


def test_asset_18_create_required_only(page: Page, created_models, created_assets):
    """[Asset-18] Them moi tai san chi voi cac truong bat buoc."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Min_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}")
    body = page.locator("body").inner_text()
    assert tag in body and "Ready to Deploy" in body
    goto(page, f"/hardware?search={tag}")
    row = page.locator("table tbody tr", has_text=tag).first
    expect(row).to_be_visible()
    expect(row).to_contain_text("Ready to Deploy")


def test_asset_19_create_full_info(page: Page, created_models, created_assets):
    """[Asset-19] Them moi tai san voi day du thong tin hop le.
    Kiem tra bang cach mo lai form sua va doi chieu tung truong da luu."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Full_{time.time_ns() // 1_000_000}"
    data = {
        "#name": "G17 Laptop Full",
        "#serial_1": "SN-FULL-001",
        "#purchase_cost": "1999.99",
        "#notes": "Ghi chu kiem thu nhom 17",
        "#order_number": "PO-17-001",
    }
    asset_id = create_asset(page, created_assets, tag, model, **data)

    goto(page, f"/hardware/{asset_id}/edit")
    expand_optional_sections(page)
    expect(page.locator('input[name="asset_tags[1]"]')).to_have_value(tag)
    for selector, value in data.items():
        expect(page.locator(selector)).to_have_value(value)


def test_asset_21_cancel_create(page: Page, created_models):
    """[Asset-21] Huy khi dang nhap du lieu tao moi."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Cancel_{time.time_ns() // 1_000_000}"

    goto(page, "/hardware")
    goto(page, "/hardware/create")
    fill_asset_form(page, tag, model, **{"#name": "G17 Cancel"})
    page.get_by_role("link", name="Cancel").first.click()
    page.wait_for_url(re.compile(r"/hardware$"))
    goto(page, f"/hardware?search={tag}")
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


# =====================================================================
# 6. ASSETS - TEST CASE SUA
# =====================================================================
def test_asset_22_edit_valid(page: Page, created_models, created_assets):
    """[Asset-22] Cap nhat thong tin tai san voi du lieu hop le + History."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Edit_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model, **{"#name": "G17 Laptop"})

    goto(page, f"/hardware/{asset_id}/edit")
    expand_optional_sections(page)
    page.locator("#name").fill("G17 Laptop Edited")
    page.locator("#purchase_cost").fill("1999.99")
    page.locator("#notes").fill("G17 edited")
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_ASSET_UPDATED)

    goto(page, f"/hardware/{asset_id}/edit")
    expand_optional_sections(page)
    expect(page.locator("#name")).to_have_value("G17 Laptop Edited")
    expect(page.locator("#purchase_cost")).to_have_value("1999.99")
    expect(page.locator("#notes")).to_have_value("G17 edited")

    goto(page, f"/hardware/{asset_id}")
    history = page.locator("#history, table", has_text="update").first
    expect(history).to_contain_text(re.compile("update", re.I))


def test_asset_23_edit_duplicate_tag(page: Page, created_models, created_assets):
    """[Asset-23] Sua Asset Tag thanh gia tri da ton tai."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    first = f"G17-TagA_{time.time_ns() // 1_000_000}"
    create_asset(page, created_assets, first, model)
    second = f"G17-TagB_{time.time_ns() // 1_000_000}"
    second_id = create_asset(page, created_assets, second, model)

    goto(page, f"/hardware/{second_id}/edit")
    page.locator('input[name="asset_tags[1]"]').fill(first)
    save(page)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    assert any(MSG_TAG_UNIQUE in text for text in field_errors(page)), field_errors(page)

    goto(page, f"/hardware?search={second}")
    expect(page.locator("table tbody tr", has_text=second)).to_have_count(1)


def test_asset_24_edit_clear_model(page: Page, created_models, created_assets):
    """[Asset-24] Xoa trang truong bat buoc Model khi sua."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Clear_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}/edit")
    page.locator('select[name="model_id"]').evaluate("e => { e.value = ''; }")
    save(page)
    state = html5_state(page, 'select[name="model_id"]')
    assert not state["valid"], f"Model rong phai bi chan: {state}"
    assert re.search(rf"/hardware/{asset_id}/edit", page.url), "Van o lai form sua"


def test_asset_25_cancel_edit(page: Page, created_models, created_assets):
    """[Asset-25] Huy thay doi khi dang sua."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-CancelEdit_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model, **{"#name": "G17 Before"})

    goto(page, f"/hardware/{asset_id}/edit")
    expand_optional_sections(page)
    page.locator("#name").fill("G17 After Cancel")
    page.get_by_role("link", name="Cancel").first.click()
    page.wait_for_timeout(1_500)

    goto(page, f"/hardware/{asset_id}/edit")
    expand_optional_sections(page)
    expect(page.locator("#name")).to_have_value("G17 Before")


# =====================================================================
# 7. ASSETS - TEST CASE XOA
# =====================================================================
def test_asset_26_delete_unused(page: Page, created_models, created_assets):
    """[Asset-26] Xoa tai san chua duoc cap phat."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Del_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}")
    page.locator(".delete-asset").first.click()
    modal = page.locator("#dataConfirmModal")
    expect(modal).to_be_visible()
    expect(modal).to_contain_text(tag)
    modal.get_by_role("button", name="Yes").click()
    expect(success_alert(page)).to_contain_text(MSG_ASSET_DELETED)

    goto(page, f"/hardware?search={tag}")
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_asset_27_delete_deployed(page: Page, created_models, created_assets):
    """[Asset-27] Xoa tai san dang duoc cap phat cho User.
    Ky vong cua test case: he thong phai canh bao va khong cho xoa."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Deployed_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)
    checkout_asset(page, asset_id)

    goto(page, f"/hardware/{asset_id}")
    page.locator(".delete-asset").first.click()
    page.locator("#dataConfirmModal").get_by_role("button", name="Yes").click()
    page.wait_for_timeout(2_000)

    goto(page, f"/hardware?search={tag}")
    still_there = page.locator("table tbody tr", has_text=tag).count()
    if not still_there:
        pytest.xfail("BUG #G17-BUG-01: xoa duoc tai san dang cap phat, khong canh bao nhu ky vong")


def test_asset_28_cancel_delete(page: Page, created_models, created_assets):
    """[Asset-28] Huy thao tac xoa."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Keep_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}")
    page.locator(".delete-asset").first.click()
    modal = page.locator("#dataConfirmModal")
    expect(modal).to_be_visible()
    modal.get_by_role("button", name="Cancel").click()
    page.wait_for_timeout(800)
    expect(modal).not_to_be_visible()

    goto(page, f"/hardware?search={tag}")
    expect(page.locator("table tbody tr", has_text=tag)).to_have_count(1)


# =====================================================================
# 8. ASSETS - DANH SACH VA TIM KIEM
# =====================================================================
def test_asset_29_search_by_tag(page: Page, created_models, created_assets):
    """[Asset-29] Tim kiem tai san theo Asset Tag (co ket qua / khong co ket qua)."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    token = f"G17-Search{time.time_ns() // 1_000_000}"
    first, second = f"{token}_01", f"{token}_02"
    create_asset(page, created_assets, first, model)
    create_asset(page, created_assets, second, model)

    goto(page, f"/hardware?search={token}")
    expect(page.get_by_role("row").filter(has_text=token)).to_have_count(2)

    goto(page, f"/hardware?search={first}")
    expect(page.get_by_role("row").filter(has_text=first)).to_have_count(1)

    goto(page, f"/hardware?search={token}KhongTonTai")
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_asset_30_filter_sort_paging(page: Page):
    """[Asset-30] Loc theo Status, sap xep theo Asset Tag va phan trang."""
    goto(page, "/hardware?status=Ready%20to%20Deploy")
    page.wait_for_timeout(2_000)
    statuses = page.locator("table tbody tr td:nth-child(8)").all_inner_texts()
    if statuses:
        assert all("Ready to Deploy" in s for s in statuses), statuses[:5]

    goto(page, "/hardware")
    page.wait_for_timeout(2_000)
    info = page.locator(".pagination-info").first.inner_text()
    assert re.search(r"Showing 1 to \d+ of", info), info
    page.locator(".page-list").first.get_by_role("button").click()
    page.locator(".page-list").first.get_by_text("50", exact=True).click()
    page.wait_for_timeout(1_500)
    assert "Showing 1 to 50 of" in page.locator(".pagination-info").first.inner_text()


# =====================================================================
# 9. CHECKOUT / CHECKIN
# =====================================================================
def test_checkout_01_checkout_to_user(page: Page, created_models, created_assets):
    """[Checkout-1] Cap phat tai san cho User."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Co_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    checkout_asset(page, asset_id, "admin")
    goto(page, f"/hardware/{asset_id}")
    body = page.locator("body").inner_text()
    assert "User Admin" in body and "Deployed" in body


def test_checkout_02_checkout_without_user(page: Page, created_models, created_assets):
    """[Checkout-2] Cap phat nhung khong chon User."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-NoUser_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}/checkout")
    page.locator("label", has_text="User").first.click()
    save(page)
    state = html5_state(page, 'select[name="assigned_user"]')
    assert not state["valid"], f"Phai bat buoc chon User: {state}"
    assert f"/hardware/{asset_id}/checkout" in page.url


def test_checkout_03_checkout_to_location(page: Page, created_models, created_assets):
    """[Checkout-3] Cap phat tai san cho Location."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Loc_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}/checkout")
    page.locator("label", has_text="Location").first.click()
    pick_select2(page, "assigned_location", "East Elvera")
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_CHECKOUT_OK)

    goto(page, f"/hardware/{asset_id}")
    assert "East Elvera" in page.locator("body").inner_text()


def test_checkout_04_checkin(page: Page, created_models, created_assets):
    """[Checkout-4] Thu hoi tai san da cap phat."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Ci_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)
    checkout_asset(page, asset_id)

    checkin_asset(page, asset_id)
    goto(page, f"/hardware/{asset_id}")
    body = page.locator("body").inner_text()
    assert "Ready to Deploy" in body, "Sau checkin tai san phai ve Ready to Deploy"


def test_checkout_05_checkout_deployed_asset(page: Page, created_models, created_assets):
    """[Checkout-5] Cap phat lai tai san dang duoc cap phat (phai bi chan)."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-Twice_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)
    checkout_asset(page, asset_id)

    goto(page, f"/hardware/{asset_id}/checkout")
    if page.locator("#submit_button").count() == 0:
        return  # he thong khong cho mo form checkout lan 2
    save(page)
    page.wait_for_timeout(2_000)
    messages = " ".join(field_errors(page))
    assert error_alert(page).count() or messages, "Phai bao loi khi checkout tai san da cap phat"


def test_checkout_06_checkin_not_checked_out(page: Page, created_models, created_assets):
    """[Checkout-6] Thu hoi tai san chua duoc cap phat (phai bi chan)."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-NotCo_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware/{asset_id}/checkin")
    if page.locator("#submit_button").count() == 0:
        return  # he thong khong cho mo form checkin
    save(page)
    page.wait_for_timeout(2_000)
    assert error_alert(page).count(), "Phai bao loi khi checkin tai san chua cap phat"


def test_checkout_07_history_after_checkout(page: Page, created_models, created_assets):
    """[Checkout-7] Lich su tai san ghi nhan lan cap phat."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-His_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)
    checkout_asset(page, asset_id)

    goto(page, f"/hardware/{asset_id}")
    history = page.locator("table", has_text="checkout").first
    expect(history).to_contain_text(re.compile("checkout", re.I))
    expect(history).to_contain_text("User Admin")


def test_checkout_08_checkout_from_list(page: Page, created_models, created_assets):
    """[Checkout-8] Cap phat nhanh tu danh sach tai san."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    tag = f"G17-List_{time.time_ns() // 1_000_000}"
    asset_id = create_asset(page, created_assets, tag, model)

    goto(page, f"/hardware?search={tag}")
    row = page.locator("table tbody tr", has_text=tag).first
    row.get_by_role("link", name="Checkout").first.click()
    page.wait_for_url(re.compile(r"/checkout"))
    page.locator("label", has_text="User").first.click()
    pick_select2(page, "assigned_user", "admin")
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_CHECKOUT_OK)
    goto(page, f"/hardware?search={tag}")
    expect(page.locator("table tbody tr", has_text=tag).first).to_contain_text("User Admin")


def test_checkout_09_checkout_to_asset(page: Page, created_models, created_assets):
    """[Checkout-9] Cap phat tai san cho tai san khac (Checkout to Asset)."""
    model = unique_name("Model")
    create_model(page, created_models, model)
    parent_tag = f"G17-Parent_{time.time_ns() // 1_000_000}"
    parent_id = create_asset(page, created_assets, parent_tag, model)
    child_tag = f"G17-Child_{time.time_ns() // 1_000_000}"
    child_id = create_asset(page, created_assets, child_tag, model)

    goto(page, f"/hardware/{child_id}/checkout")
    page.locator("label", has_text="Asset").first.click()
    pick_select2(page, "assigned_asset", parent_tag)
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_CHECKOUT_OK)

    goto(page, f"/hardware/{child_id}")
    assert parent_tag in page.locator("body").inner_text()


# =====================================================================
# 10. ASSET MODELS
# =====================================================================
def test_model_01_create_required_only(page: Page, created_models):
    """[Model-1] Them moi mau tai san chi voi truong bat buoc."""
    name = unique_name("Basic")
    create_model(page, created_models, name)
    goto(page, f"/models?search={name}")
    expect(page.locator("table tbody tr", has_text=name)).to_have_count(1)


def test_model_02_create_full(page: Page, created_models):
    """[Model-2] Them moi mau tai san voi day du thong tin."""
    name = unique_name("Full")
    model_id = create_model(page, created_models, name, manufacturer="Dell",
                            model_number="MN-G17-02", min_amt=3, notes="Mau test nhom 17")
    goto(page, f"/models/{model_id}/edit")
    expect(page.locator("#name")).to_have_value(name)
    expect(page.locator("#model_number")).to_have_value("MN-G17-02")
    expect(page.locator("#min_amt")).to_have_value("3")
    expect(page.locator("#notes")).to_have_value("Mau test nhom 17")


def test_model_03_duplicate_name(page: Page, created_models):
    """[Model-3] Them moi trung ten mau tai san."""
    name = unique_name("Dup")
    create_model(page, created_models, name)
    goto(page, "/models/create")
    page.locator("#name").fill(name)
    pick_select2(page, "category_id", "Laptop")
    save(page)
    expect(error_alert(page)).to_contain_text(MSG_FORM_ERROR)
    assert any(MSG_MODEL_UNIQUE in text for text in field_errors(page)), field_errors(page)


def test_model_04_empty_name(page: Page):
    """[Model-4] Bo trong truong bat buoc Name."""
    goto(page, "/models/create")
    save(page)
    state = html5_state(page, "#name")
    assert not state["valid"] and MSG_REQUIRED_HTML in state["message"], state
    assert page.url.endswith("/models/create")


def test_model_05_edit_name(page: Page, created_models):
    """[Model-5] Sua ten mau tai san hop le."""
    name = unique_name("Edit")
    model_id = create_model(page, created_models, name)
    new_name = unique_name("Edited")
    created_models.append(new_name)

    goto(page, f"/models/{model_id}/edit")
    expect(page.locator("#name")).to_have_value(name)
    page.locator("#name").fill(new_name)
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_MODEL_UPDATED)

    goto(page, f"/models?search={new_name}")
    expect(page.locator("table tbody tr", has_text=new_name)).to_have_count(1)


def test_model_06_delete_unused(page: Page, created_models):
    """[Model-6] Xoa mau tai san chua duoc su dung."""
    name = unique_name("Del")
    model_id = create_model(page, created_models, name)
    goto(page, f"/models/{model_id}")
    page.locator(".delete-asset").first.click()
    page.locator("#dataConfirmModal").get_by_role("button", name="Yes").click()
    expect(success_alert(page)).to_contain_text(MSG_MODEL_DELETED)

    goto(page, f"/models?search={name}")
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_model_07_delete_used_by_asset(page: Page, created_models, created_assets):
    """[Model-7] Xoa mau tai san dang duoc tai san su dung (phai bi chan)."""
    name = unique_name("Used")
    model_id = create_model(page, created_models, name)
    create_asset(page, created_assets, f"G17-Use_{time.time_ns() // 1_000_000}", name)

    goto(page, f"/models/{model_id}")
    page.locator(".delete-asset").first.click()
    page.locator("#dataConfirmModal").get_by_role("button", name="Yes").click()
    expect(error_alert(page)).to_contain_text(MSG_MODEL_USED)

    goto(page, f"/models?search={name}")
    expect(page.locator("table tbody tr", has_text=name)).to_have_count(1)


def test_model_08_cancel_delete(page: Page, created_models):
    """[Model-8] Huy thao tac xoa mau tai san."""
    name = unique_name("Keep")
    model_id = create_model(page, created_models, name)
    goto(page, f"/models/{model_id}")
    page.locator(".delete-asset").first.click()
    modal = page.locator("#dataConfirmModal")
    expect(modal).to_be_visible()
    modal.get_by_role("button", name="Cancel").click()
    page.wait_for_timeout(800)
    expect(modal).not_to_be_visible()

    goto(page, f"/models?search={name}")
    expect(page.locator("table tbody tr", has_text=name)).to_have_count(1)


def test_model_09_search(page: Page, created_models):
    """[Model-9] Tim kiem mau tai san theo mot phan ten."""
    name = unique_name("Search")
    create_model(page, created_models, name)
    partial = name[len("G17_"):]
    goto(page, f"/models?search={partial}")
    expect(page.locator("table tbody tr", has_text=name)).to_have_count(1)
    goto(page, f"/models?search={unique_name('KhongTonTai')}")
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)


def test_model_10_require_serial(page: Page, created_models, created_assets):
    """[Model-10] Model bat buoc Serial thi khong tao duoc tai san thieu Serial."""
    name = unique_name("ReqSerial")
    created_models.append(name)
    goto(page, "/models/create")
    page.locator("#name").fill(name)
    pick_select2(page, "category_id", "Laptop")
    page.locator("#require_serial").check()
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_MODEL_CREATED)

    tag = f"G17-NoSer_{time.time_ns() // 1_000_000}"
    created_assets.append(tag)
    goto(page, "/hardware/create")
    fill_asset_form(page, tag, name)
    save(page)
    page.wait_for_timeout(2_000)
    messages = " ".join(field_errors(page))
    assert page.url.endswith("/hardware/create"), "Khong duoc tao tai san thieu Serial bat buoc"
    assert re.search(r"serial", messages, re.I), f"Phai bao loi Serial bat buoc: {messages!r}"


def test_model_11_upload_image(page: Page, created_models):
    """[Model-11] Tai anh hop le cho mau tai san."""
    name = unique_name("Image")
    created_models.append(name)
    goto(page, "/models/create")
    page.locator("#name").fill(name)
    pick_select2(page, "category_id", "Laptop")
    page.locator("#uploadFile").set_input_files(
        {"name": "g17.png", "mimeType": "image/png", "buffer": PNG_1PX}
    )
    expect(page.locator("#uploadFile-info")).to_contain_text("g17.png")
    save(page)
    expect(success_alert(page)).to_contain_text(MSG_MODEL_CREATED)


def test_model_12_cancel_create(page: Page):
    """[Model-12] Huy thao tac tao mau tai san."""
    name = unique_name("Cancel")
    goto(page, "/models")
    goto(page, "/models/create")
    page.locator("#name").fill(name)
    page.get_by_role("link", name="Cancel").first.click()
    page.wait_for_url(re.compile(r"/models$"))
    goto(page, f"/models?search={name}")
    expect(no_records(page)).to_contain_text(MSG_NO_RECORDS)
