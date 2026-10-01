#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ถ่ายภาพหน้าจอแอป Streamlit จริง (ใช้ทำสไลด์นำเสนอ)"""
import os, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8777"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shots")
os.makedirs(OUT, exist_ok=True)

TABS = [("01_hero", None), ("02_catalog", "คลังหนังสือ"),
        ("03_graph", "โครงสร้างกราฟ"), ("04_demo", "เดโมสด"),
        ("05_about", "เกี่ยวกับระบบ")]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1680, "height": 3400}, device_scale_factor=1.0,
                        locale="th-TH")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(9000)

    for name, tab in TABS:
        if tab:
            try:
                pg.get_by_role("tab", name=tab, exact=False).first.click(timeout=15000)
            except Exception:
                pg.click(f"text={tab}", timeout=15000)
            pg.wait_for_timeout(7000)
        path = os.path.join(OUT, name + ".png")
        pg.screenshot(path=path, full_page=True)
        print("shot", path, os.path.getsize(path) // 1024, "KB")

    # ภาพแถบข้างแบบซูม + การ์ดแนะนำ 1 ใบ (ช็อตเดี่ยวสำหรับสไลด์)
    pg.get_by_role("tab", name="แนะนำหนังสือ", exact=False).first.click()
    pg.wait_for_timeout(6000)
    pg.screenshot(path=os.path.join(OUT, "06_reco_card.png"),
                  clip={"x": 0, "y": 0, "width": 1680, "height": 1000})
    print("shot 06_reco_card.png")
    b.close()