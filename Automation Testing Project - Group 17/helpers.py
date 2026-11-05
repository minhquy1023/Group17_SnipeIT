"""
Phan dung chung cho ca nhom 17 - Automation Testing Project - Group 17.
Moi file test import tu day:  from helpers import BASE_URL, unique_name
KHONG SUA file nay; can them gi thi nhan nhom truong.
"""

import time

# Cau hinh moi truong (giong Profile trong Katalon)
BASE_URL = "https://demo.snipeitapp.com"
USERNAME = "admin"
PASSWORD = "password"


def unique_name(label: str) -> str:
    """Ten du lieu test khong trung: G17_<nhan>_<so mili giay hien tai>."""
    return f"G17_{label}_{time.time_ns() // 1_000_000}"
