#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างโน๊ตบุ๊ก .ipynb สำหรับส่ง (Colab + Neo4j) จากข้อมูลชุดเดียวกับแอป

    py -3.13 tools/build_notebook.py            # ตัวส่งจริง (ใช้ Neo4j Aura + getpass)
    py -3.13 tools/build_notebook.py --test     # สำเนาทดสอบ (ต่อ Neo4j ในเครื่อง)

ห้ามมี docstring สามชั้นในข้อความเซลล์ (จะพังตอนประกอบ) — ใช้ # แทน
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "data"))
import seed_data  # noqa: E402

TEST = "--test" in sys.argv
REPO = "Nasak16/book-recommender"
COVER_BASE = f"https://cdn.jsdelivr.net/gh/{REPO}@main/assets/covers/"
OUT = os.path.join(ROOT, "notebooks" if not TEST else os.path.join("tools", "out"),
                   "BookRecommender_Neo4j_007.ipynb")

users, books, likes = seed_data.graph_data()
for b in books:
    b["cover"] = os.path.basename(b["cover_file"])

BOOKS_PY = "[\n" + "".join(
    "    {\"book_id\": \"%s\", \"title\": \"%s\", \"author\": \"%s\", \"genre\": \"%s\", "
    "\"isbn\": \"%s\", \"year\": %s, \"cover\": \"%s\"},\n"
    % (b["book_id"], b["title"].replace('"', "'"), b["author"].replace('"', "'"),
       b["genre"], b["isbn"], b["year"], b["cover"]) for b in books) + "]"
USERS_PY = "[\n" + "".join(
    "    {\"user\": \"%s\", \"age\": %s, \"group\": \"%s\"},\n" % (u["user"], u["age"], u["group"])
    for u in users) + "]"
LIKES_PY = "[\n" + "".join(
    "    (\"%s\", \"%s\"),\n" % (u, b) for u, b in likes) + "]"

MD, PY = {}, {}

# ------------------------------------------------------------------ cell 0-1
MD[0] = """[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/gist/Nasak16/247492673b9b3a74dd39bd7d442d398c/BookRecommender_Neo4j_007.ipynb)

GitHub: https://github.com/Nasak16/book-recommender

# 📚 ระบบแนะนำหนังสือด้วย Graph Database (Neo4j)

**ผู้จัดทำ:** รหัส 007 · **งาน:** พัฒนาระบบแนะนำเป็นระบบของตัวเอง

ระบบนี้เป็น **ระบบแนะนำหนังสือ** ที่สร้างข้อมูลขึ้นเองทั้งชุด (ไม่ใช้ dataset สำเร็จรูป)
12 คน × 28 เล่ม × 51 ความชอบ — และ **แสดงภาพปกหนังสือจริง** ในผลการแนะนำ

**แนวคิด** ผู้ใช้ชอบหนังสืออะไร → หาคนอื่นที่ชอบเล่มเดียวกัน (รสนิยมใกล้กัน) →
ดูว่าเขาชอบเล่มอะไรอีกที่เรายังไม่เคยอ่าน → เรียงตามคะแนน = คำแนะนำ

หัวใจของงานนี้คือใช้ **ฐานข้อมูลกราฟ (Neo4j)** เพราะข้อมูลแบบ "ใครชอบอะไร" เป็นเรื่องของ
ความสัมพันธ์ ไม่ใช่ตาราง — เขียนคำถามได้สั้นมาก (`MATCH (u)-[:LIKES]->(b)`) และอธิบายย้อนหลังได้ว่า
ทำไมระบบถึงแนะนำเล่มนั้น"""

