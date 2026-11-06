"""
ASM7 - 23130138 - Ta Van Huy - Nhom 17 - Snipe-IT.
Accessory 30, Consumable 25, Component 25 case trong Excel.
Theo README: case GUI 1-2/module kiem tra rieng; script gom 74 test chuc nang.
Moi ham test = mot ma Excel; imports dau file, 3 phan chuc nang ro rang.
Moi test tu tao G17_ co timestamp va cleanup ID rieng, ke ca khi Failed.

Cach chay tu thu muc goc repo:
    python -m pytest Automation/23130138_TaVanHuy_ASM7.py -v
Them --headed --slowmo 1000 de xem thao tac cham 1 giay, hoac -k accessory_04.
Bao cao: --html=report_Huy.html --self-contained-html --junitxml=report_Huy.xml
Minh chung: --screenshot on --tracing off --output results_Huy
Anh truoc cleanup va evidence.json tu luu trong output/screenshots/<ten-test>/.
ASM8 dung helpers/conftest cua nhom; khong sua cau hinh chung.
"""

import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, expect

# =====================================================================
# 1. CAU HINH VA DANG NHAP RIENG CHO ASM7
# =====================================================================
BASE_URL = "https://demo.snipeitapp.com"
USERNAME = "admin"
PASSWORD = "password"
expect.set_options(timeout=10_000)


def unique_name(label: str) -> str:
    return f"G17_{label}_{time.time_ns() // 1_000_000}"


@pytest.fixture(autouse=True)
def logged_in(page: Page):
    page.set_default_timeout(15_000)
    page.set_default_navigation_timeout(30_000)
    page.goto(f"{BASE_URL}/login")
    page.get_by_role("textbox", name="Username").fill(USERNAME)
    page.get_by_role("textbox", name="Password").fill(PASSWORD)
    page.get_by_role("textbox", name="Password").press("Enter")
    expect(page.get_by_role("link", name="Admin Settings")).to_be_visible()


