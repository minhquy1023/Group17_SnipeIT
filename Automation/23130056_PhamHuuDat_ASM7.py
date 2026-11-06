"""
ASM7 - Automation script cho chuc nang ca nhan
Sinh vien : Pham Huu Dat - MSSV 23130056 (Nhom 17)
Website   : https://demo.snipeitapp.com  (Snipe-IT demo, tai khoan admin / password)
Cong cu   : Playwright (Python)
Chuc nang : 1) Licenses (20 TC)   2) Predefined Kits (20 TC)   3) Custom Fields (20 TC)
Test case : lay tu file Group17_23130056_Pham_Huu_Dat.xlsx (sheet ChucNang1, ChucNang2, ChucNang3)
Tong cong : 60 test case

Cai dat (1 lan):
    pip install playwright
    playwright install chromium

Chay:
    python 23130056_PhamHuuDat_ASM7.py                  # mo trinh duyet, chay cham de quay video
    python 23130056_PhamHuuDat_ASM7.py --headless       # chay an
    python 23130056_PhamHuuDat_ASM7.py --slow 700       # cham hon (ms moi thao tac)
    python 23130056_PhamHuuDat_ASM7.py --only License_  # chi chay cac TC co ID bat dau bang License_
    python 23130056_PhamHuuDat_ASM7.py --only Kit_005,Field_009

Ket qua: in bang PASS/FAIL/BLOCKED ra man hinh, anh chup luu trong thu muc screenshots/,
         ket qua chi tiet luu vao results.csv.

Ghi chu thiet ke:
 - Moi test tu tao du lieu tien dieu kien (license, kit, field, user, model...) voi ten
   duy nhat theo gio chay (RUN) de khong dung do voi du lieu cua nguoi khac tren demo dung chung.
 - Du lieu doc/kiem tra (tim ID, dem so seat...) lay qua endpoint /api/v1 cua chinh website
   (cung endpoint ma bang du lieu tren giao dien su dung, dung phien dang nhap san co).
 - PASS = hanh vi thuc te dung voi Expected Output. FAIL = website khac ky vong (la loi cua he thong
   hoac cua test design). BLOCKED = khong dung duoc tien dieu kien (vd khong tao duoc user).
"""
import argparse
import csv
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PWTimeout  # noqa: F401
from playwright.sync_api import sync_playwright

BASE_URL = "https://demo.snipeitapp.com"
USERNAME = "admin"
PASSWORD = "password"
NEW_USER_PASS = "Passw0rd!2026Xyz"
HERE = Path(__file__).parent
SHOT_DIR = HERE / "screenshots"

RUN = time.strftime("%H%M%S")
TODAY = time.strftime("%Y-%m-%d")

# ---- ten du lieu (duy nhat moi lan chay) ----
LIC = f"Samsung Knox Suite {RUN}"
LIC_KEY = f"KNOX-{RUN}-ABCDE-12345"
KIT = f"Onboarding Kit - Dev {RUN}"
KIT_QA = f"Onboarding Kit - QA {RUN}"
FIELD = f"Employee Badge {RUN}"
FIELD_ID = f"Employee Badge ID {RUN}"
FSET = f"Laptop Fieldset {RUN}"
MACBOOK = "Macbook Pro 13"          # asset model co san tren demo
BAD_NUMBERS = ["0", "-1", "1.5", "abc", "@#$"]

S = {}          # du lieu dung chung giua cac test
DIALOGS = []    # noi dung cac hop thoai alert/confirm cua trinh duyet
RESULTS = []    # (test_id, mo_ta, PASS/FAIL/BLOCKED, ghi_chu)


class Blocked(Exception):
    """Khong dung duoc tien dieu kien cua test case."""


# ================================================================ helpers
def goto(page, path):
    page.goto(path if path.startswith("http") else BASE_URL + path)
    page.wait_for_load_state("networkidle")


def login(page, user=USERNAME, pw=PASSWORD):
    page.goto(f"{BASE_URL}/login")
    page.fill("#username", user)
    page.fill("#password-field", pw)          # id thuc te cua o mat khau tren Snipe-IT
    page.locator("button[type=submit], input[type=submit]").first.click()
    page.wait_for_load_state("networkidle")
    assert "/login" not in page.url, f"Dang nhap that bai ({user})"


def pick(page, names, text=None, fallback_first=True):
    """Chon gia tri cho <select name=...> (select2 co ajax hoac select thuong). Tra ve text da chon."""
    for n in names:
        sel = page.locator(f"select[name='{n}']")
        if sel.count() == 0:
            continue
        box = sel.first.locator("xpath=following-sibling::span[contains(@class,'select2')]")
        if box.count() == 0:  # select thuong
            val = sel.first.evaluate(
                "(s,t)=>{const o=[...s.options].find(o=>o.value!==''&&(!t||o.text.includes(t)));return o?o.value:null}",
                text or "",
            )
            if val is None:
                raise Blocked(f"Khong co lua chon '{text}' trong {n}")
            sel.first.select_option(value=val, force=True)
            return text or val
        box.first.click()
        search = page.locator(".select2-search__field")
        if text and search.count():
            search.last.fill(text)
            page.wait_for_timeout(1500)
        opts = page.locator(".select2-results__option:not(.loading-results):not(.select2-results__message)")
        opt = opts.filter(has_text=text) if text else opts
        if opt.count() == 0 and fallback_first:
            if text and search.count():
                search.last.fill("")
                page.wait_for_timeout(1500)
            opt = opts
        if opt.count() == 0:
            page.keyboard.press("Escape")
            raise Blocked(f"Khong co lua chon '{text}' trong {n}")
        chosen = opt.first.inner_text().strip()
        opt.first.click()
        return chosen
    raise Blocked(f"Khong tim thay o chon {names}")


def set_raw(page, selector, value):
    """Gan gia tri tho vao input (ke ca input type=number) de test du lieu khong hop le."""
    page.evaluate(
        """([s, v]) => { const e = document.querySelector(s); e.type = 'text';
           e.removeAttribute('min'); e.removeAttribute('max'); e.removeAttribute('step');
           e.removeAttribute('required'); e.value = v; }""",
        [selector, value],
    )


def fill_force(page, selector, value):
    """Nhap gia tri vuot qua maxlength cua HTML de kiem tra validation that o server."""
    page.evaluate(
        """([s, v]) => { const e = document.querySelector(s);
           e.removeAttribute('maxlength'); e.value = v;
           e.dispatchEvent(new Event('input', {bubbles: true}));
           e.dispatchEvent(new Event('change', {bubbles: true})); }""",
        [selector, value],
    )


def click_save(page):
    # Modal cua kit dung #modal-save; uu tien no truoc vi trang nen cung co #submit_button.
    modal = page.locator("#modal-save")
    if modal.count() and modal.first.is_visible():
        modal.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        return
    btn = page.locator("#submit_button")
    if btn.count() and btn.first.is_visible():
        btn.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(600)
        return
    btn = page.get_by_role(
        "button", name=re.compile(r"^\s*(Save|Checkout|Checkin|Add|Create New)\b", re.I))
    if btn.count() == 0:
        btn = page.locator("button[type=submit], input[type=submit]")
    btn.first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(600)


def confirm_modal(page):
    """Bam xac nhan o hop thoai xoa (modal Snipe-IT hoac confirm cua trinh duyet)."""
    page.wait_for_timeout(900)
    for sel in ("#dataConfirmOK", ".modal.in .btn-danger", ".modal.show .btn-danger",
                "button:has-text('Yes')", "a:has-text('Yes')"):
        loc = page.locator(sel)
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            break
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)


def has_success(page):
    return page.locator(".alert-success").count() > 0


def has_error(page):
    if page.locator(".alert-danger, .alert-warning, .help-block, .alert-msg, .invalid-feedback").count() > 0:
        return True
    return page.locator("input:invalid, select:invalid, textarea:invalid").count() > 0