PY[1] = """!pip -q install neo4j pandas

import getpass
import pandas as pd
from collections import Counter
from neo4j import GraphDatabase
from IPython.display import HTML, display

# ---- ข้อมูลการเชื่อมต่อ (เวอร์ชันส่งจริงใช้ Neo4j Aura ของเราเอง) ----
URI = "neo4j+s://<รหัส-instance>.databases.neo4j.io"
USER = "neo4j"
PASSWORD = getpass.getpass("Neo4j password: ")

def connect(uri=None, user=None, password=None):
    driver = GraphDatabase.driver(uri or URI, auth=(user or USER, password or PASSWORD))
    driver.verify_connectivity()
    return driver

def run(driver, query, **params):
    with driver.session() as s:
        return [r.data() for r in s.run(query, **params)]

driver = connect()
print("เชื่อมต่อสำเร็จ:", driver.get_server_info().agent)"""

# ------------------------------------------------------------------ data
MD[2] = """## 👥 ข้อมูลชุดของเรา (เก็บเอง ไม่ใช่ dataset สำเร็จรูป)

| องค์ประกอบ | จำนวน | รายละเอียด |
|---|---|---|
| ผู้ใช้ | 12 คน | สอบถามเพื่อนในห้องว่า "ชอบหนังสือเรื่องอะไร" (ข้อมูลสมมติเพื่อสาธิต) |
| หนังสือ | 28 เล่ม | ครอบคลุม 14 หมวด: แฟนตาซี ไซไฟ สืบสวน พัฒนาตัวเอง การเงิน การ์ตูน คลาสสิก ฯลฯ |
| ความชอบ | 51 เส้น | ความสัมพันธ์ `LIKES` หนึ่งเส้น = "คนนี้ชอบเล่มนี้" |

**ภาพปก** ดึงจาก Open Library (ฟรี ไม่ต้องใช้ API key) แล้วเก็บไฟล์ไว้ในโปรเจกต์ GitHub
จึงแสดงในผลการแนะนำได้ทุกที่ — ในโน๊ตบุ๊กนี้อ่านภาพผ่าน jsDelivr CDN ของ repo
`https://github.com/Nasak16/book-recommender`"""

PY[3] = """COVER_BASE = "%s"

USERS = %s

BOOKS = %s

LIKES = %s
""" % (COVER_BASE, USERS_PY, BOOKS_PY, LIKES_PY) + """
BOOK = {b["book_id"]: b for b in BOOKS}

def cover_url(book_id):
    return COVER_BASE + BOOK[book_id]["cover"]

def show_cards(rows, title=None, height=200):
    # แสดงผลเป็น "การ์ดหนังสือ" พร้อมภาพปก — ใช้ HTML ให้ Colab เรนเดอร์รูปได้
    css_box = ("display:flex;gap:12px;flex-wrap:wrap;margin:6px 0 14px 0")
    css_card = ("width:150px;background:#172136;border:1px solid #2B3A5C;border-radius:10px;"
                "padding:8px;color:#E9EFFA;font-family:sans-serif")
    html = []
    if title:
        html.append("<h4 style='color:#E9EFFA;font-family:sans-serif'>" + title + "</h4>")
    html.append("<div style='" + css_box + "'>")
    for r in rows:
        bid = r["book_id"]
        b = BOOK[bid]
        badge = ""
        if r.get("score") is not None:
            badge = "<div style='color:#FBBF24'>คะแนน " + str(r["score"]) + "</div>"
        elif r.get("votes"):
            badge = "<div style='color:#FBBF24'>" + str(r["votes"]) + " โหวต จาก " + \\
                    ", ".join(r.get("voters", [])) + "</div>"
        elif r.get("genre_hits"):
            badge = "<div style='color:#38BDF8'>หมวด " + b["genre"] + "</div>"
        why = ""
        if r.get("via_books"):
            why = "<div style='color:#9FB0CB;font-size:11px'>เพราะคุณชอบ: " + \\
                  ", ".join(r["via_books"]) + "</div>"
        html.append(
            "<div style='" + css_card + "'>"
            "<img src='" + cover_url(bid) + "' style='width:100%;height:" + str(height) +
            "px;object-fit:cover;border-radius:6px'>"
            "<div style='font-weight:600;margin-top:6px'>" + b["title"] + "</div>"
            "<div style='color:#9FB0CB;font-size:12px'>" + b["author"] + " · " + b["genre"] +
            "</div>" + badge + why + "</div>")
    html.append("</div>")
    display(HTML("".join(html)))

print("ผู้ใช้", len(USERS), "คน | หนังสือ", len(BOOKS), "เล่ม | ความชอบ", len(LIKES), "เส้น")
show_cards([{"book_id": b["book_id"]} for b in BOOKS[:6]],
           title="ตัวอย่างหนังสือในระบบ (แสดงภาพปกจาก Open Library)")"""

