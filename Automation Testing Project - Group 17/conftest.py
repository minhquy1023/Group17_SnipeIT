"""
conftest.py - pytest tu doc file nay truoc khi chay bat ky test nao trong project.
Fixture viet o day duoc moi file trong tests/ dung chung, khong can import.
KHONG SUA file nay; can thay doi thi nhan nhom truong.
"""

import pytest
from playwright.sync_api import Page, expect

from helpers import BASE_URL, PASSWORD, USERNAME

# Demo phan hoi cham: moi buoc kiem tra expect(...) cho toi da 10 giay
expect.set_options(timeout=10_000)


@pytest.fixture(autouse=True)
def logged_in(page: Page):
    """Pre-condition chung cua moi test case: dang nhap thanh cong bang admin/password.
    autouse=True: tu chay truoc MOI test, khong can ghi ten fixture vao ham test."""
    page.set_default_timeout(15_000)  # moi thao tac (click, fill...) cho toi da 15 giay
    page.goto(f"{BASE_URL}/login")
    page.get_by_role("textbox", name="Username").fill(USERNAME)
    page.get_by_role("textbox", name="Password").fill(PASSWORD)
    page.get_by_role("textbox", name="Password").press("Enter")
    expect(page.get_by_role("link", name="Admin Settings")).to_be_visible()
