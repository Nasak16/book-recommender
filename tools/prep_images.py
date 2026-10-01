#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ตัดขอบว่างด้านล่างของภาพหน้าจอ + เตรียมภาพประกอบสไลด์

    py -3.13 tools/prep_images.py       # -> deck_assets/
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deck_assets")
os.makedirs(OUT, exist_ok=True)


def content_bbox(path, pad=26, tol=18, x_from=480):
    """หาขอบล่างของเนื้อหา (สแกนเฉพาะพื้นที่เนื้อหาหลัก — ข้ามแถบข้างที่ยาวเต็มหน้า)"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 6, h - 6))
    px = im.load()
    last = h
    step = 4
    for y in range(h - 1, 0, -step):
        diff = 0
        for x in range(min(x_from, w // 2), w - 20, 12):
            p = px[x, y]
            if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > tol:
                diff += 1
        if diff >= 3:
            last = y + pad
            break
    return im.crop((0, 0, w, min(h, last)))


def save(im, name, max_w=1500):
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    p = os.path.join(OUT, name)
    im.save(p, optimize=True)
    print("%-22s %s  %d KB" % (name, im.size, os.path.getsize(p) // 1024))
    return p


for src, dst in [("shots/01_hero.png", "app_reco.png"),
                 ("shots/02_catalog.png", "app_catalog.png"),
                 ("shots/03_graph.png", "app_graph_tab.png"),
                 ("shots/04_demo.png", "app_demo.png"),
                 ("shots/05_about.png", "app_about.png"),
                 ("shots/06_reco_card.png", "app_top.png")]:
    p = os.path.join(ROOT, src)
    if os.path.exists(p):
        save(content_bbox(p), dst)

# ภาพการ์ดแนะำนำแบบซูม (ใช้สไลด์เดโม) — ตัดเอาเฉพาะโซนการ์ด
hero = Image.open(os.path.join(ROOT, "shots", "01_hero.png"))
save(hero.crop((0, 300, 1680, 1500)), "reco_zoom.png")
save(hero.crop((0, 0, 620, 1400)), "sidebar.png")

# ภาพกราฟที่วาดเอง + ตารางหน้าปกหนังสือ
g = os.path.join(ROOT, "tools", "out", "graph_สมชาย.png")
if os.path.exists(g):
    save(Image.open(g).convert("RGB"), "graph_somchai.png", max_w=1500)
cs = os.path.join(ROOT, "tools", "out", "contact_sheet.png")
if os.path.exists(cs):
    save(Image.open(cs).convert("RGB"), "cover_sheet.png", max_w=1500)
print("พร้อมใช้:", len(os.listdir(OUT)), "ไฟล์ ->", OUT)