# ------------------------------------------------------------------ schema
MD[4] = """## 🧩 โครงสร้างกราฟที่ใช้ในงานนี้

| องค์ประกอบ | รายละเอียด |
|---|---|
| โหนด `User` | 12 โหนด (ชื่อผู้ใช้, อายุ, กลุ่มความสนใจ) |
| โหนด `Book` | 28 โหนด (ชื่อเรื่อง, ผู้เขียน, ISBN, หมวด) |
| โหนด `Genre` | 14 โหนด (หมวดหนังสือ) |
| ความสัมพันธ์ `LIKES` | `(User)-[:LIKES]->(Book)` — ผู้ใช้ชอบหนังสือเล่มนั้น |
| ความสัมพันธ์ `IN_GENRE` | `(Book)-[:IN_GENRE]->(Genre)` — หนังสืออยู่หมวดไหน |

การเดิน 3 hop เพื่อหาคำแนะนำ

```
                 สมชาย (คนที่เราจะแนะนำ)
                        ↓ [:LIKES]
        Harry Potter · The Hobbit · LOTR · Da Vinci Code
                        ↓ ใครชอบเล่มพวกนี้เหมือนกัน
            คนรสนิยมใกล้กัน (นรินทร์ · มะลิ · พลอย)
                        ↓ เล่มอื่นที่คนกลุ่มนี้ชอบ
   The Hunger Games · Dune · The Lightning Thief · ...
                        ↓ นับคะแนน
                  คำแนะนำสำหรับสมชาย
```

เริ่มจากล้างฐานข้อมูลเดิม แล้วสร้าง constraint ให้ `user` / `book_id` / `name` ไม่ซ้ำ"""

PY[5] = """Q_RESET = "MATCH (n) DETACH DELETE n"

Q_CONSTRAINTS = [
    "CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.user IS UNIQUE",
    "CREATE CONSTRAINT book_id IF NOT EXISTS FOR (b:Book) REQUIRE b.book_id IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
]

Q_LOAD_USERS = '''
UNWIND $rows AS row
MERGE (u:User {user: row.user})
SET u.age = row.age, u.group = row.group, u.node_type = 'user'
RETURN count(u) AS users
'''

Q_LOAD_BOOKS = '''
UNWIND $rows AS row
MERGE (b:Book {book_id: row.book_id})
SET b.title = row.title, b.author = row.author, b.genre = row.genre,
    b.isbn = row.isbn, b.year = row.year, b.cover = row.cover, b.node_type = 'book'
MERGE (g:Genre {name: row.genre})
MERGE (b)-[:IN_GENRE]->(g)
RETURN count(b) AS books
'''

Q_LOAD_LIKES = '''
UNWIND $rows AS row
MATCH (u:User {user: row.user})
MATCH (b:Book {book_id: row.book_id})
MERGE (u)-[:LIKES]->(b)
RETURN count(*) AS likes
'''

run(driver, Q_RESET)
for q in Q_CONSTRAINTS:
    run(driver, q)
print("สร้างผู้ใช้:", run(driver, Q_LOAD_USERS, rows=USERS))
print("สร้างหนังสือ:", run(driver, Q_LOAD_BOOKS, rows=BOOKS))
print("สร้างความชอบ:", run(driver, Q_LOAD_LIKES,
                          rows=[{"user": u, "book_id": b} for u, b in LIKES]))"""

