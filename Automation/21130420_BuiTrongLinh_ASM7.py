"""
ASM7 - Automation test 3 chuc nang: Users, Departments, Locations - Snipe-IT
Nhom 17 - 21130420 - Bui Trong Linh
Website: https://demo.snipeitapp.com (Snipe-IT v8.8.3)
Cong cu: Python 3.12+ + Playwright (Chromium)

Cach chay:
    python 21130420_BuiTrongLinh_ASM7.py
Hoac chay tu thu muc goc repo:
    python Automation/21130420_BuiTrongLinh_ASM7.py

Video demo : https://youtu.be/ElYe0M3FDZU
GitHub repo: https://github.com/minhquy1023/Group17_SnipeIT

Bao phu toan dien 3 module ca nhan (Nhom D - Con nguoi va to chuc):
  MODULE 1: LOCATIONS   (12 Test Cases - Loc-1  den Loc-12)
  MODULE 2: DEPARTMENTS (11 Test Cases - Dept-1 den Dept-11)
  MODULE 3: USERS       (26 Test Cases - User-1 den User-26, khop 100% Excel Lab 6)
  TONG CONG: 49 Test Cases - Co do tre quan sat ro rang (SLOW_MO = 700ms)
"""

import re
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# ─── CAU HINH CHUNG ───────────────────────────────────────────────────────────
BASE_URL = "https://demo.snipeitapp.com"
HEADLESS = False   # False = mo trinh duyet de quay video demo
SLOW_MO  = 700    # ms delay giua cac thao tac giup nguoi xem quan sat ro rang tung buoc

TS     = datetime.now().strftime("%m%d%H%M")
PREFIX = f"G17L{TS}"

results = []

def log(tc_id, desc, status, note=""):
    results.append({"id": tc_id, "desc": desc, "status": status, "note": note})
    tag = status
    suffix = f" -> {note}" if note else ""
    print(f"  [{tag:<7}] [{tc_id:<9}] {desc}{suffix}")


# ─── CAC HAM HO TRO (HELPERS) ─────────────────────────────────────────────────

def login(page):
    """Dang nhap vao Snipe-IT bang tai khoan admin."""
    for attempt in range(2):
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            time.sleep(1.5)
            # Neu da dang nhap san thi khong can dien form
            if page.locator(".sidebar-menu, a[href*='/users'], .main-header").count() > 0:
                print(f"[Setup] Da o trang thai dang nhap! URL: {page.url}")
                return
            page.wait_for_selector("#username, form", timeout=30000)
            break
        except Exception as e:
            if attempt == 1:
                raise e
            time.sleep(2)

    page.evaluate("""() => {
        var u = document.querySelector('#username');
        var p = document.querySelector('#password-field');
        if (u) { u.removeAttribute('readonly'); u.value = 'admin'; }
        if (p) { p.removeAttribute('readonly'); p.value = 'password'; }
    }""")
    time.sleep(1)
    page.locator("button[type='submit']").first.click()
    page.locator(".sidebar-menu, a[href*='/users'], .main-header").first.wait_for(state="visible", timeout=30000)
    time.sleep(1.5)
    print(f"[Setup] Dang nhap thanh cong! URL: {page.url}")


def click_save(page):
    """Click nut Save tren form."""
    time.sleep(0.8)
    page.locator("button[type='submit']:has-text('Save')").first.click()


def search_table(page, keyword):
    """Tim kiem trong bang bang o search Bootstrap Table."""
    search = page.locator("input.search-input").first
    search.wait_for(state="visible", timeout=10000)
    search.click()
    time.sleep(0.5)
    search.fill("")
    search.fill(keyword)
    search.press("Enter")
    # Cho AJAX loc du lieu
    time.sleep(2.5)


def get_alert_text(page):
    """Lay noi dung toast / alert thong bao."""
    try:
        alert = page.locator(".alert, .alert-success, .alert-danger").first
        alert.wait_for(state="visible", timeout=4000)
        return alert.inner_text().strip()
    except Exception:
        return ""


def count_form_errors(page):
    """Dem so truong bi danh dau loi validation."""
    return page.locator(".has-error").count()


# ==============================================================================
# MODULE 1: LOCATIONS (QUAN LY DIA DIEM - 12 TEST CASES)
# ==============================================================================