# =====================================================================
# 2. HAM THAO TAC CHUNG - CHI GHI/XOA ID DO TEST TAO
# =====================================================================
class Inventory:
    def __init__(self, page: Page, request):
        self.page = page
        self.request = request
        self.module = request.node.name.split('_')[1]
        self.route = {'accessory': 'accessories', 'consumable': 'consumables',
                      'component': 'components'}[self.module]
        self.case = re.search(r'_(\d{2})_', request.node.name).group(1)
        self.label = f'Huy_{self.module.title()}_TC{self.case}'
        self.category = None
        self.owned = []
        self.observations = {}
        self.cleanups = []
        output = Path(request.config.getoption('--output'))
        self.folder = output / 'screenshots' / request.node.name
        self.folder.mkdir(parents=True, exist_ok=True)

    def name(self, label='Item'):
        return unique_name(f'{self.label}_{label}')

    def shot(self, step):
        self.page.screenshot(path=str(self.folder / f'{step}.png'), full_page=True)

    def goto(self, path):
        self.page.goto(f'{BASE_URL}{path}', wait_until='domcontentloaded')
        text = self.page.locator('body').inner_text()
        if 'resetting the database' in text.lower():
            pytest.skip('Demo dang reset database; chua thuc hien duoc test.')
        assert '/login' not in self.page.url, 'Session dang nhap khong con hop le'

    def field(self, name):
        return self.page.locator(f'[name="{name}"]:not([type="hidden"])').first

    def fill(self, name, value):
        field = self.field(name)
        if field.get_attribute('readonly') is not None:
            field.click()
        if name == 'purchase_date':
            # Dong bo widget ngay voi gia tri tren form, tranh blur phuc hoi ngay cu.
            applied = field.evaluate('''(el, value) => {
                const widget = window.jQuery && jQuery(el)
                    .closest('[data-provide=datetimepicker]').data('DateTimePicker');
                if (!widget) return false;
                widget.date(value); return true;
            }''', str(value))
            if applied:
                expect(field).to_have_value(str(value))
                return
        field.fill(str(value))

    def select(self, name, text, expected_id=None):
        select = self.page.locator(f'select[name="{name}"]')
        select.locator('xpath=following-sibling::span[contains(@class,"select2")]').click()
        self.page.locator('.select2-container--open input.select2-search__field').fill(text)
        options = self.page.locator('.select2-results__option[role="option"]')
        option = options.filter(has_text=re.compile(re.escape(text))).first
        expect(option).to_be_visible()
        option.click()
        assert select.input_value(), f'Chua chon {name}: {text}'
        if expected_id is not None:
            expect(select).to_have_value(str(expected_id))

    def save(self, destination='index'):
        redirect = self.page.locator('select[name="redirect_option"]')
        if redirect.count():
            redirect.select_option(destination)
        self.page.locator('#submit_button').click()

    def success(self):
        alert = self.page.locator('.alert-success').filter(visible=True).first
        expect(alert).to_be_visible()
        return alert.inner_text()

    def ready(self):
        table = f'#{self.route}ListingTable'
        self.page.locator(table).wait_for()
        self.page.wait_for_function('''id => !!(window.jQuery &&
            jQuery(id).data('bootstrap.table'))''', arg=table)
        expect(self.page.locator('.fixed-table-loading.open')).to_have_count(0)

    def data(self):
        self.ready()
        rows = self.page.evaluate('''id => jQuery(id).bootstrapTable('getData')''',
                                  f'#{self.route}ListingTable')
        for row in rows:
            row['name'] = html.unescape(row['name'])
        return rows

    def action(self, callback):
        with self.page.expect_response(
            lambda r: f'/api/v1/{self.route}?' in r.url and r.request.method == 'GET'
        ):
            callback()
        self.ready()

    def search(self, text):
        self.goto('/' + self.route)
        self.ready()
        box = self.page.locator('.fixed-table-toolbar input.search-input')
        if box.input_value() != text:
            box.fill(text)
            with self.page.expect_response(
                lambda r: f'/api/v1/{self.route}?' in r.url
                and parse_qs(urlparse(r.url).query).get('search') == [text]
            ):
                box.press('Enter')
        self.ready()
        return self.data()

    def find(self, record):
        rows = self.search(record['name'])
        found = next((r for r in rows if str(r['id']) == str(record['id'])), None)
        assert found is not None, f'Khong tim thay ID cua test: {record}'
        return found

    def create_form(self):
        self.goto('/' + self.route + '/create')
        expect(self.field('name')).to_be_visible()

    def category_fixture(self):
        if self.category:
            return
        name = self.name('Cat')
        record = {'route': 'categories', 'name': name, 'id': None}
        self.owned.append(record)
        self.goto('/categories/create')
        self.fill('name', name)
        self.page.locator('[name="category_type"]').select_option(self.module)
        eula = self.page.locator('[name="use_default_eula"]')
        if eula.count():
            eula.uncheck()
        self.save()
        # Fixture is verified by its unique persisted Select2 ID, not a timed flash message.
        expect(self.page).to_have_url(f'{BASE_URL}/categories')
        self.create_form()
        self.select('category_id', name)
        record['id'] = self.field('category_id').input_value()
        self.category = record

    def inputs(self, name, qty='10', category=True):
        self.fill('name', name)
        if category:
            self.select('category_id', self.category['name'], self.category['id'])
        self.fill('qty', qty)
        self.observations['input'] = {'name': self.field('name').input_value(),
                                      'qty': self.field('qty').input_value()}

    def remember_created(self, name):
        match = re.search(rf'/{self.route}/(\d+)(?:[?#].*)?$', self.page.url)
        assert match, f'Create khong tra ID moi: {self.page.url}'
        record = {'route': self.route, 'name': name, 'id': match.group(1)}
        self.owned.append(record)
        self.observations['created_id'] = record['id']
        return record

    def create(self, qty=10, name=None, extras=None, verify=True):
        self.category_fixture()
        self.create_form()
        name = name or self.name()
        self.inputs(name, str(qty))
        for key, value in (extras or {}).items():
            if key == 'purchase_cost' and self.module != 'accessory':
                hint = self.field(key).locator('xpath=ancestor::div[contains(@class,"form-group")]').inner_text()
                if '1.234,56' in hint:
                    value = str(value).replace('.', ',')
                self.observations['money_format_hint'] = hint
            self.fill(key, value)
            expect(self.field(key)).to_have_value(str(value))
        if extras:
            self.shot('01_InputOptional')
        self.save('item')
        self.success()
        record = self.remember_created(name)
        if verify:
            row = self.find(record)
            assert int(row.get('qty') or 0) == qty, f'Quantity luu khac {qty}: {row}'
            assert row['category']['name'] == self.category['name']
        return record

    def edit(self, record):
        self.goto(f'/{self.route}/{record["id"]}/edit')
        expect(self.field('name')).to_have_value(record['name'])

    def optional(self):
        extras = {'model_number': self.name('Model'), 'notes': self.name('Note'),
                  'min_amt': '1', 'order_number': self.name('Order'),
                  'purchase_date': '2026-10-01', 'purchase_cost': '25.50'}
        record = self.create(5, extras=extras)
        row = self.find(record)
        self.observations['persisted_optional'] = {
            k: row.get(k) for k in ['purchase_cost', 'purchase_date', 'orders']}
        self.edit(record)
        for key in ['model_number', 'notes', 'min_amt']:
            expect(self.field(key)).to_have_value(extras[key])
        self.goto(f'/{self.route}/{record["id"]}')
        orders = self.page.locator('a[href="#orders"]')
        if orders.count():
            orders.click()
        expect(self.page.locator('.content')).to_contain_text(extras['order_number'])
        expect(self.page.locator('.content')).to_contain_text(re.compile(r'25[.,]50'))
        assert row['purchase_date']['date'] == extras['purchase_date']
        self.shot('02_OrdersPersisted')

    def reject(self, field):
        before = self.page.url
        self.save()
        # Success redirect proves a negative case was accepted; do not convert it to Pass.
        self.page.wait_for_function('''([url,name]) => location.href!==url ||
            [...document.querySelectorAll('.has-error,.alert-danger,.error,.invalid-feedback')]
            .some(e=>e.offsetParent!==null && e.textContent.trim()) ||
            [...document.getElementsByName(name)].some(e=>e.validity && !e.validity.valid)
        ''', arg=[before, field])
        self.shot('02_Validation')
        assert self.page.url == before, f'Invalid {field} duoc chap nhan: {self.page.url}'
        native = self.field(field).evaluate('el=>el.validationMessage || ""')
        errors = self.page.locator(
            '.has-error,.alert-danger,.error,.invalid-feedback'
        ).filter(visible=True).all_text_contents()
        aliases = {'qty': 'quantity', 'category_id': 'category',
                   'asset_id': 'asset', 'assigned_user': 'user',
                   'checkout_qty': 'quantity', 'assigned_qty': 'quantity'}
        assert native or aliases.get(field, field) in ' '.join(errors).lower(), errors
        self.observations['validation'] = native or ' '.join(errors)

    def invalid_create(self, name=None, qty='3', field='name', category=True):
        self.category_fixture()
        self.create_form()
        name = self.name('Invalid') if name is None else name
        marker = self.name('Marker')
        self.inputs(name, qty, category)
        self.fill('model_number', marker)
        # Unique marker is registered BEFORE Save, so unexpected acceptance is cleaned too.
        pending = {'route': self.route, 'id': None, 'name': name, 'marker': marker}
        self.owned.append(pending)
        self.shot('01_InvalidInput')
        self.reject(field)
        assert not self.search(marker), 'Invalid form da tao ban ghi moi'
        self.owned.remove(pending)

    def cancel_create(self):
        self.category_fixture()
        name = self.name('Cancel')
        self.create_form()
        self.fill('name', name)
        self.page.locator(f'.content a.btn-link[href="{BASE_URL}/{self.route}"]').click()
        self.page.wait_for_url(f'{BASE_URL}/{self.route}')
        assert not self.search(name), 'Cancel van luu ban ghi'

    def edit_form(self):
        record = self.create()
        self.edit(record)
        expect(self.field('category_id')).to_have_value(self.category['id'])

    def rename(self):
        record = self.create()
        old_name = record['name']
        new_name = self.name('Updated')
        self.edit(record)
        self.fill('name', new_name)
        self.save()
        self.success()
        record['name'] = new_name
        assert self.find(record)['name'] == new_name
        assert not any(str(r['id']) == record['id'] for r in self.search(old_name))

    def adjust(self):
        record = self.create()
        self.edit(record)
        if self.field('qty').count():
            self.fill('qty', '12')
            self.save()
            self.success()
        else:
            self.find(record)
            self.page.locator(
                f'button.adjust-quantity[data-adjust-url="{BASE_URL}/{self.route}/'
                f'{record["id"]}/adjust-quantity"]'
            ).click()
            modal = self.page.locator('#adjustQuantityModal')
            modal.locator('[name="amount"]').fill('2')
            note = modal.locator('[name="note"]')
            if note.count():
                note.fill(self.label + '_Qty')
            modal.locator('button[type=submit]').click()
            expect(modal).not_to_be_visible()
        assert int(self.find(record)['qty']) == 12, 'Adjust +2 phai cho tong 12'

    def edit_blank(self):
        record = self.create()
        self.edit(record)
        self.fill('name', '')
        self.reject('name')
        assert self.find(record)['name'] == record['name']

    def cancel_edit(self):
        record = self.create()
        self.edit(record)
        self.fill('name', self.name('Unsaved'))
        self.page.locator(f'.content a.btn-link[href="{BASE_URL}/{self.route}"]').click()
        self.page.wait_for_url(f'{BASE_URL}/{self.route}')
        assert self.find(record)['name'] == record['name']

    def search_existing(self):
        record = self.create()
        assert str(self.find(record)['id']) == record['id']

    def search_missing(self):
        assert not self.search(self.name('NotFound'))
        expect(self.page.locator('tr.no-records-found')).to_contain_text('No matching records')

    def sort(self):
        stem = self.name('Sort')
        for suffix in ['A', 'B', 'C']:
            self.create(1, name=stem + '_' + suffix)
        self.search(stem)
        samples = []
        for _ in range(2):
            self.action(lambda: self.page.locator(f'#{self.route}ListingTable th[data-field=name] .sortable').click())
            names = [r['name'] for r in self.data()]
            direction = self.page.evaluate('id=>jQuery(id).bootstrapTable("getOptions").sortOrder',
                                           f'#{self.route}ListingTable')
            assert len(names) == 3
            assert names == sorted(names, reverse=direction == 'desc')
            samples.append(direction)
        assert samples[0] != samples[1], 'Hai lan click phai doi chieu sap xep'

    def pagination(self):
        stem = self.name('Page')
        for n in range(1, 22):
            self.create(1, name=f'{stem}_{n:02d}', verify=False)
            print(f'[Paging fixture] {self.module} {n}/21', flush=True)
        self.search(stem)
        size = self.page.evaluate('id=>jQuery(id).bootstrapTable("getOptions").pageSize',
                                  f'#{self.route}ListingTable')
        if size != 20:
            self.page.locator('.page-list button.dropdown-toggle').first.click()
            option = self.page.locator('.page-list .dropdown-menu a').filter(
                has_text=re.compile('^20$'), visible=True).first
            self.action(lambda: option.click())
        first = {r['id'] for r in self.data()}
        assert len(first) == 20
        self.shot('01_Page1')
        self.action(lambda: self.page.locator('.pagination .page-next a').first.click())
        second = {r['id'] for r in self.data()}
        assert len(second) == 1 and first.isdisjoint(second)
        expect(self.page.locator('.pagination .active').first).to_have_text('2')
        expected = {int(r['id']) for r in self.owned if r['route'] == self.route}
        assert first | second == expected, 'Hai trang phai chua dung 21 ID test vua tao'
        self.shot('02_Page2')

    def recipient(self):
        if self.module != 'component':
            # Public demo forbids deleting users (editableOnDemo gate).
            # Reuse the login account read-only; never edit/delete this baseline user.
            return {'route': 'users', 'name': 'Admin User', 'id': '1', 'owned': False}
        name = self.name('Asset')
        route = 'hardware'
        pending = {'route': route, 'name': name, 'id': None}
        self.owned.append(pending)
        self.goto('/' + route + '/create')
        self.fill('asset_tags[1]', name)
        if not self.field('name').is_visible():
            self.page.locator('#optional_info').click()
        self.fill('name', name)
        self.select('model_id', 'Macbook')
        self.field('status_id').select_option(label='Ready to Deploy')
        self.save('item')
        self.success()
        match = re.search(rf'/{route}/(\d+)(?:[?#].*)?$', self.page.url)
        assert match, f'Khong co ID moi cua {route}: {self.page.url}'
        pending['id'] = match.group(1)
        return pending

    def checkout_form(self, record):
        self.goto(f'/{self.route}/{record["id"]}/checkout')
        expect(self.field(self.qty_field)).to_be_visible()

    @property
    def qty_field(self):
        return 'assigned_qty' if self.module == 'component' else 'checkout_qty'

    @property
    def target_field(self):
        return 'asset_id' if self.module == 'component' else 'assigned_user'

    def assign(self, record, target, qty=2):
        self.checkout_form(record)
        self.select(self.target_field, target['name'], target['id'])
        self.fill(self.qty_field, str(qty))
        self.shot('01_CheckoutInput')
        self.save()
        self.success()
        record['target'] = target

    def checkout_valid(self):
        record = self.create()
        target = self.recipient()
        self.assign(record, target)
        row = self.find(record)
        assert int(row['remaining']) == 8 and int(row['qty']) == 10
        self.goto(f'/{self.route}/{record["id"]}')
        table = self.page.locator(f'#{self.module}CheckedOutListingTable')
        header = table.get_by_role(
            'columnheader', name=re.compile(r'^(Name|Checked out to)$', re.IGNORECASE))
        expect(header).to_be_visible()
        index = header.evaluate('th=>Array.from(th.parentElement.children).indexOf(th)+1')
        links = table.locator(f'tbody tr td:nth-child({index}) a[href]')
        expect(links.first).to_be_visible()
        hrefs = links.evaluate_all('es=>es.map(e=>e.href)')
        assert set(hrefs) == {f'{BASE_URL}/{target["route"]}/{target["id"]}'}, hrefs
        self.observations['recipient_links'] = hrefs
        self.observations['stock'] = {'total': 10, 'available': row['remaining'], 'target': target}

    def checkout_missing(self):
        record = self.create()
        self.checkout_form(record)
        self.fill(self.qty_field, '1')
        self.reject(self.target_field)
        assert int(self.find(record)['remaining']) == 10

    def checkout_over(self):
        record = self.create()
        target = self.recipient()
        self.checkout_form(record)
        self.select(self.target_field, target['name'], target['id'])
        self.fill(self.qty_field, '11')
        self.reject(self.qty_field)
        assert int(self.find(record)['remaining']) == 10

    def checkin(self, record, qty=None):
        self.goto(f'/{self.route}/{record["id"]}')
        target = record.get('target')
        rows = self.page.locator('tr')
        if target:
            rows = rows.filter(has=self.page.locator(f'a[href="{BASE_URL}/{target["route"]}/{target["id"]}"]'))
        link = rows.locator('a[href*="/checkin"]').filter(visible=True).first
        expect(link).to_be_visible()
        link.click()
        quantity = self.field('checkin_qty')
        if quantity.count():
            value = str(qty) if qty is not None else quantity.get_attribute('max') or quantity.input_value()
            quantity.fill(value)
        self.page.locator('#submit_button').click()
        self.success()

    def checkin_partial(self):
        record = self.create()
        target = self.recipient()
        self.assign(record, target)
        assert int(self.find(record)['remaining']) == 8
        self.checkin(record, 1)
        row = self.find(record)
        assert int(row['remaining']) == 9 and int(row['qty']) == 10
        self.observations['stock'] = {'total': 10, 'available': 9, 'assigned': 1}
        self.goto(f'/{self.route}/{record["id"]}')

    def delete(self, record, cancel=False, loaded=False):
        if not loaded:
            self.goto('/' + record['route'])
            box = self.page.locator('.fixed-table-toolbar input.search-input').first
            expect(box).to_be_visible()
            query = record.get('marker') or record['name']
            if box.input_value() != query:
                box.fill(query)
                with self.page.expect_response(lambda r: f'/api/v1/{record["route"]}?' in r.url
                                               and parse_qs(urlparse(r.url).query).get('search') == [query]):
                    box.press('Enter')
        expect(self.page.locator('.fixed-table-loading.open')).to_have_count(0)
        if record['id'] is None:
            # A candidate created by this exact unique marker, not any old same-name record.
            links = self.page.locator(f'a.delete-asset[href*="/{record["route"]}/"]')
            if not links.count():
                return
            assert links.count() == 1, 'Marker bat ngo trung; khong xoa nham ban ghi'
            record['id'] = links.first.get_attribute('href').rstrip('/').split('/')[-1]
        button = self.page.locator(f'a.delete-asset[href="{BASE_URL}/{record["route"]}/{record["id"]}"]')
        if not button.count():
            # Delete case already removed this ID; no cleanup mutation required.
            if self.page.locator(f'a[href="{BASE_URL}/{record["route"]}/{record["id"]}"]').count():
                raise AssertionError(f'Ban ghi con ton tai nhung khong co Delete: {record}')
            return
        button.click()
        modal = self.page.locator('#dataConfirmModal')
        expect(modal).to_contain_text(record['name'])
        if cancel:
            modal.locator('button[data-dismiss="modal"].btn').click()
            expect(modal).not_to_be_visible()
            return
        modal.locator('#dataConfirmOK').click()
        expect(modal).not_to_be_visible()
        self.success()

    def delete_case(self, cancel=False):
        record = self.create()
        self.delete(record, cancel)
        rows = self.search(record['name'])
        assert any(str(r['id']) == record['id'] for r in rows) == cancel

    def cleanup(self):
        errors = []
        items = [r for r in self.owned if r['route'] == self.route]
        others = [r for r in self.owned if r['route'] != self.route]
        for record in items + list(reversed(others)):
            try:
                if record['route'] == self.route and record['id'] is None:
                    rows = self.search(record.get('marker') or record['name'])
                    if rows:
                        assert len(rows) == 1, 'Unique marker trung; khong cleanup nham'
                        record['id'] = str(rows[0]['id'])
                        self.observations['unexpected_persisted'] = {
                            key: rows[0].get(key) for key in ['id', 'name', 'qty', 'remaining']}
                if record['route'] == self.route and record.get('id'):
                    rows = self.search(record.get('marker') or record['name'])
                    row = next((r for r in rows if str(r['id']) == record['id']), None)
                    if self.module == 'consumable' and row and int(row.get('checked_out') or 0):
                        for _ in range(20):
                            if int(row.get('checked_out') or 0) == 0:
                                break
                            self.goto(f'/consumables/{record["id"]}')
                            forms = self.page.locator(
                                f'#consumableCheckedOutListingTable '
                                f'form[action^="{BASE_URL}/consumables/{record["id"]}/consume/"]')
                            # Wait for AJAX rows after every redirect before consuming the next unit.
                            expect(forms.first).to_be_visible()
                            before = int(row['checked_out'])
                            with self.page.expect_response(
                                lambda r: f'/consumables/{record["id"]}/consume/' in r.url
                                and r.request.method == 'POST'
                            ) as response:
                                forms.first.locator('button[type="submit"]').click()
                            assert 200 <= response.value.status < 400, 'Mark as consumed khong thanh cong'
                            row = self.find(record)
                            assert int(row.get('checked_out') or 0) < before
                        assert int(row.get('checked_out') or 0) == 0
                        self.observations['cleanup_consumed'] = True
                    for _ in range(20):
                        if self.module == 'consumable':
                            break  # Consumed units never return to available stock.
                        if not row or int(row.get('remaining') or 0) >= int(row.get('qty') or 0):
                            break
                        before = int(row.get('remaining') or 0)
                        self.checkin(record)
                        row = self.find(record)
                        assert int(row['remaining']) > before, 'Checkin khong tang ton kho'
                self.delete(record, loaded=record['route'] == self.route)
                self.cleanups.append({'record': record.copy(), 'status': 'deleted_or_absent'})
            except Exception as error:
                errors.append(f'{record}: {error}')
                self.cleanups.append({'record': record.copy(), 'status': 'error', 'error': str(error)})
        return errors