MD[6] = """## ✅ ตรวจสอบว่าข้อมูลเข้าครบตามที่ออกแบบไว้

ถ้าตัวเลขตรงกับตารางข้างบน แปลว่าข้อมูลชุดเดียวกันถูกโหลดเข้า Neo4j แล้วจริง"""

PY[7] = """Q_STATS = '''
MATCH (u:User) WITH count(u) AS users
MATCH (b:Book) WITH users, count(b) AS books
MATCH ()-[r:LIKES]->() WITH users, books, count(r) AS likes
MATCH (g:Genre) RETURN users, books, likes, count(g) AS genres
'''

stats = run(driver, Q_STATS)[0]
print("สรุปฐานข้อมูล:", stats)

rows = run(driver, '''
    MATCH (b:Book) OPTIONAL MATCH (b)<-[:LIKES]-(u:User)
    RETURN b.genre AS หมวด, count(DISTINCT b) AS จำนวนเล่ม, count(u) AS ความชอบรวม
    ORDER BY ความชอบรวม DESC''')
display(pd.DataFrame(rows))"""

# ------------------------------------------------------------------ Q1
MD[8] = """## ❓ คำถามข้อ 1: ผู้ใช้คนนี้ชอบหนังสืออะไรบ้าง?

Neighbor ของโหนดผู้ใช้ = หนังสือที่เขาเชื่อมด้วย `[:LIKES]`
เขียนเป็น Cypher ได้สั้น ๆ ว่า `MATCH (u)-[:LIKES]->(b)` แล้วคืน `b` ทั้งหมด"""

PY[9] = """Q_LIKED = '''
MATCH (u:User {user: $user})-[:LIKES]->(b:Book)
OPTIONAL MATCH (b)-[:IN_GENRE]->(g:Genre)
RETURN b.book_id AS book_id, b.title AS title, b.author AS author,
       b.genre AS genre, collect(g.name) AS genres
ORDER BY b.title
'''

TARGET = "สมชาย"
liked = run(driver, Q_LIKED, user=TARGET)
display(pd.DataFrame(liked)[["book_id", "title", "author", "genre"]])
show_cards(liked, title="หนังสือที่ " + TARGET + " ชอบอยู่แล้ว (" + str(len(liked)) + " เล่ม)")"""

# ------------------------------------------------------------------ Q2
MD[10] = """## ❓ คำถามข้อ 2: ใครมีรสนิยมใกล้ "สมชาย" และใกล้แค่ไหน?

วิธีคิด: หาหนังสือที่ทั้งสองคนชอบร่วมกัน แล้วเทียบสัดส่วนด้วย **Jaccard similarity**

```
Jaccard(เรา, เขา) = |หนังสือที่ชอบร่วมกัน| / |หนังสือของสองคนรวมกัน (ไม่ซ้ำ)|
```

- 0 = ไม่มีเล่มไหนเหมือนกันเลย
- 1 = ชอบเหมือนกันทุกเล่ม
"""

PY[11] = """Q_SIMILAR = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Book)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.book_id) AS common
MATCH (me)-[:LIKES]->(mine:Book)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Book)
WITH other, common, n_mine, count(DISTINCT theirs) AS n_theirs
RETURN other.user AS user, size(common) AS common_count, common AS common_books,
       n_mine, n_theirs,
       toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard
ORDER BY jaccard DESC, user
'''

sims = run(driver, Q_SIMILAR, user=TARGET)
display(pd.DataFrame([{**s, "jaccard": round(s["jaccard"], 3)} for s in sims]))
print("อ่านผล: คนที่ได้ Jaccard สูงสุดคือคนที่รสนิยมใกล้เราที่สุด — "
      "น้ำหนักโหวตของเขาจะมากกว่าคนที่ชอบบังเอิญตรงกันเล่มเดียว")"""