def rejected(page):
    """Form bi tu choi: khong co thong bao thanh cong va (co bao loi hoac van o form)."""
    if has_success(page):
        return False
    return has_error(page) or any(x in page.url for x in ("create", "edit", "checkout", "checkin"))


def body(page):
    return page.inner_text("body")


def table_search(page, text, index=0):
    boxes = page.locator(".fixed-table-toolbar .search input, input[type=search]")
    box = boxes.nth(index) if boxes.count() > index else boxes.first
    box.click()
    box.fill("")
    if text.strip() or text:
        box.press_sequentially(text, delay=40)
    page.wait_for_timeout(2200)


def table_links(page, pattern):
    """Tra ve text cac link trong bang khop regex href (vd r'/licenses/\\d+$')."""
    pairs = page.eval_on_selector_all(
        "table tbody tr td a",
        "els => els.map(e => [e.getAttribute('href') || '', e.innerText.trim()])",
    )
    return [t for h, t in pairs if re.search(pattern, h) and t]


def api(page, path):
    token = page.evaluate(
        "() => { const m = document.querySelector('meta[name=csrf-token]'); return m ? m.content : ''; }")
    res = page.evaluate(
        """async ([u, token]) => { try {
             const r = await fetch(u, {headers: {'Accept': 'application/json',
                 'X-Requested-With': 'XMLHttpRequest', 'X-CSRF-TOKEN': token},
                 credentials: 'same-origin'});
             const t = await r.text();
             try { return {status: r.status, json: JSON.parse(t)}; } catch (e) { return {status: r.status, json: null}; }
           } catch (e) { return {status: 0, json: null}; } }""",
        [f"/api/v1/{path}", token],
    )
    if res["status"] != 200 or res["json"] is None:
        raise Blocked(f"API /{path} tra ve {res['status']}")
    return res["json"]


def find_row(page, resource, value, key="name"):
    data = api(page, f"{resource}?search={quote(value)}&limit=100")
    for r in data.get("rows", []):
        if r.get(key) == value:
            return r
    return None


def shot(page, name):
    SHOT_DIR.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOT_DIR / f"{name}.png"), full_page=True)


def row_delete(page, list_path, text, search=True):
    """Vao danh sach, tim dong chua text, bam nut Delete va xac nhan."""
    goto(page, list_path)
    if search and page.locator(".fixed-table-toolbar .search input, input[type=search]").count():
        table_search(page, text)
    row = page.locator("tbody tr", has_text=text).first
    btn = row.locator(".delete-asset, a.btn-danger, button.btn-danger, a[data-tooltip='Delete']").first
    btn.click()
    confirm_modal(page)


def row_delete_blocked(page, list_path, text, search_index=0):
    """True neu dong bi chan xoa (khong co nut Delete hoac nut o trang thai disabled)."""
    goto(page, list_path)
    if page.locator(".fixed-table-toolbar .search input, input[type=search]").count() > search_index:
        table_search(page, text, index=search_index)
    row = page.locator("tbody tr", has_text=text).first
    if row.count() == 0:
        raise Blocked(f"Khong tim thay dong '{text}' trong danh sach")
    btn = row.locator(
        ".delete-asset, a.btn-danger, button.btn-danger, "
        "a[data-original-title='Delete'], button[data-original-title='Delete']").first
    if btn.count() == 0:
        return True
    if btn.is_disabled():
        return True
    if "disabled" in (btn.get_attribute("class") or "").lower():
        return True
    if btn.get_attribute("disabled") is not None:
        return True
    return False


def run_test(page, test_id, desc, fn):
    try:
        fn(page)
        RESULTS.append((test_id, desc, "PASS", ""))
        print(f"[PASS]    {test_id}: {desc}")
    except Blocked as e:
        RESULTS.append((test_id, desc, "BLOCKED", str(e)[:150]))
        print(f"[BLOCKED] {test_id}: {desc} -> {e}")
    except Exception as e:  # noqa: BLE001  (AssertionError, Timeout, loi selector...)
        msg = str(e).splitlines()[0][:150] if str(e) else type(e).__name__
        RESULTS.append((test_id, desc, "FAIL", msg))
        print(f"[FAIL]    {test_id}: {desc} -> {msg}")
    finally:
        try:
            shot(page, test_id)
        except Exception:  # noqa: BLE001
            pass


# ======================================================= du lieu tien dieu kien
def ensure_user(page, tag="a"):
    key = f"user_{tag}"
    if key in S:
        return S[key]
    first, last = "Nguyen", f"Van A {RUN}{tag}"
    uname = f"nva{RUN}{tag}"
    goto(page, "/users/create")
    page.fill("input[name=first_name]", first)
    page.fill("input[name=last_name]", last)
    # O username/password co readonly cho den khi focus; password chi hien khi da tick Activated.
    act = page.locator("input[name=activated]")
    if act.count() and not act.first.is_checked():
        act.first.check(force=True)
        page.wait_for_timeout(500)
    u = page.locator("#username")
    if u.count() == 0:
        u = page.locator("input[name=username]").first
    u.first.click()
    page.evaluate("() => { const e = document.querySelector('#username'); if (e) e.removeAttribute('readonly'); }")
    u.first.fill(uname)
    page.fill("#password", NEW_USER_PASS)
    page.fill("#password_confirm", NEW_USER_PASS)
    click_save(page)
    row = find_row(page, "users", uname, key="username")
    if not row:
        raise Blocked("Khong tao duoc user tien dieu kien (demo co the chan tao user)")
    S[key] = {"id": row["id"], "username": uname, "full": f"{first} {last}"}
    return S[key]


def fill_license(page, name, seats="5", key=None, vendor=False, **extra):
    page.fill("input[name=name]", name)
    pick(page, ["category_id"], "Software")
    if vendor:
        S["manu"] = pick(page, ["manufacturer_id"], "Samsung")
        try:
            S["supp"] = pick(page, ["supplier_id"], "Samsung")
        except Blocked:
            S["supp"] = None
    page.fill("input[name=seats]", str(seats))
    if key:
        page.fill("textarea[name=serial], input[name=serial]", key)   # Product Key la textarea
    for k, v in extra.items():
        page.fill(f"[name={k}]", v)
        if k.endswith("date"):
            page.keyboard.press("Escape")


def make_license(page, name, seats=5, key=None, **extra):
    goto(page, "/licenses/create")
    fill_license(page, name, seats, key, **extra)
    click_save(page)
    row = find_row(page, "licenses", name)
    if not row:
        raise Blocked(f"Khong tao duoc license tien dieu kien '{name}'")
    return row


def ensure_license(page):
    if "lic" not in S:
        goto(page, "/licenses/create")
        fill_license(page, LIC, 5, LIC_KEY, vendor=True)
        click_save(page)
        row = find_row(page, "licenses", LIC)
        if not row:
            raise Blocked("Khong tao duoc license co ban")
        S["lic"] = row
    return S["lic"]


def checkout_license(page, lic_id, user):
    goto(page, f"/licenses/{lic_id}/checkout")
    pick(page, ["assigned_user"], user["full"], fallback_first=False)
    click_save(page)
    return has_success(page)


def license_avail(page, name):
    row = find_row(page, "licenses", name)
    if not row or row.get("free_seats_count") is None:
        raise Blocked("API khong tra ve free_seats_count")
    return int(row["free_seats_count"])


def make_kit(page, name):
    goto(page, "/kits/create")
    page.fill("input[name=name]", name)
    click_save(page)
    row = find_row(page, "kits", name)
    if not row:
        raise Blocked(f"Khong tao duoc kit tien dieu kien '{name}'")
    return row