# =====================================================================
# 3. FIXTURE: CHUP MINH CHUNG TRUOC CLEANUP, DON DU LIEU SAU MOI TEST
# =====================================================================
@pytest.fixture
def page(page: Page, request):
    """Kiem tra maintenance truoc khi fixture logged_in cua nhom dung page.
    Ke thua page fixture cua pytest-playwright; khong tu dang nhap o ASM8.
    GET chi doc trang login, khong thay doi tai khoan hay du lieu test.
    """
    reason = ''
    for attempt in range(3):
        try:
            response = page.request.get(f'{BASE_URL}/login', timeout=10_000)
            maintenance = 'resetting the database' in response.text().lower()
            if response.status < 500 and not maintenance:
                yield page
                return
            reason = f'Demo HTTP {response.status}; maintenance={maintenance}'
        except Exception as error:
            reason = f'Demo availability: {error}'
        if attempt < 2:
            page.wait_for_timeout(5_000)
    folder = Path(request.config.getoption('--output')) / 'screenshots' / request.node.name
    folder.mkdir(parents=True, exist_ok=True)
    try:
        page.goto(f'{BASE_URL}/login', wait_until='domcontentloaded', timeout=15_000)
        page.screenshot(path=str(folder / '00_DemoUnavailable.png'), full_page=True)
    except Exception:
        pass
    request.node.add_report_section('setup', 'environment', reason)
    pytest.skip(reason + '; chay lai khi website hoat dong. Khong tinh Passed.')