# ------------------------------------------------------------------ v1
MD[12] = """## 🎯 เริ่มสร้างระบบ Recommendation (เวอร์ชัน 1: นับโหวต)

ลำดับการทำงานบนกราฟ (3 hop) เขียนเป็น Cypher ได้ในคำสั่งเดียว

```
MATCH (me)-[:LIKES]->(shared:Book)<-[:LIKES]-(other)-[:LIKES]->(rec:Book)
```

> 💡 **จุดสังเกตสำคัญ** — ถ้าเขียนด้วยลูปใน Python (แบบในคลาส) จะนับซ้ำได้ง่าย
> เช่นเพื่อนที่ชอบตรงกับเราหลายเล่มจะออกเสียงหลายครั้ง แต่ใน Cypher เราใช้
> `count(DISTINCT other)` ทำให้ **1 คน = 1 เสียง ต่อ 1 เล่ม** อย่างอัตโนมัติ
> และ `WHERE NOT (me)-[:LIKES]->(rec)` กันไม่ให้แนะนำเล่มที่เราชอบแล้ว"""

PY[13] = """Q_RECO_VOTES = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Book)<-[:LIKES]-(other:User)-[:LIKES]->(rec:Book)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.book_id AS book_id, rec.title AS title, rec.author AS author, rec.genre AS genre,
       count(DISTINCT other) AS votes,
       collect(DISTINCT other.user) AS voters,
       collect(DISTINCT shared.title) AS via_books
ORDER BY votes DESC, title
'''

votes = run(driver, Q_RECO_VOTES, user=TARGET)
display(pd.DataFrame(votes)[["title", "votes", "voters"]])
show_cards(votes[:4], title="คำแนะนำจากเพื่อน (นับโหวต) — " + str(len(votes)) + " เล่มที่เข้าเกณฑ์")

top = votes[0]
print("อันดับ 1 คือ", top["title"], "ได้", top["votes"], "โหวต จาก", ", ".join(top["voters"]))
print("เหตุผล: คุณชอบ", ", ".join(top["via_books"]), "ซึ่งเพื่อนกลุ่มนี้ก็ชอบเหมือนกัน")"""

# ------------------------------------------------------------------ v2
MD[14] = """## ⭐ เวอร์ชัน 2: ถ่วงน้ำหนักด้วยความคล้าย (Jaccard)

เวอร์ชันนับโหวตให้ทุกคนน้ำหนักเท่ากัน ปัญหาคือ "เพื่อนที่ชอบตรงกันเล่มเดียว" มีเสียงเท่ากับ
"เพื่อนที่รสนิยมเหมือนเราเกือบทั้งหมด" — เวอร์ชันนี้จึงคูณน้ำหนักด้วย Jaccard

```
คะแนน(เล่ม) = Σ Jaccard(เรา, คนที่ชอบเล่มนั้น)
```
"""

PY[15] = """Q_RECO_WEIGHTED = '''
MATCH (me:User {user: $user})-[:LIKES]->(shared:Book)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.book_id) AS common
MATCH (me)-[:LIKES]->(mine:Book)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Book)
WITH me, other, common, n_mine, count(DISTINCT theirs) AS n_theirs
WITH me, other, toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard, common
MATCH (other)-[:LIKES]->(rec:Book)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.book_id AS book_id, rec.title AS title, rec.author AS author, rec.genre AS genre,
       round(sum(jaccard) * 1000) / 1000.0 AS score,
       count(DISTINCT other) AS votes, collect(DISTINCT other.user) AS voters,
       collect(DISTINCT rec.genre) AS genres
ORDER BY score DESC, title
'''

weighted = run(driver, Q_RECO_WEIGHTED, user=TARGET)
display(pd.DataFrame(weighted)[["title", "score", "votes", "voters"]])
show_cards(weighted[:3], title="3 อันดับแรก: คำแนะนำแบบถ่วงน้ำหนัก (Jaccard)")
print("เทียบกับเวอร์ชันนับโหวต: อันดับอาจสลับกัน เพราะเล่มที่คนรสนิยมใกล้เราสุดชอบ จะได้คะแนนสูงกว่า")"""

