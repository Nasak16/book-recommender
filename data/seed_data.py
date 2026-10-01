#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ข้อมูลตั้งต้นของระบบแนะนำหนังสือ — ของเราเอง (สมมติจากการสำรวจเพื่อนในห้อง)

Single source of truth: the Colab notebook builder and the Streamlit app both read this file,
so the notebook's data can never drift from the app's data.

USERS  : 12 คน
LIKES  : (user, book_id) — ผู้ใช้ "ชอบ/อ่านแล้ว" หนังสือเล่มนั้น
GENRES : book_id -> หมวด (โหลดจาก data/books.json ตอนรัน)
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

USERS = [
    {"user": "สมชาย", "age": 20, "group": "แฟนตาซี/สืบสวน"},
    {"user": "มะลิ", "age": 19, "group": "แฟนตาซี/เยาวชน"},
    {"user": "นรินทร์", "age": 21, "group": "แฟนตาซี"},
    {"user": "พลอย", "age": 20, "group": "สืบสวน"},
    {"user": "อนุชา", "age": 22, "group": "ไซไฟ/คอมพิวเตอร์"},
    {"user": "ธนกร", "age": 21, "group": "คอมพิวเตอร์"},
    {"user": "มินต์", "age": 20, "group": "พัฒนาตัวเอง"},
    {"user": "กัญญา", "age": 19, "group": "พัฒนาตัวเอง/การเงิน"},
    {"user": "เฟิร์น", "age": 18, "group": "การ์ตูน/เยาวชน"},
    {"user": "ชัย", "age": 22, "group": "การ์ตูน/ไซไฟ"},
    {"user": "แบม", "age": 21, "group": "สืบสวน/ดิสโทเปีย"},
    {"user": "ปวีณา", "age": 23, "group": "คลาสสิก/ประวัติศาสตร์"},
]

# book_id อ้างอิง data/books.json (สร้างจาก Open Library)
LIKES = [
    # สมชาย — แฟนตาซี + สืบสวน (แกนหลักของเดโม)
    ("สมชาย", "B01"), ("สมชาย", "B02"), ("สมชาย", "B03"), ("สมชาย", "B11"),
    # มะลิ — แฟนตาซี/เยาวชน คาบเกี่ยวกับสมชาย
    ("มะลิ", "B01"), ("มะลิ", "B02"), ("มะลิ", "B04"), ("มะลิ", "B25"),
    # นรินทร์ — แฟนตาซี คาบกับสมชายมาก (B01,B02,B03)
    ("นรินทร์", "B01"), ("นรินทร์", "B02"), ("นรินทร์", "B03"), ("นรินทร์", "B04"), ("นรินทร์", "B05"),
    # พลอย — สืบสวนล้วน
    ("พลอย", "B11"), ("พลอย", "B12"), ("พลอย", "B13"), ("พลอย", "B26"),
    # อนุชา — ไซไฟ/คอมพิวเตอร์
    ("อนุชา", "B05"), ("อนุชา", "B06"), ("อนุชา", "B21"), ("อนุชา", "B22"), ("อนุชา", "B07"),
    # ธนกร — คอมพิวเตอร์ คาบกับอนุชา
    ("ธนกร", "B21"), ("ธนกร", "B22"), ("ธนกร", "B17"),
    # มินต์ — พัฒนาตัวเอง/จิตวิทยา
    ("มินต์", "B15"), ("มินต์", "B16"), ("มินต์", "B17"), ("มินต์", "B10"),
    # กัญญา — พัฒนาตัวเอง/การเงิน
    ("กัญญา", "B15"), ("กัญญา", "B18"), ("กัญญา", "B20"), ("กัญญา", "B19"),
    # เฟิร์น — การ์ตูน/เยาวชน
    ("เฟิร์น", "B24"), ("เฟิร์น", "B27"), ("เฟิร์น", "B25"), ("เฟิร์น", "B23"),
    # ชัย — การ์ตูน/ไซไฟ
    ("ชัย", "B24"), ("ชัย", "B27"), ("ชัย", "B06"), ("ชัย", "B04"),
    # แบม — สืบสวน/ดิสโทเปีย
    ("แบม", "B13"), ("แบม", "B14"), ("แบม", "B08"), ("แบม", "B28"), ("แบม", "B26"),
    # ปวีณา — คลาสสิก/ประวัติศาสตร์
    ("ปวีณา", "B07"), ("ปวีณา", "B08"), ("ปวีณา", "B09"), ("ปวีณา", "B19"), ("ปวีณา", "B23"),
]


def load_books():
    with open(os.path.join(_HERE, "books.json"), encoding="utf-8") as f:
        return json.load(f)


def graph_data():
    """คืนค่า (users, books, likes) พร้อมตรวจความถูกต้องของข้อมูล"""
    books = load_books()
    ids = {b["book_id"] for b in books}
    bad = [l for l in LIKES if l[0] not in {u["user"] for u in USERS} or l[1] not in ids]
    if bad:
        raise ValueError("LIKES อ้างถึงข้อมูลที่ไม่มีอยู่: %s" % bad)
    liked_books = {b for _, b in LIKES}
    floating = ids - liked_books          # หนังสือที่ไม่มีใครชอบ = โหนดลอยในกราฟ
    if floating:
        raise ValueError("หนังสือที่ไม่มีใครชอบ (โหนดลอย): %s" % sorted(floating))
    return USERS, books, LIKES


if __name__ == "__main__":
    users, books, likes = graph_data()
    per_user = {u["user"]: sum(1 for l in likes if l[0] == u["user"]) for u in users}
    per_book = {b["book_id"]: sum(1 for l in likes if l[1] == b["book_id"]) for b in books}
    print("users", len(users), "books", len(books), "likes", len(likes))
    print("ชอบต่อคน :", per_user)
    print("min/max ต่อเล่ม:", min(per_book.values()), max(per_book.values()))
    print("เล่มยอดนิยม:", sorted(per_book.items(), key=lambda kv: -kv[1])[:5])