def kit_add(page, kid, kind, text=None, qty=None):
    """kind: model | license | accessory | consumable. Tra ve text muc da chon."""
    goto(page, f"/kits/{kid}")
    link = page.locator(f"a[href*='/modals/kit-{kind}/']").first
    if link.count() == 0:
        raise Blocked(f"Khong tim thay nut them {kind} vao kit")
    link.click()
    page.wait_for_timeout(1500)          # cho modal + select2 nap xong
    sel = page.locator(f"select[name='{kind}']")
    if sel.count() == 0:
        raise Blocked(f"Khong tim thay form them {kind} vao kit")
    chosen = pick(page, [kind], text)
    if qty is not None and page.locator("input[name=quantity]").count():
        page.fill("input[name=quantity]", str(qty))
    click_save(page)                      # #modal-save
    return chosen


def kit_checkout(page, kid, user):
    goto(page, f"/kits/{kid}/checkout")
    if user:
        pick(page, ["user_id"], user["full"], fallback_first=False)
    click_save(page)


def user_assets(page, uid):
    return api(page, f"users/{uid}/assets?limit=200").get("rows", [])


def make_model(page, name):
    goto(page, "/models/create")
    page.fill("input[name=name]", name)
    pick(page, ["category_id"], None)
    click_save(page)
    row = find_row(page, "models", name)
    if not row:
        raise Blocked(f"Khong tao duoc asset model '{name}'")
    return row


def make_field(page, name, element="text", fmt="ANY", values=None, encrypted=False):
    goto(page, "/fields/create")
    fill_field(page, name, element, fmt, values, encrypted)
    click_save(page)
    row = find_row(page, "fields", name)
    if not row:
        raise Blocked(f"Khong tao duoc custom field '{name}'")
    return row


def fill_field(page, name, element="text", fmt="ANY", values=None, encrypted=False, regex=None):
    page.fill("#name", name)               # input khong co thuoc tinh name
    page.select_option("select[name=element]", element)
    sel = page.locator("select[name=format]")
    try:
        sel.select_option(label=fmt)
    except Exception:  # noqa: BLE001
        sel.select_option(value=fmt)
    page.wait_for_timeout(400)
    if values is not None and page.locator("#field_values").count():
        page.fill("#field_values", values)
    if regex is not None:
        page.fill("#custom_format", regex)
    if encrypted:
        page.check("[name=field_encrypted]", force=True)


def ensure_field(page):
    if "field" not in S:
        S["field"] = find_row(page, "fields", FIELD) or make_field(page, FIELD)
    return S["field"]


def ensure_badge(page):
    """Field dung cho fieldset (ten 'Employee Badge ID')."""
    if "badge" not in S:
        S["badge"] = find_row(page, "fields", FIELD_ID) or make_field(page, FIELD_ID)
    return S["badge"]


def make_fieldset(page, name):
    goto(page, "/fields/fieldsets/create")
    page.fill("input[name=name]", name)
    click_save(page)                       # nut "Create New"
    row = find_row(page, "fieldsets", name)
    if not row:
        raise Blocked(f"Khong tao duoc fieldset '{name}'")
    return row


def ensure_fset(page):
    if "fset" not in S:
        S["fset"] = find_row(page, "fieldsets", FSET) or make_fieldset(page, FSET)
    return S["fset"]


def fieldset_add(page, fset_id, field_name, required=False):
    goto(page, f"/fields/fieldsets/{fset_id}")
    # Idempotent: field da co trong fieldset thi khong them lai (tranh loi trung).
    if page.locator("tbody tr", has_text=field_name).count():
        return
    sel = page.locator("select[name=field_id]")
    if sel.count() == 0:
        raise Blocked("Khong tim thay form them field vao fieldset")
    val = sel.first.evaluate(
        "(s,t)=>{const o=[...s.options].find(o=>o.text.trim()===t);return o?o.value:null}", field_name)
    if val is None:
        raise Blocked(f"Field '{field_name}' khong co trong danh sach them vao fieldset")
    sel.first.select_option(value=val, force=True)
    cb = page.locator("input[name=required]")
    if cb.count():
        cb.first.set_checked(required, force=True)
    page.locator("form:has(select[name=field_id]) button[type=submit]").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(600)


def ensure_cf_model(page):
    """Asset model rieng (khong dung model chung cua demo) de gan fieldset."""
    if "cfmodel" not in S:
        S["cfmodel"] = make_model(page, f"Model CF {RUN}")
    return S["cfmodel"]


def assign_fieldset_to_model(page, model_id, fset_name):
    goto(page, f"/models/{model_id}/edit")
    pick(page, ["fieldset_id"], fset_name, fallback_first=False)
    click_save(page)
    return has_success(page)


def asset_form(page, model_name):
    goto(page, "/hardware/create")
    pick(page, ["model_id"], model_name, fallback_first=False)
    pick(page, ["status_id"], "Ready to Deploy")
    page.wait_for_timeout(2500)  # cho form nap cac custom field (ajax)


def cf_input(page, field_name):
    return page.locator("#custom_fields_content .form-group", has_text=field_name) \
        .locator("input:not([type=hidden]), textarea, select").first


def setup_cf_chain(page):
    """Field(Required) -> Fieldset -> Asset Model; dung cho Field_015..020."""
    if S.get("cf_chain"):
        return
    badge, fset, model = ensure_badge(page), ensure_fset(page), ensure_cf_model(page)
    fieldset_add(page, fset["id"], badge["name"], required=True)
    if not assign_fieldset_to_model(page, model["id"], fset["name"]):
        raise Blocked("Khong gan duoc fieldset cho asset model")
    S["cf_chain"] = True


# ============================================================ 1) LICENSES
def license_001(page):
    """Them moi license voi day du thong tin hop le."""
    goto(page, "/licenses/create")
    fill_license(page, LIC, 5, LIC_KEY, vendor=True)
    click_save(page)
    assert has_success(page), "Khong thay thong bao tao license thanh cong"
    row = find_row(page, "licenses", LIC)
    assert row, "License vua tao khong ton tai"
    S["lic"] = row
    goto(page, "/licenses")
    table_search(page, LIC)
    assert LIC in table_links(page, r"/licenses/\d+$"), "License vua tao khong hien thi trong danh sach"


def license_002(page):
    """Bo trong Name, Category, Seats."""
    goto(page, "/licenses/create")
    page.fill("input[name=name]", "")
    page.fill("input[name=seats]", "")
    click_save(page)
    assert rejected(page), "He thong khong bao loi truong bat buoc / van tao license"


def license_003(page):
    """Seats = 0, am, thap phan, chu, ky tu dac biet -> bi chan."""
    for v in ["0", "-5", "2.5", "abc", "@#$"]:
        goto(page, "/licenses/create")
        fill_license(page, f"Seat Test {RUN}", "1")
        set_raw(page, "input[name=seats]", v)
        click_save(page)
        assert not has_success(page), f"He thong chap nhan Seats khong hop le: {v!r}"


def license_004(page):
    """Het seat -> nut checkout bi chan."""
    lic = make_license(page, f"Full Seat {RUN}", seats=1)
    user = ensure_user(page, "a")
    assert checkout_license(page, lic["id"], user), "Checkout seat duy nhat khong thanh cong"
    S["full_lic"] = lic
    goto(page, f"/licenses/{lic['id']}")
    # Chi xet nut checkout cua license nay (bo qua "Bulk Checkout" o menu).
    links = page.locator(f"a[href*='/licenses/{lic['id']}/checkout']")
    enabled = 0
    for i in range(links.count()):
        lk = links.nth(i)
        cls = (lk.get_attribute("class") or "").lower()
        if lk.is_visible() and "disabled" not in cls and lk.get_attribute("disabled") is None:
            enabled += 1
    assert enabled == 0, "Nut Checkout van bam duoc khi da het seat"