# ------------------------------------------------------------------ content + hybrid
MD[16] = """## 🏷️ เพิ่มอีกสัญญาณ: หมวดหนังสือ (Content-based) แล้วผสมกับสัญญาณเพื่อน

Collaborative Filtering มีจุดอ่อนเรื่อง **cold start** — คนใหม่ที่ยังไม่มีความชอบร่วมกับใครเลย
จะไม่ได้คำแนะนำอะไร ระบบนี้จึงใช้โหนด `Genre` เป็นสัญญาณที่สอง

- **สายหมวด** `(me)-[:LIKES]->(:Book)-[:IN_GENRE]->(Genre)<-[:IN_GENRE]-(rec)` → หนังสือหมวดที่เราชอบ
- **ผสม** `คะแนน = 0.6 × (คะแนนเพื่อนที่ normalize) + 0.4 × (คะแนนหมวดที่ normalize)`
"""

PY[17] = """Q_RECO_CONTENT = '''
MATCH (me:User {user: $user})-[:LIKES]->(:Book)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec:Book)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.book_id AS book_id, rec.title AS title, rec.author AS author, rec.genre AS genre,
       collect(DISTINCT g.name) AS genres, count(DISTINCT g) AS genre_hits
ORDER BY genre_hits DESC, title
'''

content = run(driver, Q_RECO_CONTENT, user=TARGET)
display(pd.DataFrame(content)[["title", "genre", "genre_hits"]])
show_cards(content[:3], title="คำแนะนำจากหมวดหนังสือที่ " + TARGET + " ชอบ")

def hybrid(user, top_n=5, weight_collab=0.6):
    # รวมสองสัญญาณหลัง normalize ให้คะแนนอยู่ช่วง 0-1 เท่ากัน
    recs = {r["book_id"]: r for r in run(driver, Q_RECO_WEIGHTED, user=user)}
    gens = {r["book_id"]: r for r in run(driver, Q_RECO_CONTENT, user=user)}
    max_s = max([r["score"] for r in recs.values()] or [0]) or 1
    max_g = max([r["genre_hits"] for r in gens.values()] or [0]) or 1
    out = {}
    for bid in set(recs) | set(gens):
        c, g = recs.get(bid), gens.get(bid)
        base = c or g
        out[bid] = {"book_id": bid, "title": base["title"], "author": base["author"],
                    "genre": base.get("genre"),
                    "score": round(weight_collab * (c["score"] if c else 0) / max_s
                                   + (1 - weight_collab) * (g["genre_hits"] if g else 0) / max_g, 3),
                    "because": ("เพื่อน + หมวดที่คุณชอบ" if c and g else
                                "เพื่อนที่รสนิยมใกล้ชอบ" if c else "หมวดหนังสือที่คุณชอบ"),
                    "voters": (c or {}).get("voters", []),
                    "via_books": (c or {}).get("via_books", [])}
    return sorted(out.values(), key=lambda r: (-r["score"], r["title"]))[:top_n]

mixed = hybrid(TARGET)
display(pd.DataFrame(mixed))
show_cards(mixed, title="คำแนะนำแบบผสม (เพื่อน 60% + หมวด 40%)")"""

# ------------------------------------------------------------------ all users
MD[18] = """## 📊 คำแนะนำของทุกคนในระบบ + เทียบกับ baseline

ระบบที่ใช้ได้จริงต้องตอบได้ว่า "ทุกคนได้อะไร" และเรามี **baseline** ให้เทียบว่า
คำแนะนำเฉพาะบุคคลดีกว่าการแนะนำของยอดนิยม (Popular) อย่างไร"""

PY[19] = """rows = []
for u in USERS:
    top = run(driver, Q_RECO_WEIGHTED, user=u["user"])[:3]
    rows.append({"ผู้ใช้": u["user"], "กลุ่มความสนใจ": u["group"],
                 "คำแนะนำ 3 อันดับ (%s)" % "คะแนน":
                     " | ".join(r["title"][:30] + " (" + str(r["score"]) + ")" for r in top)})
display(pd.DataFrame(rows))

Q_POPULAR = '''
MATCH (b:Book)<-[:LIKES]-(u:User)
RETURN b.book_id AS book_id, b.title AS title, count(u) AS likes
ORDER BY likes DESC, title LIMIT 5
'''
popular = run(driver, Q_POPULAR)
show_cards(popular, title="Baseline: 5 เล่มยอดนิยมในระบบ (แนะนำแบบไม่ดูว่าใครเป็นใคร)")
print("ทุกคนจะได้ลิสต์เดียวกัน = ไม่เฉพาะบุคคล ระบบของเราจึงดูที่ความคล้ายของแต่ละคนแทน")"""