@pytest.fixture
def inventory(page: Page, request):
    inv = Inventory(page, request)
    started = datetime.now(timezone.utc).isoformat()
    yield inv
    screenshot_error = None
    try:
        inv.shot('99_BeforeCleanup')
    except Exception as error:
        screenshot_error = str(error)
    errors = inv.cleanup()
    manifest = {'test': request.node.name, 'started': started,
                'observations': inv.observations, 'owned': inv.owned,
                'cleanup': inv.cleanups, 'screenshot_error': screenshot_error}
    (inv.folder / 'evidence.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    assert not errors, 'Cleanup chua hoan tat:\n' + '\n'.join(errors)

# =====================================================================
# 4. ACCESSORY - TEST CASE THEO MA EXCEL
# =====================================================================


def test_accessory_03_defaults(inventory):
    """[Accessory-3] Kiểm tra giá trị mặc định form."""
    inventory.create_form()
    for name in ['name', 'model_number', 'notes', 'purchase_date', 'purchase_cost']:
        expect(inventory.field(name)).to_have_value('')
    assert inventory.field('qty').input_value() in ['', '0']
    expect(inventory.field('category_id')).to_have_value('')


def test_accessory_04_create_required(inventory):
    """[Accessory-4] Tạo phụ kiện hợp lệ với trường bắt buộc."""
    inventory.create()


def test_accessory_05_create_optional(inventory):
    """[Accessory-5] Tạo phụ kiện với thông tin bổ sung."""
    inventory.optional()


def test_accessory_06_missing_name(inventory):
    """[Accessory-6] Không nhập tên phụ kiện."""
    inventory.invalid_create(name='', field='name')


def test_accessory_07_missing_category(inventory):
    """[Accessory-7] Không chọn danh mục."""
    inventory.invalid_create(field='category_id', category=False)


def test_accessory_08_blank_quantity_optional(inventory):
    """[Accessory-8] Bỏ trống số lượng."""
    inventory.category_fixture()
    inventory.create_form()
    name = inventory.name('BlankQty')
    inventory.inputs(name, '')
    inventory.save('item')
    if '/create' in inventory.page.url:
        inventory.reject('qty')
    else:
        inventory.success()
        record = inventory.remember_created(name)
        row = inventory.find(record)
        assert int(row.get('remaining') or 0) == 0
        assert int(row.get('checkouts_count') or 0) == 0


def test_accessory_09_negative_quantity(inventory):
    """[Accessory-9] Nhập số lượng âm."""
    inventory.invalid_create(qty='-1', field='qty')


def test_accessory_10_text_quantity(inventory):
    """[Accessory-10] Nhập chữ vào số lượng."""
    inventory.category_fixture()
    inventory.create_form()
    inventory.inputs(inventory.name('TextQty'), '')
    inventory.field('qty').press_sequentially('abc')
    assert inventory.field('qty').input_value() != 'abc'
    assert inventory.field('qty').get_attribute('type') == 'number'
    inventory.shot('01_LettersBlocked')


def test_accessory_11_decimal_quantity(inventory):
    """[Accessory-11] Nhập số lượng thập phân."""
    inventory.invalid_create(qty='1.5', field='qty')


def test_accessory_12_zero_quantity(inventory):
    """[Accessory-12] Nhập số lượng bằng 0."""
    inventory.create(qty=0)


def test_accessory_13_whitespace_name(inventory):
    """[Accessory-13] Tên chỉ chứa khoảng trắng."""
    inventory.invalid_create(name='    ', field='name')


def test_accessory_14_vietnamese_name(inventory):
    """[Accessory-14] Tên tiếng Việt có dấu."""
    inventory.create(name=inventory.name('Chuot_không_dây'))


def test_accessory_15_special_name(inventory):
    """[Accessory-15] Tên chứa ký tự đặc biệt."""
    inventory.create(name=inventory.name('Mouse_#1_@'))


def test_accessory_16_html_name(inventory):
    """[Accessory-16] Tên chứa chuỗi HTML."""
    record = inventory.create(name=inventory.name('<b>Mouse</b>'))
    inventory.find(record)
    link = inventory.page.locator(
        f'#accessoriesListingTable a[href="{BASE_URL}/accessories/{record["id"]}"]:not(.delete-asset)')
    expect(link).to_have_text(record['name'])
    assert link.locator('b,script').count() == 0


def test_accessory_17_cancel_create(inventory):
    """[Accessory-17] Hủy thao tác tạo mới."""
    inventory.cancel_create()


def test_accessory_18_edit_form(inventory):
    """[Accessory-18] Mở form chỉnh sửa."""
    inventory.edit_form()


def test_accessory_19_edit_name(inventory):
    """[Accessory-19] Sửa tên phụ kiện."""
    inventory.rename()


def test_accessory_20_edit_quantity(inventory):
    """[Accessory-20] Sửa số lượng."""
    inventory.adjust()


def test_accessory_21_edit_blank_name(inventory):
    """[Accessory-21] Sửa tên thành rỗng."""
    inventory.edit_blank()


def test_accessory_22_cancel_edit(inventory):
    """[Accessory-22] Hủy thao tác chỉnh sửa."""
    inventory.cancel_edit()


def test_accessory_23_search_existing(inventory):
    """[Accessory-23] Tìm kiếm phụ kiện tồn tại."""
    inventory.search_existing()


def test_accessory_24_search_not_found(inventory):
    """[Accessory-24] Tìm kiếm không có kết quả."""
    inventory.search_missing()


def test_accessory_25_sort_name(inventory):
    """[Accessory-25] Sắp xếp danh sách theo tên."""
    inventory.sort()


def test_accessory_26_pagination(inventory):
    """[Accessory-26] Chuyển trang danh sách."""
    inventory.pagination()


def test_accessory_27_checkout_form(inventory):
    """[Accessory-27] Mở thao tác cấp phát phụ kiện."""
    record = inventory.create()
    inventory.checkout_form(record)
    expect(inventory.field('checkout_qty')).to_have_value('1')
    assert inventory.field('checkout_qty').get_attribute('max') == '10'
    expect(inventory.page.locator('#submit_button')).to_be_visible()


def test_accessory_28_checkout_valid(inventory):
    """[Accessory-28] Cấp phát số lượng hợp lệ."""
    inventory.checkout_valid()


def test_accessory_29_checkout_over_stock(inventory):
    """[Accessory-29] Không cấp phát vượt số lượng khả dụng."""
    inventory.checkout_over()


def test_accessory_30_cancel_delete(inventory):
    """[Accessory-30] Hủy thao tác xóa phụ kiện."""
    inventory.delete_case(cancel=True)


# =====================================================================
# 5. CONSUMABLE - TEST CASE THEO MA EXCEL
# =====================================================================


def test_consumable_03_create_required(inventory):
    """[Consumable-3] Tạo mới với dữ liệu bắt buộc."""
    inventory.create()


def test_consumable_04_create_optional(inventory):
    """[Consumable-4] Tạo mới với thông tin bổ sung."""
    inventory.optional()


def test_consumable_05_missing_name(inventory):
    """[Consumable-5] Không nhập Name."""
    inventory.invalid_create(name='', field='name')


def test_consumable_06_missing_category(inventory):
    """[Consumable-6] Không chọn Category."""
    inventory.invalid_create(field='category_id', category=False)


def test_consumable_07_blank_quantity(inventory):
    """[Consumable-7] Bỏ trống Quantity."""
    inventory.invalid_create(qty='', field='qty')


def test_consumable_08_negative_quantity(inventory):
    """[Consumable-8] Quantity âm."""
    inventory.invalid_create(qty='-1', field='qty')


def test_consumable_09_text_quantity(inventory):
    """[Consumable-9] Quantity không nhận ký tự chữ."""
    inventory.category_fixture()
    inventory.create_form()
    inventory.inputs(inventory.name('TextQty'), '')
    inventory.field('qty').press_sequentially('abc')
    assert inventory.field('qty').input_value() != 'abc'
    assert inventory.field('qty').get_attribute('type') == 'number'
    inventory.shot('01_LettersBlocked')
    inventory.owned.append({'route': inventory.route, 'id': None, 'name': inventory.field('name').input_value()})
    inventory.reject('qty')


def test_consumable_10_decimal_quantity(inventory):
    """[Consumable-10] Quantity thập phân."""
    inventory.invalid_create(qty='1.5', field='qty')


def test_consumable_11_zero_quantity(inventory):
    """[Consumable-11] Quantity bằng 0."""
    inventory.create(qty=0)


def test_consumable_12_cancel_create(inventory):
    """[Consumable-12] Hủy tạo mới."""
    inventory.cancel_create()


def test_consumable_13_edit_form(inventory):
    """[Consumable-13] Mở form sửa đúng bản ghi."""
    inventory.edit_form()


def test_consumable_14_edit_name(inventory):
    """[Consumable-14] Sửa Name hợp lệ."""
    inventory.rename()


def test_consumable_15_edit_quantity(inventory):
    """[Consumable-15] Sửa số lượng từ 10 lên 12."""
    inventory.adjust()


def test_consumable_16_edit_blank_name(inventory):
    """[Consumable-16] Sửa Name thành rỗng."""
    inventory.edit_blank()


def test_consumable_17_cancel_edit(inventory):
    """[Consumable-17] Hủy chỉnh sửa."""
    inventory.cancel_edit()


def test_consumable_18_search_existing(inventory):
    """[Consumable-18] Tìm kiếm có kết quả."""
    inventory.search_existing()


def test_consumable_19_search_not_found(inventory):
    """[Consumable-19] Tìm kiếm không có kết quả."""
    inventory.search_missing()


def test_consumable_20_sort_name(inventory):
    """[Consumable-20] Sắp xếp theo Name."""
    inventory.sort()


def test_consumable_21_pagination(inventory):
    """[Consumable-21] Chuyển trang danh sách."""
    inventory.pagination()


def test_consumable_22_checkout_valid(inventory):
    """[Consumable-22] Cấp phát 2 đơn vị cho người dùng."""
    inventory.checkout_valid()


def test_consumable_23_checkout_missing(inventory):
    """[Consumable-23] Không chọn người nhận khi cấp phát."""
    inventory.checkout_missing()


def test_consumable_24_checkout_over_stock(inventory):
    """[Consumable-24] Không cấp phát vượt tồn."""
    inventory.checkout_over()


def test_consumable_25_delete(inventory):
    """[Consumable-25] Xóa bản ghi chưa cấp phát."""
    inventory.delete_case()


# =====================================================================
# 6. COMPONENT - TEST CASE THEO MA EXCEL
# =====================================================================


def test_component_03_create_required(inventory):
    """[Component-3] Tạo mới với dữ liệu bắt buộc."""
    inventory.create()


def test_component_04_create_optional(inventory):
    """[Component-4] Tạo mới với thông tin bổ sung."""
    inventory.optional()


def test_component_05_missing_name(inventory):
    """[Component-5] Không nhập Name."""
    inventory.invalid_create(name='', field='name')


def test_component_06_missing_category(inventory):
    """[Component-6] Không chọn Category."""
    inventory.invalid_create(field='category_id', category=False)


def test_component_07_blank_quantity(inventory):
    """[Component-7] Bỏ trống Quantity."""
    inventory.invalid_create(qty='', field='qty')


def test_component_08_negative_quantity(inventory):
    """[Component-8] Quantity âm."""
    inventory.invalid_create(qty='-1', field='qty')


def test_component_09_decimal_quantity(inventory):
    """[Component-9] Quantity thập phân."""
    inventory.invalid_create(qty='1.5', field='qty')


def test_component_10_zero_quantity(inventory):
    """[Component-10] Quantity bằng 0."""
    inventory.invalid_create(qty='0', field='qty')


def test_component_11_cancel_create(inventory):
    """[Component-11] Hủy tạo mới."""
    inventory.cancel_create()


def test_component_12_edit_form(inventory):
    """[Component-12] Mở form sửa đúng bản ghi."""
    inventory.edit_form()


def test_component_13_edit_name(inventory):
    """[Component-13] Sửa Name hợp lệ."""
    inventory.rename()


def test_component_14_edit_quantity(inventory):
    """[Component-14] Sửa số lượng từ 10 lên 12."""
    inventory.adjust()


def test_component_15_edit_blank_name(inventory):
    """[Component-15] Sửa Name thành rỗng."""
    inventory.edit_blank()


def test_component_16_cancel_edit(inventory):
    """[Component-16] Hủy chỉnh sửa."""
    inventory.cancel_edit()


def test_component_17_search_existing(inventory):
    """[Component-17] Tìm kiếm có kết quả."""
    inventory.search_existing()


def test_component_18_search_not_found(inventory):
    """[Component-18] Tìm kiếm không có kết quả."""
    inventory.search_missing()


def test_component_19_sort_name(inventory):
    """[Component-19] Sắp xếp theo Name."""
    inventory.sort()


def test_component_20_pagination(inventory):
    """[Component-20] Chuyển trang danh sách."""
    inventory.pagination()


def test_component_21_checkout_valid(inventory):
    """[Component-21] Gắn 2 linh kiện vào tài sản."""
    inventory.checkout_valid()


def test_component_22_checkout_missing(inventory):
    """[Component-22] Không chọn tài sản khi gắn."""
    inventory.checkout_missing()


def test_component_23_checkout_over_stock(inventory):
    """[Component-23] Không cấp phát vượt tồn."""
    inventory.checkout_over()


def test_component_24_checkin_partial(inventory):
    """[Component-24] Thu hồi 1 linh kiện đã gắn."""
    inventory.checkin_partial()


def test_component_25_delete(inventory):
    """[Component-25] Xóa bản ghi chưa cấp phát."""
    inventory.delete_case()