def license_005(page):
    """Nguoi duoc cap license co nut Checkin bam duoc, checkin xong seat tang 1."""
    lic = S.get("full_lic")
    if not lic:
        raise Blocked("Can License_004 chay truoc")
    user = ensure_user(page, "a")
    before = license_avail(page, lic["name"])
    goto(page, "/users")
    table_search(page, user["username"])
    page.locator("table tbody tr td a", has_text=user["full"]).first.click()
    page.wait_for_load_state("networkidle")
    tab = page.locator("a[href='#licenses']")
    if tab.count():
        tab.first.click()
        page.wait_for_timeout(2000)
    btn = page.locator("tr", has_text=lic["name"]).locator("a:has-text('Checkin'), button:has-text('Checkin')").first
    assert "disabled" not in (btn.get_attribute("class") or ""), "Nut Checkin khong bam duoc"
    btn.click()
    page.wait_for_load_state("networkidle")
    click_save(page)
    assert license_avail(page, lic["name"]) == before + 1, "So seat con lai khong tang 1 sau checkin"


def license_006(page):
    """Sua seats tu 10 xuong 5."""
    lic = make_license(page, f"Seat Edit {RUN}", seats=10)
    goto(page, f"/licenses/{lic['id']}/edit")
    page.fill("input[name=seats]", "5")
    click_save(page)
    assert has_success(page), "Khong thay thong bao cap nhat thanh cong"
    assert int(find_row(page, "licenses", lic["name"])["seats"]) == 5, "Seats khong ve 5"


def license_007(page):
    """Giam seats thap hon so seat da cap -> bao loi."""
    lic = make_license(page, f"Seat Low {RUN}", seats=2)
    user = ensure_user(page, "b")
    assert checkout_license(page, lic["id"], user), "Checkout lan 1 that bai"
    assert checkout_license(page, lic["id"], user), "Checkout lan 2 that bai"
    goto(page, f"/licenses/{lic['id']}/edit")
    page.fill("input[name=seats]", "1")
    click_save(page)
    assert not has_success(page) and has_error(page), "He thong cho giam seats thap hon so da cap"


def license_008(page):
    """Xoa user co license -> license duoc tra lai (+1 seat)."""
    lic = make_license(page, f"Del User Lic {RUN}", seats=3)
    user = ensure_user(page, "del")
    assert checkout_license(page, lic["id"], user), "Checkout license cho user that bai"
    before = license_avail(page, lic["name"])
    row_delete(page, "/users", user["username"])
    assert find_row(page, "users", user["username"], key="username") is None, "User chua bi xoa"
    assert license_avail(page, lic["name"]) == before + 1, "License khong duoc tra lai sau khi xoa user"


def license_009(page):
    """Them license voi ten da ton tai -> phai bao loi."""
    ensure_license(page)
    goto(page, "/licenses/create")
    fill_license(page, LIC, 5, f"KNOX-{RUN}-DUPNAME")
    click_save(page)
    assert rejected(page), "He thong cho phep tao license trung ten"


def license_010(page):
    """Them license voi Product Key da ton tai -> phai bao loi."""
    ensure_license(page)
    goto(page, "/licenses/create")
    fill_license(page, f"{LIC} B", 5, LIC_KEY)
    click_save(page)
    assert rejected(page), "He thong cho phep tao license trung Product Key"


def license_011(page):
    """Name qua dai / ky tu dac biet / chi khoang trang."""
    goto(page, "/licenses/create")
    fill_license(page, "tmp", 1)
    fill_force(page, "input[name=name]", "a" * 256)
    click_save(page)
    assert rejected(page), "Name 256 ky tu van duoc luu"
    goto(page, "/licenses/create")
    fill_license(page, f"@#$%^&*()_+ {RUN}", 1)
    click_save(page)
    assert has_success(page), "Name chua ky tu dac biet khong luu duoc"
    goto(page, "/licenses/create")
    fill_license(page, "     ", 1)
    click_save(page)
    assert rejected(page), "Name chi gom khoang trang van duoc luu"


def license_012(page):
    """Nhap script/HTML vao Name, Notes -> khong thuc thi."""
    DIALOGS.clear()
    goto(page, "/licenses/create")
    fill_license(page, "<script>alert('XSS')</script>" + RUN, 1,
                 notes="<b>test</b><img src=x onerror=alert(1)>")
    click_save(page)
    goto(page, "/licenses")
    table_search(page, RUN)
    row = find_row(page, "licenses", "<script>alert('XSS')</script>" + RUN)
    if row:
        goto(page, f"/licenses/{row['id']}")
    page.wait_for_timeout(2000)
    assert not any(m in ("XSS", "1") for m in DIALOGS), "Script duoc thuc thi (hop thoai alert xuat hien)"
    assert page.locator("img[src='x']").count() == 0, "The <img> trong Notes bi render thanh HTML"


def license_013(page):
    """Nhan Cancel -> khong luu du lieu."""
    name = f"Samsung Knox Test Cancel {RUN}"
    goto(page, "/licenses/create")
    fill_license(page, name, 5)
    page.get_by_role("link", name=re.compile("Cancel", re.I)).first.click()
    page.wait_for_load_state("networkidle")
    assert re.search(r"/licenses/?$", page.url), "Khong quay ve danh sach Licenses"
    assert find_row(page, "licenses", name) is None, "License van duoc luu sau khi Cancel"


def license_014(page):
    """Sua thong tin license hop le."""
    lic = make_license(page, f"{LIC} Edit", 5, f"KNOX-{RUN}-EDIT1")
    new_name = f"{lic['name']} (Updated)"
    goto(page, f"/licenses/{lic['id']}/edit")
    page.fill("input[name=name]", new_name)
    page.fill("input[name=license_name]", "Cong ty XYZ")
    page.fill("textarea[name=notes]", "Da cap nhat")
    click_save(page)
    assert has_success(page), "Khong thay thong bao cap nhat thanh cong"
    goto(page, f"/licenses/{lic['id']}")
    txt = body(page)
    assert new_name in txt and "Cong ty XYZ" in txt, "Thong tin moi khong hien thi dung"


def license_015(page):
    """Tang seats 10 -> 15 khi da cap 3 seat."""
    lic = make_license(page, f"Seat Up {RUN}", seats=10)
    user = ensure_user(page, "b")
    for _ in range(3):
        assert checkout_license(page, lic["id"], user), "Checkout seat that bai"
    goto(page, f"/licenses/{lic['id']}/edit")
    page.fill("input[name=seats]", "15")
    click_save(page)
    assert has_success(page), "Khong thay thong bao cap nhat thanh cong"
    row = find_row(page, "licenses", lic["name"])
    assert int(row["seats"]) == 15, "Seats khong tang len 15"
    assert int(row["free_seats_count"]) == 12, "Seat trong phai la 12 (15 - 3 da cap)"


def license_016(page):
    """Tim kiem theo ten (co / khong co ket qua)."""
    ensure_license(page)
    goto(page, "/licenses")
    table_search(page, "Samsung")
    names = table_links(page, r"/licenses/\d+$")
    assert names and all("samsung" in n.lower() for n in names), "Ket qua tim 'Samsung' khong dung"
    table_search(page, "zzzxyz123")
    assert not table_links(page, r"/licenses/\d+$"), "Van co ket qua cho tu khoa khong ton tai"
    assert re.search(r"No matching|no records|not found", body(page), re.I), "Khong co thong bao khong tim thay"


def license_017(page):
    """Tim kiem theo Product Key, Manufacturer, Supplier."""
    ensure_license(page)
    goto(page, "/licenses")
    table_search(page, LIC_KEY)
    assert LIC in table_links(page, r"/licenses/\d+$"), "Khong tim thay theo Product Key"
    if S.get("manu"):
        table_search(page, S["manu"])
        assert LIC in table_links(page, r"/licenses/\d+$"), "Khong tim thay theo Manufacturer"
    if S.get("supp"):
        table_search(page, S["supp"])
        assert LIC in table_links(page, r"/licenses/\d+$"), "Khong tim thay theo Supplier"