# ------------------------------------------------------------------ cold start
MD[20] = """## 🧊 Cold start: ผู้ใช้ใหม่ที่มีข้อมูลน้อย

เพิ่มผู้ใช้ใหม่ที่ชอบแค่เล่มเดียว **และเล่มนั้นยังไม่มีใครในระบบชอบเลย**
กรณีนี้สัญญาณจาก "เพื่อน" (collaborative filtering) จะว่างเปล่า แต่ระบบของเรายังแนะนำได้
เพราะใช้ **หมวดหนังสือ** (โหนด `Genre`) เป็นสัญญาณสำรอง — ถ้าใช้เฉพาะ collaborative filtering
ผู้ใช้แบบนี้จะไม่ได้คำแนะนำอะไรเลย"""

PY[21] = """NEW_USER = "ผู้ใช้ใหม่"
NEW_BOOK = "B99"

# เพิ่มหนังสือใหม่ที่ยังไม่มีใครชอบ + ให้ผู้ใช้ใหม่ชอบเล่มนั้นเป็นเล่มเดียว
run(driver, "MERGE (u:User {user: $user}) SET u.age = 18, u.group = 'ทดลอง', u.node_type = 'user'",
    user=NEW_USER)
run(driver, '''
    MERGE (b:Book {book_id: $book_id})
    SET b.title = $title, b.author = $author, b.genre = $genre,
        b.isbn = $isbn, b.year = $year, b.cover = $cover, b.node_type = 'book'
    WITH b MERGE (g:Genre {name: $genre}) MERGE (b)-[:IN_GENRE]->(g)
''', book_id=NEW_BOOK, title="One-Punch Man, Vol. 1", author="ONE", genre="การ์ตูน",
     isbn="9781421585642", year=2015, cover="one-punch-man-vol-1.jpg")
run(driver, '''
    MATCH (u:User {user: $user}) MATCH (b:Book {book_id: $book_id})
    MERGE (u)-[:LIKES]->(b)
''', user=NEW_USER, book_id=NEW_BOOK)

cold_votes = run(driver, Q_RECO_VOTES, user=NEW_USER)
cold_content = run(driver, Q_RECO_CONTENT, user=NEW_USER)
print("ผู้ใช้ใหม่ชอบแค่ 1 เล่ม: One-Punch Man, Vol. 1 (หมวดการ์ตูน) และยังไม่มีใครอื่นในระบบชอบเล่มนี้")
print("คำแนะนำจากสัญญาณเพื่อน :", [r["title"] for r in cold_votes] or "ว่างเปล่า (cold start จริง)")
print("คำแนะนำจากหมวดหนังสือ  :", [r["title"] for r in cold_content][:4])
show_cards(cold_content[:3],
           title="ระบบยังแนะนำได้ เพราะใช้โหนด Genre (หมวดการ์ตูน) เป็นสัญญาณสำรอง")"""