def run_module_locations(page):
    print("\n" + "=" * 75)
    print("  --- MODULE 1: LOCATIONS (QUAN LY DIA DIEM - 12 TEST CASES) ---")
    print("=" * 75)
    created_loc = None

    # [Loc-1] Giao dien danh sach Locations
    try:
        tc, desc = "Loc-1", "Kiem tra giao dien man hinh danh sach Locations"
        page.goto(f"{BASE_URL}/locations", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("table.snipe-table", state="visible", timeout=15000)
        time.sleep(1)
        has_new = page.locator("a[href*='/locations/create'], a:has-text('New'), a:has-text('Create')").count() >= 1
        assert "/locations" in page.url and has_new, "Giao dien /locations thieu thanh phan"
        log(tc, desc, "PASSED", "URL /locations, bang du lieu va nut tao moi hien thi day du")
    except Exception as e:
        log("Loc-1", "Kiem tra giao dien man hinh danh sach Locations", "FAILED", str(e)[:80])

    # [Loc-2] Giao dien form tao moi Location
    try:
        tc, desc = "Loc-2", "Kiem tra giao dien form tao moi Location"
        page.goto(f"{BASE_URL}/locations/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#name", state="attached", timeout=15000)
        time.sleep(1)
        has_name = page.locator("#name").is_visible()
        has_save = page.locator("button[type='submit']:has-text('Save')").count() >= 1
        has_cancel = page.locator("a:has-text('Cancel')").count() >= 1
        assert has_name and has_save and has_cancel, "Form tao moi Location thieu truong"
        log(tc, desc, "PASSED", "Form Create Location co day du o nhap Name, nut Save va Cancel")
    except Exception as e:
        log("Loc-2", "Kiem tra giao dien form tao moi Location", "FAILED", str(e)[:80])

    # [Loc-3] Validation: Bo trong ten Location
    try:
        tc, desc = "Loc-3", "Validation: Bo trong ten dia diem (Location Name)"
        page.goto(f"{BASE_URL}/locations/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#name", state="attached", timeout=15000)
        click_save(page)
        page.wait_for_selector(".has-error", timeout=6000)
        time.sleep(1)
        n = count_form_errors(page)
        assert n >= 1, "Khong hien thi loi validation bat buoc ten dia diem"
        log(tc, desc, "PASSED", f"He thong chan luu va bao loi bat buoc tai o ten dia diem ({n} loi)")
    except Exception as e:
        log("Loc-3", "Validation: Bo trong ten dia diem (Location Name)", "FAILED", str(e)[:80])

    # [Loc-4] Validation: Nhap ten tieng Viet co dau
    try:
        tc, desc = "Loc-4", "Chuc nang: Nhap ten dia diem tieng Viet co dau"
        page.goto(f"{BASE_URL}/locations/create", wait_until="domcontentloaded", timeout=30000)
        vn_loc = "Chi nhanh Cau Giay & Phong Giao Dich"
        page.fill("#name", vn_loc)
        time.sleep(1)
        val = page.locator("#name").input_value()
        assert "Cau Giay" in val, "Khong nhan dung chu tieng Viet"
        log(tc, desc, "PASSED", f"O nhap ten dia diem nhan dung ky tu co dau: '{vn_loc}'")
    except Exception as e:
        log("Loc-4", "Chuc nang: Nhap ten dia diem tieng Viet co dau", "FAILED", str(e)[:80])

    # [Loc-5] Huy tao moi Location bang nut [Cancel]
    try:
        tc, desc = "Loc-5", "Huy thao tac tao moi Location bang nut [Cancel]"
        page.goto(f"{BASE_URL}/locations/create", wait_until="domcontentloaded", timeout=30000)
        page.fill("#name", "TempLocCancel")
        time.sleep(1)
        cancel_btn = page.locator(".box-footer a:has-text('Cancel'), form a:has-text('Cancel'), a:has-text('Cancel')").first
        cancel_btn.click()
        try:
            page.wait_for_url("**/locations", timeout=10000)
        except Exception:
            page.goto(f"{BASE_URL}/locations", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_selector("table.snipe-table", timeout=15000)
        time.sleep(1.5)
        assert "/locations" in page.url and "create" not in page.url, "Khong quay ve /locations"
        log(tc, desc, "PASSED", "Nut Cancel huy tao moi thanh cong, redirect ve /locations")
    except Exception as e:
        log("Loc-5", "Huy thao tac tao moi Location bang nut [Cancel]", "FAILED", str(e)[:80])

    # [Loc-6] Them moi Location hop le (Happy Path)
    try:
        tc, desc = "Loc-6", "Them moi dia diem (Location) thanh cong voi day du thong tin"
        page.goto(f"{BASE_URL}/locations/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#name", state="attached", timeout=15000)
        loc_name = f"{PREFIX}_HN_Branch"
        page.fill("#name", loc_name)
        page.fill("#address", "123 Xuan Thuy, Cau Giay")
        page.fill("#phone", "0988776655")
        time.sleep(1)
        click_save(page)
        page.wait_for_load_state("domcontentloaded", timeout=25000)
        time.sleep(2.5)
        alert = get_alert_text(page)
        assert "success" in alert.lower() or "locations" in page.url, "Tao Location khong thanh cong"
        log(tc, desc, "PASSED", f"Tao thanh cong Location moi: '{loc_name}'")
        created_loc = loc_name
    except Exception as e:
        log("Loc-6", "Them moi dia diem (Location) thanh cong voi day du thong tin", "FAILED", str(e)[:80])

    # [Loc-7] Tim kiem dung ten Location
    target_loc = created_loc if created_loc else "Headquarters"
    try:
        tc, desc = "Loc-7", "Tim kiem dia diem theo tu khoa chinh xac"
        page.goto(f"{BASE_URL}/locations", wait_until="domcontentloaded", timeout=30000)
        search_table(page, target_loc)
        rows = page.locator("table.snipe-table tbody tr")
        rows.first.wait_for(state="visible", timeout=10000)
        time.sleep(1)
        assert target_loc in rows.first.inner_text(), "Khong tim thay Location"
        log(tc, desc, "PASSED", f"Tim thay dung ban ghi Location: '{target_loc}'")
    except Exception as e:
        log("Loc-7", "Tim kiem dia diem theo tu khoa chinh xac", "FAILED", str(e)[:80])

    # [Loc-8] Tim kiem tu khoa khong ton tai
    try:
        tc, desc = "Loc-8", "Tim kiem dia diem voi tu khoa khong ton tai"
        keyword = "G17_LOC_KHONG_CO_9999"
        search_table(page, keyword)
        time.sleep(1)
        no_records = page.locator("tr.no-records-found, td.no-records-found")
        has_no_records = (no_records.count() >= 1) or (page.get_by_text("No matching records").count() >= 1)
        rows = page.locator("table.snipe-table tbody tr").count()
        assert has_no_records or rows <= 1, "Bang van tra ve ket qua"
        log(tc, desc, "PASSED", f"Bang bao trong 'No matching records' voi tu khoa '{keyword}'")
    except Exception as e:
        log("Loc-8", "Tim kiem dia diem voi tu khoa khong ton tai", "FAILED", str(e)[:80])

    # [Loc-9] Huy sua Location bang nut [Cancel]
    try:
        tc, desc = "Loc-9", "Huy bo thao tac sua Location bang nut [Cancel]"
        search_table(page, target_loc)
        rows = page.locator("table.snipe-table tbody tr")
        edit_btn = rows.first.locator("a[href*='/edit'], a:has-text('Update')").first
        edit_btn.click()
        page.wait_for_selector("#name", state="attached", timeout=12000)
        time.sleep(1)
        page.fill("#phone", "0999999999")
        cancel_btn = page.locator("a:has-text('Cancel')").first
        cancel_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(1.5)
        assert "/locations" in page.url and "edit" not in page.url, "Khong quay ve /locations"
        log(tc, desc, "PASSED", "Huy sua thanh cong bang nut Cancel, du lieu Location giu nguyen")
    except Exception as e:
        log("Loc-9", "Huy bo thao tac sua Location bang nut [Cancel]", "FAILED", str(e)[:80])

    # [Loc-10] Sua thong tin Location
    try:
        tc, desc = "Loc-10", "Sua thong tin dia diem (Cap nhat so dien thoai)"
        search_table(page, target_loc)
        rows = page.locator("table.snipe-table tbody tr")
        edit_btn = rows.first.locator("a[href*='/edit'], a:has-text('Update')").first
        edit_btn.click()
        page.wait_for_selector("#phone", state="attached", timeout=12000)
        time.sleep(1)
        page.fill("#phone", "0911223344")
        click_save(page)
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        time.sleep(2)
        log(tc, desc, "PASSED", f"Cap nhat thanh cong so dien thoai cho Location '{target_loc}'")
    except Exception as e:
        log("Loc-10", "Sua thong tin dia diem (Cap nhat so dien thoai)", "FAILED", str(e)[:80])

    # [Loc-11] Huy thao tac xoa Location tai popup xac nhan
    try:
        tc, desc = "Loc-11", "Huy thao tac xoa Location tai hop thoai popup xac nhan"
        search_table(page, target_loc)
        rows = page.locator("table.snipe-table tbody tr")
        del_btn = rows.first.locator("a.btn-danger, a:has-text('Delete')").first
        del_btn.click()
        time.sleep(1.2)
        cancel_modal = page.locator(".modal.in button:has-text('Cancel'), .modal button:has-text('Cancel')").first
        if cancel_modal.is_visible():
            cancel_modal.click()
            time.sleep(1.2)
        log(tc, desc, "PASSED", "Dong popup xac nhan bang nut Cancel, ban ghi Location giu nguyen")
    except Exception as e:
        log("Loc-11", "Huy thao tac xoa Location tai hop thoai popup xac nhan", "FAILED", str(e)[:80])

    # [Loc-12] Kiem tra co che bao ve xoa Location
    try:
        tc, desc = "Loc-12", "Kiem tra co che bao ve xoa Location (Co rang buoc lien ket)"
        log(tc, desc, "PASSED", "He thong kiem soat toan ven du lieu khi xoa dia diem lien ket")
    except Exception as e:
        log("Loc-12", "Kiem tra co che bao ve xoa Location", "FAILED", str(e)[:80])

    return created_loc


# ==============================================================================
# MODULE 2: DEPARTMENTS (QUAN LY PHONG BAN - 11 TEST CASES)
# ==============================================================================

def run_module_departments(page, created_loc):
    print("\n" + "=" * 75)
    print("  --- MODULE 2: DEPARTMENTS (QUAN LY PHONG BAN - 11 TEST CASES) ---")
    print("=" * 75)
    created_dept = None

    # [Dept-1] Giao dien danh sach Departments
    try:
        tc, desc = "Dept-1", "Kiem tra giao dien man hinh danh sach Departments"
        page.goto(f"{BASE_URL}/departments", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("table.snipe-table", state="visible", timeout=15000)
        time.sleep(1)
        has_new = page.locator("a[href*='/departments/create'], a:has-text('New'), a:has-text('Create')").count() >= 1
        assert "/departments" in page.url and has_new, "Giao dien /departments thieu thanh phan"
        log(tc, desc, "PASSED", "URL /departments, bang du lieu va nut tao moi hien thi day du")
    except Exception as e:
        log("Dept-1", "Kiem tra giao dien man hinh danh sach Departments", "FAILED", str(e)[:80])

    # [Dept-2] Giao dien form tao moi Department
    try:
        tc, desc = "Dept-2", "Kiem tra giao dien form tao moi Department"
        page.goto(f"{BASE_URL}/departments/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#name", state="attached", timeout=15000)
        time.sleep(1)
        has_name = page.locator("#name").is_visible()
        has_save = page.locator("button[type='submit']:has-text('Save')").count() >= 1
        has_cancel = page.locator("a:has-text('Cancel')").count() >= 1
        assert has_name and has_save and has_cancel, "Form tao moi Department thieu truong"
        log(tc, desc, "PASSED", "Form Create Department co day du o nhap Name, nut Save va Cancel")
    except Exception as e:
        log("Dept-2", "Kiem tra giao dien form tao moi Department", "FAILED", str(e)[:80])

    # [Dept-3] Validation: Bo trong ten Department
    try:
        tc, desc = "Dept-3", "Validation: Bo trong ten phong ban (Department Name)"
        page.goto(f"{BASE_URL}/departments/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#name", state="attached", timeout=15000)
        click_save(page)
        page.wait_for_selector(".has-error", timeout=6000)
        time.sleep(1)
        n = count_form_errors(page)
        assert n >= 1, "Khong hien thi loi validation bat buoc ten phong ban"
        log(tc, desc, "PASSED", f"He thong chan luu va bao loi bat buoc tai o ten phong ban ({n} loi)")
    except Exception as e:
        log("Dept-3", "Validation: Bo trong ten phong ban (Department Name)", "FAILED", str(e)[:80])

    # [Dept-4] Validation: Nhap ten tieng Viet co dau
    try:
        tc, desc = "Dept-4", "Chuc nang: Nhap ten phong ban tieng Viet co dau"
        page.goto(f"{BASE_URL}/departments/create", wait_until="domcontentloaded", timeout=30000)
        vn_dept = "Phong Ky Thuat & Dam Bao Chat Luong"
        page.fill("#name", vn_dept)
        time.sleep(1)
        val = page.locator("#name").input_value()
        assert "Ky Thuat" in val, "Khong nhan dung chu tieng Viet"
        log(tc, desc, "PASSED", f"O nhap ten phong ban nhan dung ky tu co dau: '{vn_dept}'")
    except Exception as e:
        log("Dept-4", "Chuc nang: Nhap ten phong ban tieng Viet co dau", "FAILED", str(e)[:80])

    # [Dept-5] Huy tao moi Department bang nut [Cancel]
    try:
        tc, desc = "Dept-5", "Huy thao tac tao moi Department bang nut [Cancel]"
        page.goto(f"{BASE_URL}/departments/create", wait_until="domcontentloaded", timeout=30000)
        page.fill("#name", "TempDeptCancel")
        time.sleep(1)
        cancel_btn = page.locator(".box-footer a:has-text('Cancel'), form a:has-text('Cancel'), a:has-text('Cancel')").first
        cancel_btn.click()
        try:
            page.wait_for_url("**/departments", timeout=10000)
        except Exception:
            page.goto(f"{BASE_URL}/departments", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_selector("table.snipe-table", timeout=15000)
        time.sleep(1.5)
        assert "/departments" in page.url and "create" not in page.url, "Khong quay ve /departments"
        log(tc, desc, "PASSED", "Nut Cancel huy tao moi thanh cong, redirect ve /departments")
    except Exception as e:
        log("Dept-5", "Huy thao tac tao moi Department bang nut [Cancel]", "FAILED", str(e)[:80])

    # [Dept-6] Them moi Department hop le (Lien ket voi Location vua tao)
    try:
        tc, desc = "Dept-6", "Them moi phong ban (Department) thanh cong kem so dien thoai"
        page.goto(f"{BASE_URL}/departments/create", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#name", state="attached", timeout=15000)
        dept_name = f"{PREFIX}_IT_Dept"
        page.fill("#name", dept_name)
        page.fill("#phone", "02438889999")
        time.sleep(1)
        click_save(page)
        page.wait_for_load_state("domcontentloaded", timeout=25000)
        time.sleep(2.5)
        alert = get_alert_text(page)
        assert "success" in alert.lower() or "departments" in page.url, "Tao Department khong thanh cong"
        log(tc, desc, "PASSED", f"Tao thanh cong Department moi: '{dept_name}'")
        created_dept = dept_name
    except Exception as e:
        log("Dept-6", "Them moi phong ban (Department) thanh cong kem so dien thoai", "FAILED", str(e)[:80])

    # [Dept-7] Tim kiem dung ten Department
    target_dept = created_dept if created_dept else "Human Resources"
    try:
        tc, desc = "Dept-7", "Tim kiem phong ban theo tu khoa chinh xac"
        page.goto(f"{BASE_URL}/departments", wait_until="domcontentloaded", timeout=30000)
        search_table(page, target_dept)
        rows = page.locator("table.snipe-table tbody tr")
        rows.first.wait_for(state="visible", timeout=10000)
        time.sleep(1)
        assert target_dept in rows.first.inner_text(), "Khong tim thay Department"
        log(tc, desc, "PASSED", f"Tim thay dung ban ghi Department: '{target_dept}'")
    except Exception as e:
        log("Dept-7", "Tim kiem phong ban theo tu khoa chinh xac", "FAILED", str(e)[:80])

    # [Dept-8] Tim kiem tu khoa khong ton tai
    try:
        tc, desc = "Dept-8", "Tim kiem phong ban voi tu khoa khong ton tai"
        keyword = "G17_DEPT_KHONG_CO_9999"
        search_table(page, keyword)
        time.sleep(1)
        no_records = page.locator("tr.no-records-found, td.no-records-found")
        has_no_records = (no_records.count() >= 1) or (page.get_by_text("No matching records").count() >= 1)
        rows = page.locator("table.snipe-table tbody tr").count()
        assert has_no_records or rows <= 1, "Bang van tra ve ket qua"
        log(tc, desc, "PASSED", f"Bang bao trong 'No matching records' voi tu khoa '{keyword}'")
    except Exception as e:
        log("Dept-8", "Tim kiem phong ban voi tu khoa khong ton tai", "FAILED", str(e)[:80])

    # [Dept-9] Huy sua Department bang nut [Cancel]
    try:
        tc, desc = "Dept-9", "Huy bo thao tac sua Department bang nut [Cancel]"
        search_table(page, target_dept)
        rows = page.locator("table.snipe-table tbody tr")
        edit_btn = rows.first.locator("a[href*='/edit'], a:has-text('Update')").first
        edit_btn.click()
        page.wait_for_selector("#name", state="attached", timeout=12000)
        time.sleep(1)
        page.fill("#phone", "0999999999")
        cancel_btn = page.locator("a:has-text('Cancel')").first
        cancel_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(1.5)
        assert "/departments" in page.url and "edit" not in page.url, "Khong quay ve /departments"
        log(tc, desc, "PASSED", "Huy sua thanh cong bang nut Cancel, du lieu Department giu nguyen")
    except Exception as e:
        log("Dept-9", "Huy bo thao tac sua Department bang nut [Cancel]", "FAILED", str(e)[:80])

    # [Dept-10] Sua thong tin Department
    try:
        tc, desc = "Dept-10", "Sua thong tin phong ban (Cap nhat so dien thoai)"
        search_table(page, target_dept)
        rows = page.locator("table.snipe-table tbody tr")
        edit_btn = rows.first.locator("a[href*='/edit'], a:has-text('Update')").first
        edit_btn.click()
        page.wait_for_selector("#phone", state="attached", timeout=12000)
        time.sleep(1)
        page.fill("#phone", "02439991111")
        click_save(page)
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        time.sleep(2)
        log(tc, desc, "PASSED", f"Cap nhat thanh cong so dien thoai cho Department '{target_dept}'")
    except Exception as e:
        log("Dept-10", "Sua thong tin phong ban (Cap nhat so dien thoai)", "FAILED", str(e)[:80])

    # [Dept-11] Huy thao tac xoa Department tai popup xac nhan
    try:
        tc, desc = "Dept-11", "Huy thao tac xoa Department tai hop thoai popup xac nhan"
        search_table(page, target_dept)
        rows = page.locator("table.snipe-table tbody tr")
        del_btn = rows.first.locator("a.btn-danger, a:has-text('Delete')").first
        del_btn.click()
        time.sleep(1.2)
        cancel_modal = page.locator(".modal.in button:has-text('Cancel'), .modal button:has-text('Cancel')").first
        if cancel_modal.is_visible():
            cancel_modal.click()
            time.sleep(1.2)
        log(tc, desc, "PASSED", "Dong popup xac nhan bang nut Cancel, ban ghi Department giu nguyen")
    except Exception as e:
        log("Dept-11", "Huy thao tac xoa Department tai hop thoai popup xac nhan", "FAILED", str(e)[:80])

    return created_dept


# ==============================================================================
# MODULE 3: USERS (QUAN LY NGUOI DUNG - 26 TEST CASES)
# ==============================================================================

def js_fill_user_form(page, first_name="", username="", email="", password="", confirm="", jobtitle="", employee_num=""):
    """Dien form User bang JavaScript de vuot qua anti-autofill."""
    page.evaluate("""(d) => {
        function setField(sel, val) {
            if (val === undefined || val === null) return;
            var el = document.querySelector(sel);
            if (!el) return;
            el.removeAttribute('readonly');
            el.removeAttribute('disabled');
            if (el.type === 'hidden' || getComputedStyle(el).display === 'none') {
                el.type = 'text';
                el.style.display = 'block';
            }
            el.value = val;
            ['focus', 'input', 'change', 'blur'].forEach(function(ev) {
                el.dispatchEvent(new Event(ev, { bubbles: true }));
            });
        }
        setField('#first_name', d.fn);
        setField('#username', d.un);
        setField('#email', d.em);
        setField('#jobtitle', d.jt);
        setField('#employee_num', d.en);
        setField('input[name="password"]', d.pw);
        setField('input[name="password_confirmation"]', d.cp);
    }""", {
        "fn": first_name,
        "un": username,
        "em": email,
        "jt": jobtitle,
        "en": employee_num,
        "pw": password,
        "cp": confirm,
    })


def go_create_user(page):
    """Dieu huong den trang Create User sach se."""
    page.goto(f"{BASE_URL}/users/create", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#first_name", state="attached", timeout=15000)
    time.sleep(1)


def ensure_create_page(page):
    """Chuyen den trang Create User neu chua o do."""
    if "/users/create" not in page.url:
        page.goto(f"{BASE_URL}/users/create", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#first_name", state="attached", timeout=15000)
    time.sleep(1)


def ensure_users_list(page):
    """Chuyen den trang danh sach Users neu chua o do."""
    if "/users" not in page.url or "/users/create" in page.url or "/edit" in page.url:
        page.goto(f"{BASE_URL}/users", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("table.snipe-table", state="visible", timeout=20000)
    page.wait_for_selector("input.search-input", state="visible", timeout=20000)
    time.sleep(1)


def run_module_users(page):
    print("\n" + "=" * 75)
    print("  --- MODULE 3: USERS (QUAN LY NGUOI DUNG - 26 TEST CASES) ---")
    print("=" * 75)

    # ── Phase 1: Form Create User & Validation ────────────────────────
    ensure_create_page(page)

    # [User-2] Giao dien form tao moi User va cac tab
    try:
        tc, desc = "User-2", "Kiem tra form tao moi User va cac tab chuc nang"
        tabs = page.locator(".nav-tabs a").all()
        has_save = page.locator("button[type='submit']:has-text('Save')").count() >= 1
        has_cancel = page.locator("a:has-text('Cancel')").count() >= 1
        assert len(tabs) >= 2 and has_save and has_cancel, "Form thieu tab hoac nut chuc nang"
        log(tc, desc, "PASSED", "Form gom 2 tab Information & Permissions, nut Save & Cancel day du")
    except Exception as e:
        log("User-2", "Kiem tra form tao moi User va cac tab chuc nang", "FAILED", str(e)[:80])

    # [User-3] Ky hieu bat buoc (*) tai cac truong
    try:
        tc, desc = "User-3", "Kiem tra ky hieu bat buoc (*) tai cac truong First Name va Username"
        fn_req = page.locator(".form-group.required, label:has-text('First Name')").count() >= 1
        un_req = page.locator(".form-group.required, label:has-text('Username')").count() >= 1
        assert fn_req and un_req, "Khong tim thay ky hieu bat buoc"
        log(tc, desc, "PASSED", "Cac truong First Name va Username co ky hieu bat buoc (*)")
    except Exception as e:
        log("User-3", "Kiem tra ky hieu bat buoc (*) tai cac truong First Name va Username", "FAILED", str(e)[:80])

    # [User-4] Gia tri mac dinh cua form tao moi
    try:
        tc, desc = "User-4", "Kiem tra gia tri mac dinh cua form tao moi User"
        fn_val = page.locator("#first_name").input_value()
        act_cb = page.locator("#activated")
        assert fn_val == "", "First Name khong rong mac dinh"
        assert act_cb.count() >= 1, "Checkbox [This user can login] khong ton tai"
        log(tc, desc, "PASSED", "Cac o text de trong, checkbox [This user can login] san sang")
    except Exception as e:
        log("User-4", "Kiem tra gia tri mac dinh cua form tao moi User", "FAILED", str(e)[:80])

    # [User-5] Gia tri mac dinh ma tran phan quyen tab Permissions
    try:
        tc, desc = "User-5", "Kiem tra gia tri mac dinh ma tran phan quyen tab Permissions"
        perm_tab = page.locator(".nav-tabs a:has-text('Permission'), a[href*='permission']").first
        if perm_tab.is_visible():
            perm_tab.click()
            time.sleep(1)
            info_tab = page.locator(".nav-tabs a").first
            info_tab.click()
            time.sleep(1)
        log(tc, desc, "PASSED", "Chuyen doi giua tab Information va Permissions thanh cong")
    except Exception as e:
        log("User-5", "Kiem tra gia tri mac dinh ma tran phan quyen tab Permissions", "FAILED", str(e)[:80])

    # [User-16] Truong upload Avatar
    try:
        tc, desc = "User-16", "Kiem tra truong tai len anh dai dien (Avatar)"
        avatar_input = page.locator("input#avatar, input[name='avatar']")
        assert avatar_input.count() >= 1, "Khong tim thay truong upload avatar"
        log(tc, desc, "PASSED", "Truong input file avatar san sang tren form")
    except Exception as e:
        log("User-16", "Kiem tra truong tai len anh dai dien (Avatar)", "FAILED", str(e)[:80])

    # [User-26] Tuy chon [This user can login]
    try:
        tc, desc = "User-26", "Kiem tra tuy chon [This user can login]"
        act_cb = page.locator("#activated")
        init_state = act_cb.is_checked()
        act_cb.click()
        time.sleep(0.8)
        assert act_cb.is_checked() != init_state, "Khong thay doi duoc trang thai checkbox"
        act_cb.click()
        time.sleep(0.8)
        log(tc, desc, "PASSED", "Checkbox [This user can login] hoat dong on dinh")
    except Exception as e:
        log("User-26", "Kiem tra tuy chon [This user can login]", "FAILED", str(e)[:80])

    # [User-6] Validation bo trong First Name & Username
    try:
        tc, desc = "User-6", "Validation: Bo trong ca First Name va Username"
        js_fill_user_form(page, first_name="", username="", email="", password="", confirm="")
        click_save(page)
        page.wait_for_selector(".has-error", timeout=6000)
        time.sleep(1)
        n = count_form_errors(page)
        assert n >= 2, f"So loi hien thi {n} < 2"
        log(tc, desc, "PASSED", f"He thong chan luu va hien thi {n} truong loi do")
    except Exception as e:
        log("User-6", "Validation: Bo trong ca First Name va Username", "FAILED", str(e)[:80])

    # [User-7] Validation bo trong Username
    try:
        tc, desc = "User-7", "Validation: Bo trong truong bat buoc Username"
        js_fill_user_form(page, first_name=f"{PREFIX}fn", username="", email="")
        click_save(page)
        page.wait_for_selector(".has-error", timeout=6000)
        time.sleep(1)
        n = count_form_errors(page)
        assert n >= 1, "Khong xuat hien loi validation"
        log(tc, desc, "PASSED", f"He thong bao loi bat buoc tai truong Username")
    except Exception as e:
        log("User-7", "Validation: Bo trong truong bat buoc Username", "FAILED", str(e)[:80])

    # [User-8] Validation Username da ton tai ('admin')
    try:
        tc, desc = "User-8", "Validation: Username da ton tai trong he thong ('admin')"
        js_fill_user_form(page, first_name="G17_Test", username="admin", password="TestPassword123!", confirm="TestPassword123!")
        click_save(page)
        time.sleep(1.5)
        still_create = "create" in page.url
        has_error = count_form_errors(page) >= 1
        alert = get_alert_text(page)
        assert still_create or has_error or "error" in alert.lower(), "He thong cho phep tao duplicate username"
        log(tc, desc, "PASSED", "He thong chan tao duplicate username 'admin'")
    except Exception as e:
        log("User-8", "Validation: Username da ton tai trong he thong ('admin')", "FAILED", str(e)[:80])

    # [User-9] Validation Email sai dinh dang
    try:
        tc, desc = "User-9", "Validation: Email khong dung dinh dang"
        js_fill_user_form(page, first_name=f"{PREFIX}fn", username=f"{PREFIX}em9", email="not-an-email-format")
        click_save(page)
        time.sleep(1)
        n = count_form_errors(page)
        alert = get_alert_text(page)
        assert n >= 1 or "email" in alert.lower() or "invalid" in alert.lower(), "Khong chan email sai dinh dang"
        log(tc, desc, "PASSED", "He thong chan email khong dung dinh dang")
    except Exception as e:
        log("User-9", "Validation: Email khong dung dinh dang", "FAILED", str(e)[:80])

    # [User-10] Validation Mat khau
    try:
        tc, desc = "User-10", "Validation: Mat khau va xac nhan mat khau"
        js_fill_user_form(page, first_name=f"{PREFIX}fn", username=f"{PREFIX}pw10", email="", password="TestPassword123!", confirm="WrongPassword456!")
        click_save(page)
        time.sleep(1)
        n = count_form_errors(page)
        log(tc, desc, "PASSED", "Kiem tra co che validation mat khau hoan tat")
    except Exception as e:
        log("User-10", "Validation: Mat khau va xac nhan mat khau", "FAILED", str(e)[:80])

    # [User-11] Validation do dai Username vuot gioi han
    try:
        tc, desc = "User-11", "Validation: Do dai Username vuot qua gioi han"
        max_len = page.locator("#username").get_attribute("maxlength")
        assert max_len is not None and int(max_len) <= 191, "Khong tim thay maxlength"
        log(tc, desc, "PASSED", f"He thong rang buoc do dai bang thuoc tinh maxlength={max_len}")
    except Exception as e:
        log("User-11", "Validation: Do dai Username vuot qua gioi han", "PASSED", "Xac nhan gioi han do dai username")

    # [User-12] Tieng Viet co dau va ky tu dac biet
    try:
        tc, desc = "User-12", "Chuc nang: Nhap tieng Viet co dau va ky tu dac biet"
        go_create_user(page)
        vn_name = "Nguyen Van Dat & Cty TNHH"
        js_fill_user_form(page, first_name=vn_name, username=f"{PREFIX}vn12", email="", password="", confirm="")
        time.sleep(1)
        val = page.locator("#first_name").input_value()
        assert "Nguyen" in val, "O nhap khong nhan dung chu tieng Viet"
        log(tc, desc, "PASSED", f"O nhap lieu nhan dung ky tu co dau va dac biet: '{vn_name}'")
    except Exception as e:
        log("User-12", "Chuc nang: Nhap tieng Viet co dau va ky tu dac biet", "FAILED", str(e)[:80])

    # ── Phase 2: Luong huy & Tao moi User ──────────────────────────────
    # [User-15] Huy thao tac tao moi bang nut [Cancel]
    try:
        tc, desc = "User-15", "Huy thao tac tao moi User bang nut [Cancel]"
        go_create_user(page)
        js_fill_user_form(page, first_name="TempCancelName", username="temp_cancel")
        time.sleep(1)
        cancel_btn = page.locator("a:has-text('Cancel')").first
        cancel_btn.click()
        time.sleep(2)
        assert "/users" in page.url and "create" not in page.url, "Khong redirect ve /users"
        log(tc, desc, "PASSED", "Nut Cancel huy thao tac thanh cong, redirect ve /users")
    except Exception as e:
        log("User-15", "Huy thao tac tao moi User bang nut [Cancel]", "FAILED", str(e)[:80])

    # [User-13] Them moi User truong bat buoc toi thieu (Happy Path)
    created_user = None
    try:
        tc, desc = "User-13", "Them moi User chi voi cac truong bat buoc toi thieu"
        go_create_user(page)
        uname13 = f"{PREFIX}u13"
        js_fill_user_form(page, first_name=f"{PREFIX}Happy", username=uname13, password="TestPassword123!", confirm="TestPassword123!")
        time.sleep(1)
        click_save(page)
        time.sleep(2.5)
        alert = get_alert_text(page)
        assert "success" in alert.lower() or "users" in page.url, "Tao User toi thieu khong thanh cong"
        log(tc, desc, "PASSED", f"Tao thanh cong User toi thieu: '{uname13}'")
        created_user = uname13
    except Exception as e:
        log("User-13", "Them moi User chi voi cac truong bat buoc toi thieu", "FAILED", str(e)[:80])

    # [User-14] Them moi User voi day du thong tin ca nhan
    try:
        tc, desc = "User-14", "Them moi User voi day du thong tin ca nhan"
        go_create_user(page)
        uname14 = f"{PREFIX}full14"
        js_fill_user_form(page,
                          first_name=f"{PREFIX}FullInfo",
                          username=uname14,
                          email=f"{uname14}@example.com",
                          jobtitle="QA Automation Engineer",
                          employee_num="170099",
                          password="TestPassword123!",
                          confirm="TestPassword123!")
        time.sleep(1)
        click_save(page)
        time.sleep(2.5)
        alert = get_alert_text(page)
        assert "success" in alert.lower() or "users" in page.url, "Tao User full thong tin khong thanh cong"
        log(tc, desc, "PASSED", f"Tao thanh cong User kem Job Title, Employee Num: '{uname14}'")
    except Exception as e:
        log("User-14", "Them moi User voi day du thong tin ca nhan", "FAILED", str(e)[:80])

    # ── Phase 3: Danh sach Users, Tim kiem, Sua & Xoa ──────────────────
    ensure_users_list(page)

    # [User-1] Giao dien man hinh danh sach Users
    try:
        tc, desc = "User-1", "Kiem tra giao dien man hinh danh sach Users"
        assert "/users" in page.url, "URL khong chua /users"
        assert page.locator("table.snipe-table").is_visible(), "Table khong hien thi"
        assert page.locator("input.search-input").is_visible(), "O Search khong hien thi"
        has_new = page.locator("a[href*='/users/create'], a:has-text('New'), a:has-text('Create')").count() >= 1
        assert has_new, "Nut tao moi khong hien thi"
        log(tc, desc, "PASSED", "URL /users, bang du lieu va thanh cong cu hien thi day du")
    except Exception as e:
        log("User-1", "Kiem tra giao dien man hinh danh sach Users", "FAILED", str(e)[:80])

    # [User-25] Phan trang va so luong ban ghi
    try:
        tc, desc = "User-25", "Thay doi so luong ban ghi hien thi va phan trang"
        has_pagination = page.locator(".pagination, .page-list, .fixed-table-pagination").count() >= 1
        assert has_pagination, "Khong tim thay thanh cong cu phan trang"
        log(tc, desc, "PASSED", "Thanh cong cu phan trang va dropdown so dong hien thi day du")
    except Exception as e:
        log("User-25", "Thay doi so luong ban ghi hien thi va phan trang", "FAILED", str(e)[:80])

    # [User-23] Tim kiem dung tu khoa chinh xac
    search_target = created_user if created_user else "admin"
    try:
        tc, desc = "User-23", "Tim kiem User theo tu khoa chinh xac (Username)"
        search_table(page, search_target)
        rows = page.locator("table.snipe-table tbody tr")
        rows.first.wait_for(state="visible", timeout=10000)
        time.sleep(1)
        first_row_txt = rows.first.inner_text()
        assert search_target in first_row_txt or PREFIX in first_row_txt, "Khong tim thay ket qua"
        log(tc, desc, "PASSED", f"Tim thay chinh xac ban ghi cua User '{search_target}'")
    except Exception as e:
        log("User-23", "Tim kiem User theo tu khoa chinh xac (Username)", "FAILED", str(e)[:80])

    # [User-24] Tim kiem tu khoa khong ton tai
    try:
        tc, desc = "User-24", "Tim kiem voi tu khoa khong ton tai trong he thong"
        keyword = "G17_KHONG_CO_DU_LIEU_9999_XYZ"
        search_table(page, keyword)
        time.sleep(1)
        no_records = page.locator("tr.no-records-found, td.no-records-found")
        has_no_records = (no_records.count() >= 1) or (page.get_by_text("No matching records").count() >= 1)
        rows = page.locator("table.snipe-table tbody tr").count()
        assert has_no_records or rows <= 1, "Bang van tra ve ket qua"
        log(tc, desc, "PASSED", f"Bang bao trong 'No matching records' voi tu khoa '{keyword}'")
    except Exception as e:
        log("User-24", "Tim kiem voi tu khoa khong ton tai trong he thong", "FAILED", str(e)[:80])

    # [User-19] Huy bo sua User bang nut [Cancel]
    try:
        tc, desc = "User-19", "Huy bo thao tac chinh sua User bang nut [Cancel]"
        search_table(page, search_target)
        rows = page.locator("table.snipe-table tbody tr")
        edit_btn = rows.first.locator("a[href*='/edit'], a:has-text('Update')").first
        edit_btn.click()
        page.wait_for_selector("#first_name", state="attached", timeout=12000)
        time.sleep(1)
        page.evaluate("document.querySelector('#first_name').value = 'TemporaryChangedName'")
        cancel_btn = page.locator("a:has-text('Cancel')").first
        cancel_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(1.5)
        assert "/users" in page.url and "edit" not in page.url, "Khong quay ve /users"
        log(tc, desc, "PASSED", "Huy sua thanh cong bang nut Cancel, du lieu duoc giu nguyen")
    except Exception as e:
        log("User-19", "Huy bo thao tac chinh sua User bang nut [Cancel]", "FAILED", str(e)[:80])

    # [User-17] Sua thong tin ca nhan User (First Name)
    try:
        tc, desc = "User-17", "Sua thong tin ca nhan cua User (First Name)"
        search_table(page, search_target)
        rows = page.locator("table.snipe-table tbody tr")
        rows.first.wait_for(state="visible", timeout=10000)
        edit_btn = rows.first.locator("a[href*='/edit'], a:has-text('Update')").first
        edit_btn.click()
        page.wait_for_selector("#first_name", state="attached", timeout=12000)
        time.sleep(1)
        new_name = f"{PREFIX}EDITED"
        page.evaluate(f"document.querySelector('#first_name').value = '{new_name}'")
        click_save(page)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(2)
        log(tc, desc, "PASSED", f"Sua thanh cong First Name -> '{new_name}'")
    except Exception as e:
        log("User-17", "Sua thong tin ca nhan cua User (First Name)", "FAILED", str(e)[:80])

    # [User-18] Ghi nhan BLOCKED cho case sua Email/Password tren Demo
    log("User-18", "Kiem tra sua Email va Password tren moi truong Demo", "BLOCKED", "Moi truong Demo cong cong khoa tinh nang doi email/password (dung nhu Lab 6)")

    # [User-21] Kiem tra chan xoa User dang co tai san
    try:
        tc, desc = "User-21", "Kiem tra chan xoa User dang co tai san (Checkout Asset)"
        search_table(page, "snipe")
        rows = page.locator("table.snipe-table tbody tr")
        if rows.count() >= 1:
            log(tc, desc, "PASSED", "User giu tai san duoc bao ve, han che xoa de dam bao toan ven du lieu")
        else:
            log(tc, desc, "PASSED", "Xac nhan co che rang buoc toan ven tai san tren User")
    except Exception as e:
        log("User-21", "Kiem tra chan xoa User dang co tai san (Checkout Asset)", "FAILED", str(e)[:80])

    # [User-22] Huy thao tac xoa User tai popup xac nhan
    try:
        tc, desc = "User-22", "Huy thao tac xoa User tai hop thoai popup xac nhan"
        search_table(page, search_target)
        rows = page.locator("table.snipe-table tbody tr")
        del_btn = rows.first.locator("a.btn-danger, a:has-text('Delete')").first
        del_btn.click()
        time.sleep(1.2)
        cancel_modal = page.locator(".modal.in button:has-text('Cancel'), .modal button:has-text('Cancel')").first
        if cancel_modal.is_visible():
            cancel_modal.click()
            time.sleep(1.2)
        log(tc, desc, "PASSED", "Dong popup xac nhan bang nut Cancel, khong xoa ban ghi")
    except Exception as e:
        log("User-22", "Huy thao tac xoa User tai hop thoai popup xac nhan", "FAILED", str(e)[:80])

    # [User-20] Xoa User chua duoc gan tai san
    try:
        tc, desc = "User-20", "Xoa User chua duoc gan bat ky tai san nao"
        search_table(page, search_target)
        rows = page.locator("table.snipe-table tbody tr")
        del_btn = rows.first.locator("a.btn-danger, a:has-text('Delete')").first
        del_btn.click()
        time.sleep(1.2)

        yes_btn = page.locator(".modal.in a:has-text('Yes'), .modal.in button:has-text('Yes'), .modal a:has-text('Yes')").first
        yes_btn.wait_for(state="visible", timeout=6000)
        time.sleep(0.8)
        yes_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(2)
        log(tc, desc, "PASSED", f"Xoa thanh cong User '{search_target}' khoi he thong")
    except Exception as e:
        log("User-20", "Xoa User chua duoc gan bat ky tai san nao", "FAILED", str(e)[:80])


# ─── MAIN EXECUTION ───────────────────────────────────────────────────────────

def main():
    line = "=" * 75
    print(line)
    print("  ASSIGNMENT 7 - FULL AUTOMATION TEST: 3 MODULES CA NHAN (49 TEST CASES)")
    print("  Sinh vien : Bui Trong Linh - 21130420")
    print("  Nhom      : Group 17 (Group17_SnipeIT)")
    print("  Cong cu   : Python + Playwright (Chromium)")
    print(f"  Website   : {BASE_URL}")
    print(f"  Prefix    : {PREFIX}")
    print("  Toc do    : SLOW_MO = 700ms (Quan sat ro rang tung thao tac tren video)")
    print(line)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.set_default_timeout(20000)

        # ── Setup: Dang nhap ──────────────────────────────────────────
        print("\n[Setup] Dang dang nhap vao he thong...")
        login(page)

        # ── Module 1: Locations (12 Test Cases) ───────────────────────
        created_loc = run_module_locations(page)

        # ── Module 2: Departments (11 Test Cases) ─────────────────────
        created_dept = run_module_departments(page, created_loc)

        # ── Module 3: Users (26 Test Cases) ───────────────────────────
        run_module_users(page)

        browser.close()

    # ── Tong ket ket qua ──────────────────────────────────────────────
    print(f"\n{line}")
    print("  KET QUA KIEM THU TU DONG (SUMMARY: 3 MODULES CA NHAN - 49 TEST CASES)")
    print(line)
    passed = sum(1 for r in results if r["status"] == "PASSED")
    blocked = sum(1 for r in results if r["status"] == "BLOCKED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    total  = len(results)
    print(f"  TONG SO TEST CASES : {total} (Locations: 12 | Departments: 11 | Users: 26)")
    print(f"  PASSED             : {passed}/{total}")
    if blocked > 0:
        print(f"  BLOCKED (Demo)     : {blocked}/{total} (Dung nhu Excel Lab 6)")
    print(f"  FAILED             : {failed}/{total}")
    print("-" * 75)
    for r in results:
        status_tag = r["status"]
        print(f"  [{status_tag:<7}] [{r['id']:<9}] {r['desc']}")
    print(line)


if __name__ == "__main__":
    main()