def license_018(page):
    """Tim kiem hoa/thuong, ky tu dac biet, khoang trang."""
    ensure_license(page)
    goto(page, "/licenses")
    table_search(page, "SAMSUNG")
    upper = set(table_links(page, r"/licenses/\d+$"))
    assert LIC in upper, "SAMSUNG (hoa) khong ra license"
    table_search(page, "samsung")
    assert set(table_links(page, r"/licenses/\d+$")) == upper, "Hoa/thuong cho ket qua khac nhau"
    table_search(page, "@#$%^&")
    assert page.locator("table").count() > 0 and "Error" not in body(page)[:300], "Ky tu dac biet gay loi"
    table_search(page, "     ")
    assert page.locator("table").count() > 0, "Khoang trang lam hong bang"


def license_019(page):
    """Loc theo Category, Manufacturer, het han (dung endpoint /api/v1/licenses cua bang)."""
    base = ensure_license(page)
    expired = make_license(page, f"Expired Lic {RUN}", 1, expiration_date="2020-01-01")
    cat, manu = (base.get("category") or {}).get("id"), (base.get("manufacturer") or {}).get("id")
    if not cat:
        raise Blocked("Khong lay duoc category cua license")
    rows = api(page, f"licenses?category_id={cat}&limit=200")["rows"]
    assert rows and all((r.get("category") or {}).get("id") == cat for r in rows), "Loc Category sai"
    assert LIC in [r["name"] for r in rows], "Loc Category thieu license mong doi"
    if manu:
        rows = api(page, f"licenses?category_id={cat}&manufacturer_id={manu}&limit=200")["rows"]
        assert all((r.get("manufacturer") or {}).get("id") == manu for r in rows), "Loc Manufacturer sai"
        assert LIC in [r["name"] for r in rows], "Loc Manufacturer thieu license mong doi"
    rows = api(page, f"licenses?category_id={cat}&limit=200")["rows"]
    exp = [r for r in rows if r["name"] == expired["name"]]
    assert exp and (exp[0].get("expiration_date") or {}).get("date", "9999") < TODAY, "License het han khong hien dung"


def license_020(page):
    """Ket hop tim kiem + sap xep."""
    ensure_license(page)
    if not find_row(page, "licenses", f"{LIC} Z"):
        make_license(page, f"{LIC} Z", 1)
    goto(page, "/licenses")
    table_search(page, "Samsung")
    hdr = page.locator("th[data-field='name'] .sortable, th:has-text('Name') .sortable").first
    hdr.click()
    page.wait_for_timeout(1800)
    asc = table_links(page, r"/licenses/\d+$")
    assert len(asc) >= 2 and asc == sorted(asc, key=str.lower), "Sap xep A-Z sai"
    hdr.click()
    page.wait_for_timeout(1800)
    desc = table_links(page, r"/licenses/\d+$")
    assert desc == sorted(desc, key=str.lower, reverse=True), "Sap xep Z-A sai"
    assert all("samsung" in n.lower() for n in desc), "Sap xep lam mat dieu kien tim kiem"


# ============================================================ 2) PREDEFINED KITS
def kit_001(page):
    """Them kit voi ten hop le."""
    goto(page, "/kits/create")
    page.fill("input[name=name]", KIT)
    click_save(page)
    assert has_success(page), "Khong thay thong bao tao kit thanh cong"
    row = find_row(page, "kits", KIT)
    assert row, "Kit vua tao khong ton tai"
    S["kit"] = row
    goto(page, "/kits")
    assert KIT in body(page), "Kit vua tao khong hien thi trong danh sach"


def ensure_kit(page):
    if "kit" not in S:
        S["kit"] = find_row(page, "kits", KIT) or make_kit(page, KIT)
    return S["kit"]


def kit_002(page):
    """Name dai dung 255 ky tu -> chap nhan."""
    name = RUN + "a" * (255 - len(RUN))
    goto(page, "/kits/create")
    page.fill("input[name=name]", name)
    click_save(page)
    assert has_success(page), "Kit voi Name 255 ky tu khong tao duoc"
    assert find_row(page, "kits", name), "Kit 255 ky tu khong co trong danh sach"


def kit_003(page):
    """Bo trong Name."""
    goto(page, "/kits/create")
    page.fill("input[name=name]", "")
    click_save(page)
    assert rejected(page), "He thong van tao kit khi bo trong Name"


def kit_004(page):
    """Name 256 ky tu -> bao loi."""
    goto(page, "/kits/create")
    page.fill("input[name=name]", RUN + "b" * (256 - len(RUN)))
    click_save(page)
    assert rejected(page), "He thong chap nhan Name dai 256 ky tu"


def kit_005(page):
    """Ten kit da ton tai -> bao loi."""
    ensure_kit(page)
    goto(page, "/kits/create")
    page.fill("input[name=name]", KIT)
    click_save(page)
    assert rejected(page), "He thong cho phep tao kit trung ten"


def kit_006(page):
    """Them model voi quantity hop le."""
    kit = ensure_kit(page)
    chosen = kit_add(page, kit["id"], "model", MACBOOK, 1)
    assert has_success(page), "Khong thay thong bao them model thanh cong"
    goto(page, f"/kits/{kit['id']}")
    assert MACBOOK in body(page), "Model khong hien thi trong noi dung kit"
    S["kit_model"] = chosen


def kit_007(page):
    """Them license, accessory, consumable vao kit."""
    kit = make_kit(page, f"Kit Items {RUN}")
    S["kit_items"] = kit
    # Tao rieng 1 license con seat, tranh chon nham license da het cho cua nguoi khac tren demo dung chung
    lic = make_license(page, f"Kit7 Lic {RUN}", seats=3)
    for kind, qty in (("license", None), ("accessory", 1), ("consumable", 1)):
        chosen = kit_add(page, kit["id"], kind, lic["name"] if kind == "license" else None, qty)
        assert has_success(page), f"Them {kind} vao kit that bai"
        goto(page, f"/kits/{kit['id']}")
        assert chosen.split(" (")[0][:20] in body(page), f"{kind} khong hien thi trong noi dung kit"


def kit_008(page):
    """Quantity khong hop le (0, am, thap phan, chu, ky tu dac biet)."""
    kit = make_kit(page, f"Kit BadQty {RUN}")
    for v in BAD_NUMBERS:
        goto(page, f"/kits/{kit['id']}")
        if page.locator("select[name=model]").count() == 0:
            kit_add_open = page.locator(f"a[href*='/kits/{kit['id']}/model']")
            if kit_add_open.count():
                kit_add_open.first.click()
                page.wait_for_load_state("networkidle")
        pick(page, ["model"], MACBOOK)
        set_raw(page, "input[name=quantity]", v)
        click_save(page)
        assert not has_success(page), f"He thong chap nhan Quantity khong hop le: {v!r}"
    goto(page, f"/kits/{kit['id']}")
    assert MACBOOK not in body(page), "Model van duoc them vao kit voi Quantity sai"