# ------------------------------------------------------------------ summary
MD[22] = """## 🧠 สรุป

**สิ่งที่ทำในงานนี้**
1. ออกแบบข้อมูลชุดของตัวเอง: 12 ผู้ใช้ × 28 หนังสือ (14 หมวด) × 51 ความชอบ + ภาพปกจริง
2. ออกแบบโครงสร้างกราฟ `(User)-[:LIKES]->(Book)-[:IN_GENRE]->(Genre)` และโหลดเข้า Neo4j
3. สร้างระบบแนะนำ 3 วิธี + วิธีผสม และ **แสดงภาพปกในผลการแนะนำ**
4. ตรวจ cold start, เทียบกับ baseline ยอดนิยม, และทดสอบว่าคำแนะนำอธิบายย้อนหลังได้

**ข้อดีของวิธีนี้**
- ไม่ต้องมีคะแนนรีวิว/ดาว แค่รู้ว่า "ใครชอบอะไร" ก็แนะนำได้
- อธิบายย้อนหลังได้ทุกคำแนะนำ (อ้างชื่อเพื่อนและหนังสือที่ชอบร่วมกัน)
- เพิ่มผู้ใช้/หนังสือใหม่แล้วได้คำแนะนำใหม่ทันที ไม่ต้องเทรนโมเดลใหม่ (ดูเซลล์ cold start)
- Cypher จัดการเรื่องนับซ้ำให้เองด้วย `count(DISTINCT ...)`

**ข้อจำกัด**
- ข้อมูล 51 ความชอบยังน้อย ถ้าเพิ่มความชอบจริงจากผู้ใช้จริงคำแนะนำจะแม่นขึ้น (ปัญหา sparsity)
- ยังไม่มีการให้คะแนนเป็นระดับ (1-5 ดาว) จึงถ่วงน้ำหนักได้แค่ความคล้ายของรสนิยม
- หมวดหนังสือใช้เพียง 14 หมวดกว้าง ๆ ถ้าใช้ tag ละเอียดขึ้นจะแนะนำได้ตรงใจกว่า

**ตัวระบบจริง (สาธิตการใช้งาน)**
แอป **Streamlit** ต่อ Neo4j ฐานข้อมูลเดียวกัน มี 5 หน้า: แนะนำหนังสือ (มีการ์ดภาพปก) ·
คลังหนังสือ 28 เล่ม · กราฟความสัมพันธ์ · เดโมสดเพิ่มความชอบแล้วเห็นคำแนะนำเปลี่ยนทันที · เกี่ยวกับระบบ
รันด้วยคำสั่ง `streamlit run app.py` — โค้ดอยู่ใน GitHub: https://github.com/Nasak16/book-recommender"""

PY[23] = """# เก็บกวาดข้อมูลทดลอง แล้วตรวจว่าฐานข้อมูลกลับสู่สภาพเดิม
run(driver, "MATCH (b:Book {book_id: $book_id}) DETACH DELETE b", book_id=NEW_BOOK)
run(driver, "MATCH (u:User {user: $user}) DETACH DELETE u", user=NEW_USER)

final = run(driver, Q_STATS)[0]
print("ลบผู้ใช้และหนังสือทดลองแล้ว — สถานะสุดท้าย:", final)
assert final == {"users": 12, "books": 28, "likes": 51, "genres": 14}, "ข้อมูลไม่กลับสู่สภาพเดิม"
print("ตรวจแล้ว: กลับมาครบ 12 ผู้ใช้ / 28 เล่ม / 51 ความชอบ เหมือนก่อนทดลอง cold start")
driver.close()
print("ปิดการเชื่อมต่อเรียบร้อย")"""


def build():
    cells = []
    for i in sorted(set(MD) | set(PY)):
        if i in MD:
            cells.append({"cell_type": "markdown", "metadata": {},
                          "source": MD[i].splitlines(keepends=True)})
        if i in PY:
            txt = PY[i]
            assert '"""' not in txt, "cell %d contains triple quotes" % i
            if TEST and i == 1:
                txt = (txt.replace('URI = "neo4j+s://<รหัส-instance>.databases.neo4j.io"',
                                   'URI = "bolt://127.0.0.1:7687"')
                          .replace('PASSWORD = getpass.getpass("Neo4j password: ")',
                                   'PASSWORD = "bookrec007"   # สำเนาทดสอบในเครื่อง'))
            cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                          "outputs": [], "source": txt.splitlines(keepends=True)})
    nb = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("wrote %s (%d cells)" % (OUT, len(cells)))


if __name__ == "__main__":
    build()
