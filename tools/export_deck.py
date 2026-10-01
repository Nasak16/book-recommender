#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export สไลด์เป็น PDF + PNG ต่อหน้า (ใช้ PowerPoint COM → ต้องรันด้วย `python` 3.11)

    python tools/export_deck.py
"""
import glob, os, sys
import win32com.client as win32

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SL = os.path.join(ROOT, "slides")
PPTX = [p for p in glob.glob(os.path.join(SL, "*.pptx")) if not p.startswith("~$")][0]
PDF = os.path.join(SL, "นำเสนอระบบแนะนำหนังสือ_007.pdf")
PNGDIR = os.path.join(SL, "png")
os.makedirs(PNGDIR, exist_ok=True)

app = win32.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(os.path.abspath(PPTX), WithWindow=False)
try:
    pres.SaveAs(os.path.abspath(PDF), 32)                  # 32 = ppSaveAsPDF
    pres.SaveAs(os.path.abspath(PNGDIR), 18)               # 18 = ppSaveAsPNG
finally:
    pres.Close()
    app.Quit()

pngs = sorted(glob.glob(os.path.join(PNGDIR, "*.PNG")) + glob.glob(os.path.join(PNGDIR, "*.png")))
print("PDF :", PDF, os.path.getsize(PDF) // 1024, "KB")
print("PNG :", len(pngs), "ไฟล์ ->", PNGDIR)
for p in pngs:
    print("   ", os.path.basename(p), os.path.getsize(p) // 1024, "KB")