def kit_009(page):
    """Them cung 1 model 2 lan vao cung kit."""
    kit = make_kit(page, f"Kit Dup Model {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    assert has_success(page), "Lan them dau khong thanh cong"
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    second_ok = has_success(page)  # doc ket qua NGAY, truoc khi chuyen trang
    goto(page, f"/kits/{kit['id']}")
    rows = page.locator("tr", has_text=MACBOOK).count()
    assert (not second_ok) or rows <= 1, "He thong tao dong model trung lap trong kit"


def kit_010(page):
    """Xoa 1 muc khoi kit, cac muc con lai giu nguyen."""
    kit = make_kit(page, f"Kit Remove Item {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    lic = make_license(page, f"Kit10 Lic {RUN}", seats=3)
    kit_add(page, kit["id"], "license", lic["name"])
    goto(page, f"/kits/{kit['id']}")
    row = page.locator("tr", has_text=MACBOOK).first
    row.locator(".delete-asset, a.btn-danger, button.btn-danger, a:has-text('Delete')").first.click()
    confirm_modal(page)
    goto(page, f"/kits/{kit['id']}")
    assert MACBOOK not in body(page), "Model van con trong kit sau khi xoa"
    assert page.locator("tr", has_text=re.compile(r"\S")).count() > 1, "Cac muc con lai bi mat"


def kit_011(page):
    """Sua ten kit hop le."""
    kit = make_kit(page, f"Kit Rename {RUN}")
    goto(page, f"/kits/{kit['id']}/edit")
    page.fill("input[name=name]", KIT_QA)
    click_save(page)
    assert has_success(page), "Khong thay thong bao cap nhat thanh cong"
    assert find_row(page, "kits", KIT_QA), "Ten moi khong co trong danh sach"
    assert find_row(page, "kits", kit["name"]) is None, "Ten cu van con"


def kit_012(page):
    """Sua ten kit trung ten kit khac."""
    ensure_kit(page)
    qa = find_row(page, "kits", KIT_QA) or make_kit(page, KIT_QA)
    goto(page, f"/kits/{qa['id']}/edit")
    page.fill("input[name=name]", KIT)
    click_save(page)
    assert rejected(page), "He thong cho phep doi ten kit trung ten kit khac"


def kit_013(page):
    """Xoa kit chua check-out."""
    name = f"Kit Test Delete {RUN}"
    make_kit(page, name)
    row_delete(page, "/kits", name)
    assert find_row(page, "kits", name) is None, "Kit van con sau khi xoa"


def kit_014(page):
    """Xoa kit da check-out -> tai san da cap cho user khong bi anh huong."""
    user = ensure_user(page, "k14")
    kit = make_kit(page, f"Kit Test Delete 2 {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    kit_checkout(page, kit["id"], user)
    assert has_success(page), "Check-out kit that bai (tien dieu kien)"
    before = len(user_assets(page, user["id"]))
    assert before >= 1, "User chua co tai san sau check-out"
    row_delete(page, "/kits", kit["name"])
    assert find_row(page, "kits", kit["name"]) is None, "Kit van con sau khi xoa"
    assert len(user_assets(page, user["id"])) == before, "Tai san cua user bi anh huong khi xoa kit"


def kit_015(page):
    """Check-out kit day du hang (model + license)."""
    user = ensure_user(page, "k15")
    kit = make_kit(page, f"Kit Full {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    lic = make_license(page, f"Kit15 Lic {RUN}", seats=3)
    kit_add(page, kit["id"], "license", lic["name"])
    kit_checkout(page, kit["id"], user)
    assert has_success(page), "Khong thay thong bao check-out kit thanh cong"
    assets = user_assets(page, user["id"])
    assert any(MACBOOK in (a.get("model") or {}).get("name", "") for a in assets), "User khong nhan duoc tai san"
    lic = api(page, f"users/{user['id']}/licenses")
    assert lic.get("total", len(lic.get("rows", []))) >= 1, "User khong nhan duoc license seat"


def kit_016(page):
    """Check-out kit co model Quantity = 2 -> cap du 2 tai san."""
    user = ensure_user(page, "k16")
    kit = make_kit(page, f"Kit Qty 2 {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 2)
    kit_checkout(page, kit["id"], user)
    assert has_success(page), "Check-out kit Quantity 2 khong thanh cong"
    n = sum(1 for a in user_assets(page, user["id"]) if MACBOOK in (a.get("model") or {}).get("name", ""))
    assert n == 2, f"User co {n} tai san, mong doi dung 2"


def kit_017(page):
    """Check-out kit khong chon User."""
    kit = ensure_kit(page)
    goto(page, f"/kits/{kit['id']}/checkout")
    click_save(page)
    assert rejected(page), "He thong cho check-out kit khi khong chon User"


def kit_018(page):
    """Mot muc thieu hang -> bao loi va rollback toan bo."""
    user = ensure_user(page, "k18")
    empty_model = make_model(page, f"Model Het Hang {RUN}")
    kit = make_kit(page, f"Kit Thieu Hang {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    kit_add(page, kit["id"], "model", empty_model["name"], 1)
    kit_checkout(page, kit["id"], user)
    assert not has_success(page) and has_error(page), "He thong khong bao loi thieu hang"
    assert len(user_assets(page, user["id"])) == 0, "Khong rollback: user van nhan tai san cua model con hang"


def kit_019(page):
    """License trong kit da het seat -> bao loi, khong cap muc nao."""
    holder = ensure_user(page, "k19h")
    user = ensure_user(page, "k19")
    lic = make_license(page, f"Kit Lic Full {RUN}", seats=1)
    assert checkout_license(page, lic["id"], holder), "Khong cap het seat license (tien dieu kien)"
    kit = make_kit(page, f"Kit License {RUN}")
    kit_add(page, kit["id"], "license", lic["name"])
    kit_checkout(page, kit["id"], user)
    assert not has_success(page) and has_error(page), "He thong khong bao loi license het seat"
    assert len(user_assets(page, user["id"])) == 0, "User da duoc cap muc khi license het seat"


def kit_020(page):
    """Ton kho giam dung sau khi check-out kit."""
    user = ensure_user(page, "k20")
    rows = api(page, f"models?search={quote(MACBOOK)}&limit=20")["rows"]
    model = rows[0] if rows else None
    if not model:
        raise Blocked("Khong tim thay asset model Macbook Pro 13")
    lic = make_license(page, f"Kit Stock Lic {RUN}", seats=5)
    kit = make_kit(page, f"Kit Stock {RUN}")
    kit_add(page, kit["id"], "model", MACBOOK, 1)
    kit_add(page, kit["id"], "license", lic["name"])

    def stock():
        return api(page, f"hardware?model_id={model['id']}&status=RTD&limit=1").get("total", 0)

    s_before, l_before = stock(), license_avail(page, lic["name"])
    kit_checkout(page, kit["id"], user)
    assert has_success(page), "Check-out kit that bai"
    assert stock() == s_before - 1, "Ton kho model khong giam dung bang Quantity"
    assert license_avail(page, lic["name"]) == l_before - 1, "Seat license khong giam 1"


# ============================================================ 3) CUSTOM FIELDS
def field_001(page):
    """Them field voi Name, Element, Format hop le."""
    goto(page, "/fields/create")
    fill_field(page, FIELD, "text", "ANY")
    click_save(page)
    assert has_success(page), "Khong thay thong bao tao field thanh cong"
    S["field"] = find_row(page, "fields", FIELD)
    assert S["field"], "Field vua tao khong ton tai"
    goto(page, "/fields")
    assert FIELD in body(page), "Field vua tao khong hien thi trong danh sach"


def field_002(page):
    """Tao field voi tung loai Element."""
    items = [("Field TextBox", "text"), ("Field Textarea", "textarea"), ("Field Listbox", "listbox"),
             ("Field Checkbox", "checkbox"), ("Field Radio", "radio")]
    for label, el in items:
        goto(page, "/fields/create")
        vals = "Option1\nOption2" if el in ("listbox", "radio") else None
        fill_field(page, f"{label} {RUN}", el, "ANY", vals)
        click_save(page)
        assert has_success(page), f"Tao field {el} that bai"
    goto(page, "/fields")
    txt = body(page)
    assert all(f"{label} {RUN}" in txt for label, _ in items), "Khong du 5 field trong danh sach"


def field_003(page):
    """Bo trong Name, Element, Format."""
    goto(page, "/fields/create")
    page.fill("#name", "")
    click_save(page)
    assert rejected(page), "He thong van tao field khi bo trong truong bat buoc"


def field_004(page):
    """Name 256 ky tu -> bao loi."""
    goto(page, "/fields/create")
    fill_field(page, "tmp", "text", "ANY")
    fill_force(page, "#name", RUN + "c" * (256 - len(RUN)))
    click_save(page)
    assert rejected(page), "He thong chap nhan Name dai 256 ky tu"


def field_005(page):
    """Name da ton tai -> bao loi."""
    ensure_field(page)
    goto(page, "/fields/create")
    fill_field(page, FIELD, "text", "ANY")
    click_save(page)
    assert rejected(page), "He thong cho phep tao field trung ten"


def field_006(page):
    """Listbox / Radio de trong Field values -> bao loi."""
    for el in ("listbox", "radio"):
        goto(page, "/fields/create")
        fill_field(page, f"Field List Empty {el} {RUN}", el, "ANY", "")
        click_save(page)
        assert rejected(page), f"He thong tao field {el} khi de trong Field values"


def field_007(page):
    """Custom regex khong hop le -> bao loi."""
    goto(page, "/fields/create")
    fill_field(page, f"Field Regex {RUN}", "text", "CUSTOM REGEX", regex="regex:/([a-z/")
    click_save(page)
    assert rejected(page), "He thong chap nhan bieu thuc regex khong hop le"


def field_008(page):
    """Sua ten field hop le."""
    field = ensure_field(page)
    goto(page, f"/fields/{field['id']}/edit")
    page.fill("input[name=name]", FIELD_ID)
    click_save(page)
    assert has_success(page), "Khong thay thong bao cap nhat thanh cong"
    S["badge"] = find_row(page, "fields", FIELD_ID)
    assert S["badge"], "Ten moi khong co trong danh sach"
    S.pop("field", None)


def field_009(page):
    """Xoa field dang gan vao fieldset -> bao loi."""
    badge, fset = ensure_badge(page), ensure_fset(page)
    fieldset_add(page, fset["id"], badge["name"], required=True)
    # Bang Custom Fields la bang thu 2 tren trang /fields (o tim kiem so 2).
    assert row_delete_blocked(page, "/fields", badge["name"], search_index=1), \
        "Field dang dung trong fieldset van co nut xoa bam duoc"
    assert find_row(page, "fields", badge["name"]), "Field dang dung trong fieldset van bi xoa"


def field_010(page):
    """Them fieldset voi ten hop le."""
    name = f"Fieldset Test {RUN}"
    goto(page, "/fields/fieldsets/create")
    page.fill("input[name=name]", name)
    click_save(page)                       # nut "Create New"
    assert has_success(page), "Khong thay thong bao tao fieldset thanh cong"
    S["fset10"] = find_row(page, "fieldsets", name)
    assert S["fset10"], "Fieldset khong ton tai"
    goto(page, "/fields/fieldsets")
    assert name in body(page), "Fieldset khong hien thi trong danh sach"


def field_011(page):
    """Fieldset bo trong Name."""
    goto(page, "/fields/fieldsets/create")
    page.fill("input[name=name]", "")
    click_save(page)
    assert rejected(page), "He thong van tao fieldset khi bo trong Name"


def field_012(page):
    """Fieldset trung ten."""
    ensure_fset(page)
    goto(page, "/fields/fieldsets/create")
    page.fill("input[name=name]", FSET)
    click_save(page)
    assert rejected(page), "He thong cho phep tao fieldset trung ten"


def field_013(page):
    """Them field vao fieldset voi Required / Optional."""
    fset, badge = ensure_fset(page), ensure_badge(page)
    tb = find_row(page, "fields", f"Field TextBox {RUN}") or make_field(page, f"Field TextBox {RUN}")
    S["textbox"] = tb
    fieldset_add(page, fset["id"], badge["name"], required=True)
    fieldset_add(page, fset["id"], tb["name"], required=False)
    goto(page, f"/fieldsets/{fset['id']}")
    r1, r2 = page.locator("tr", has_text=badge["name"]).first, page.locator("tr", has_text=tb["name"]).first
    assert r1.count() and r2.count(), "Field khong hien thi trong fieldset"
    req1 = r1.locator(".fa-check, .fa-check-circle").count() > 0 or "Required" in r1.inner_text()
    req2 = r2.locator(".fa-check, .fa-check-circle").count() > 0 or "Required" in r2.inner_text()
    assert req1 and not req2, "Trang thai Required/Optional khong dung"


def field_014(page):
    """Xoa field khoi fieldset (field van con trong danh sach)."""
    fset = ensure_fset(page)
    tb = S.get("textbox") or find_row(page, "fields", f"Field TextBox {RUN}") or make_field(page, f"Field TextBox {RUN}")
    goto(page, f"/fieldsets/{fset['id']}")
    if page.locator("tr", has_text=tb["name"]).count() == 0:
        fieldset_add(page, fset["id"], tb["name"])
        goto(page, f"/fieldsets/{fset['id']}")
    page.locator("tr", has_text=tb["name"]).first.locator(
        "a:has-text('Remove'), button:has-text('Remove'), .btn-danger").first.click()
    confirm_modal(page)
    goto(page, f"/fieldsets/{fset['id']}")
    assert page.locator("tr", has_text=tb["name"]).count() == 0, "Field van con trong fieldset"
    assert find_row(page, "fields", tb["name"]), "Field bi xoa khoi danh sach Custom Fields"


def field_015(page):
    """Gan fieldset cho Asset Model -> form tao Asset hien dung field."""
    badge, fset, model = ensure_badge(page), ensure_fset(page), ensure_cf_model(page)
    fieldset_add(page, fset["id"], badge["name"], required=True)
    assert assign_fieldset_to_model(page, model["id"], fset["name"]), "Gan fieldset cho model that bai"
    S["cf_chain"] = True
    asset_form(page, model["name"])
    inp = cf_input(page, badge["name"])
    assert inp.count() and inp.is_visible(), "Form tao Asset khong hien thi field cua fieldset"
    grp = page.locator("#custom_fields_content .form-group", has_text=badge["name"]).first
    assert inp.get_attribute("required") is not None or "required" in (grp.get_attribute("class") or "") \
        or "*" in grp.inner_text(), "Field khong duoc danh dau bat buoc"


def field_016(page):
    """Xoa fieldset dang gan cho Asset Model -> bao loi."""
    setup_cf_chain(page)
    fset = ensure_fset(page)
    row_delete(page, "/fields", fset["name"])
    assert find_row(page, "fieldsets", fset["name"]), "Fieldset dang duoc gan cho model van bi xoa"


def field_017(page):
    """Luu Asset voi gia tri hop le, trang chi tiet hien dung."""
    setup_cf_chain(page)
    model, badge = ensure_cf_model(page), ensure_badge(page)
    asset_form(page, model["name"])
    cf_input(page, badge["name"]).fill("EMP-001")
    click_save(page)
    assert has_success(page), "Khong thay thong bao tao asset thanh cong"
    assert "EMP-001" in body(page), "Trang chi tiet asset khong hien thi EMP-001"


def field_018(page):
    """Field Required de trong -> khong tao duoc Asset."""
    setup_cf_chain(page)
    model = ensure_cf_model(page)
    asset_form(page, model["name"])
    click_save(page)
    assert rejected(page), "He thong tao asset khi field Required de trong"


def field_019(page):
    """Gia tri sai Format (NUMERIC, EMAIL, IP, MAC, DATE)."""
    setup_cf_chain(page)
    fset, model, badge = ensure_fset(page), ensure_cf_model(page), ensure_badge(page)
    bad = [("NUMERIC", "abc"), ("EMAIL", "abc@"), ("IP", "999.1.1.1"), ("MAC", "ZZ:ZZ"), ("DATE", "32/13/2026")]
    names = []
    for fmt, _ in bad:
        row = find_row(page, "fields", f"Field {fmt} {RUN}") or make_field(page, f"Field {fmt} {RUN}", "text", fmt)
        fieldset_add(page, fset["id"], row["name"])
        names.append(row["name"])
    asset_form(page, model["name"])
    cf_input(page, badge["name"]).fill("EMP-002")
    for nm, (_, val) in zip(names, bad):
        cf_input(page, nm).fill(val)
    click_save(page)
    assert rejected(page) and has_error(page), "He thong chap nhan gia tri sai Format"


def field_020(page):
    """Field Encrypted: admin xem duoc, user thuong khong xem duoc."""
    setup_cf_chain(page)
    fset, model, badge = ensure_fset(page), ensure_cf_model(page), ensure_badge(page)
    secret = find_row(page, "fields", f"Secret Key {RUN}") or make_field(page, f"Secret Key {RUN}", encrypted=True)
    fieldset_add(page, fset["id"], secret["name"])
    asset_form(page, model["name"])
    cf_input(page, badge["name"]).fill("EMP-003")
    cf_input(page, secret["name"]).fill("abc123")
    click_save(page)
    assert has_success(page), "Tao asset co field Encrypted that bai"
    assert "abc123" in body(page), "Admin khong xem duoc gia tri Secret Key"
    asset_url = page.url
    user = ensure_user(page, "n")
    ctx = S["browser"].new_context(viewport={"width": 1366, "height": 800})
    try:
        p2 = ctx.new_page()
        try:
            login(p2, user["username"], NEW_USER_PASS)
        except AssertionError:
            raise Blocked("Khong dang nhap duoc bang user thuong")
        p2.goto(asset_url)
        p2.wait_for_load_state("networkidle")
        assert "abc123" not in p2.content(), "User thuong xem duoc gia tri da ma hoa"
    finally:
        ctx.close()


TESTS = [
    ("License_001", "Them moi license voi day du thong tin hop le", license_001),
    ("License_002", "Them moi license bo trong Name, Category, Seats", license_002),
    ("License_003", "Seats = 0, am, thap phan, chu, ky tu dac biet", license_003),
    ("License_004", "Checkout khi da het seat", license_004),
    ("License_005", "User vua duoc cap license co nut Checkin va checkin duoc", license_005),
    ("License_006", "Sua seats license (10 -> 5)", license_006),
    ("License_007", "Sua seats thap hon so seat da cap", license_007),
    ("License_008", "Xoa user co license -> license duoc tra lai", license_008),
    ("License_009", "Them license voi ten da ton tai", license_009),
    ("License_010", "Them license voi Product Key da ton tai", license_010),
    ("License_011", "Name vuot do dai / ky tu dac biet / chi khoang trang", license_011),
    ("License_012", "Nhap script/HTML vao Name, Notes", license_012),
    ("License_013", "Nhan Cancel khi dang nhap du lieu", license_013),
    ("License_014", "Sua thong tin license hop le", license_014),
    ("License_015", "Tang so luong Seats", license_015),
    ("License_016", "Tim kiem license theo ten", license_016),
    ("License_017", "Tim kiem theo Product Key, Manufacturer, Supplier", license_017),
    ("License_018", "Tim kiem voi ky tu dac biet, khoang trang, hoa/thuong", license_018),
    ("License_019", "Loc theo Category, Manufacturer, het han", license_019),
    ("License_020", "Ket hop tim kiem voi loc va sap xep", license_020),
    ("Kit_001", "Them moi kit voi ten hop le", kit_001),
    ("Kit_002", "Them kit voi ten dai 255 ky tu", kit_002),
    ("Kit_003", "Them kit bo trong Name", kit_003),
    ("Kit_004", "Them kit voi ten dai hon 255 ky tu", kit_004),
    ("Kit_005", "Them kit voi ten da ton tai", kit_005),
    ("Kit_006", "Them model vao kit voi so luong hop le", kit_006),
    ("Kit_007", "Them license, accessory, consumable vao kit", kit_007),
    ("Kit_008", "Them model voi so luong khong hop le", kit_008),
    ("Kit_009", "Them cung 1 model 2 lan vao 1 kit", kit_009),
    ("Kit_010", "Xoa 1 muc khoi kit", kit_010),
    ("Kit_011", "Sua ten kit hop le", kit_011),
    ("Kit_012", "Sua ten kit trung ten kit khac", kit_012),
    ("Kit_013", "Xoa kit chua check-out", kit_013),
    ("Kit_014", "Xoa kit da check-out, tai san user khong bi anh huong", kit_014),
    ("Kit_015", "Check-out kit day du hang", kit_015),
    ("Kit_016", "Check-out kit co model so luong 2", kit_016),
    ("Kit_017", "Check-out kit khi khong chon User", kit_017),
    ("Kit_018", "Check-out khi 1 muc thieu hang (rollback)", kit_018),
    ("Kit_019", "Check-out kit khi license het seat", kit_019),
    ("Kit_020", "Ton kho giam dung sau check-out kit", kit_020),
    ("Field_001", "Them field voi du lieu hop le", field_001),
    ("Field_002", "Them field voi tung loai Element", field_002),
    ("Field_003", "Them field bo trong truong bat buoc", field_003),
    ("Field_004", "Them field voi Name dai hon 255 ky tu", field_004),
    ("Field_005", "Them field voi Name da ton tai", field_005),
    ("Field_006", "Listbox/Radio de trong Field values", field_006),
    ("Field_007", "Custom regex khong hop le", field_007),
    ("Field_008", "Sua field hop le", field_008),
    ("Field_009", "Xoa field dang gan vao fieldset", field_009),
    ("Field_010", "Them fieldset ten hop le", field_010),
    ("Field_011", "Them fieldset bo trong Name", field_011),
    ("Field_012", "Them fieldset trung ten", field_012),
    ("Field_013", "Them field vao fieldset Required/Optional", field_013),
    ("Field_014", "Xoa field khoi fieldset", field_014),
    ("Field_015", "Gan fieldset cho Asset Model, form Asset hien dung field", field_015),
    ("Field_016", "Xoa fieldset dang gan cho Asset Model", field_016),
    ("Field_017", "Luu Asset voi gia tri field hop le", field_017),
    ("Field_018", "Field Required de trong khi luu Asset", field_018),
    ("Field_019", "Gia tri sai Format khi luu Asset", field_019),
    ("Field_020", "Field Encrypted: chi nguoi co quyen xem duoc", field_020),
]
assert len(TESTS) == 60, "Phai du 60 test case"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", help="chay an trinh duyet")
    ap.add_argument("--slow", type=int, default=300, help="do tre moi thao tac (ms) de quay video")
    ap.add_argument("--only", default="", help="chi chay cac test co ID bat dau bang (cach nhau dau phay)")
    args = ap.parse_args()
    prefixes = [p.strip() for p in args.only.split(",") if p.strip()]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless, slow_mo=args.slow)
        S["browser"] = browser
        context = browser.new_context(viewport={"width": 1366, "height": 800})
        context.set_default_timeout(20000)
        page = context.new_page()
        page.on("dialog", lambda d: (DIALOGS.append(d.message), d.accept()))

        login(page)
        for test_id, desc, fn in TESTS:
            if prefixes and not any(test_id.startswith(x) for x in prefixes):
                continue
            run_test(page, test_id, desc, fn)
        browser.close()

    with open(HERE / "results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Result", "Description", "Note"])
        for tid, desc, status, note in RESULTS:
            w.writerow([tid, status, desc, note])

    print("\n" + "=" * 78)
    print(f"{'ID':<13}{'KET QUA':<10}MO TA")
    for tid, desc, status, note in RESULTS:
        print(f"{tid:<13}{status:<10}{desc}" + (f"  ({note})" if note else ""))
    n_pass = sum(1 for r in RESULTS if r[2] == "PASS")
    n_fail = sum(1 for r in RESULTS if r[2] == "FAIL")
    n_blk = sum(1 for r in RESULTS if r[2] == "BLOCKED")
    print(f"\nTong: {len(RESULTS)} test | PASS {n_pass} | FAIL {n_fail} | BLOCKED {n_blk}")
    sys.exit(0 if n_fail == 0 and n_blk == 0 else 1)


if __name__ == "__main__":
    main()
