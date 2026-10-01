#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""แกนของระบบแนะนำหนังสือ (Book Recommender Engine) — คุยกับ Neo4j ด้วย Cypher

ใช้ร่วมกันทั้ง Streamlit app และสคริปต์ทดสอบ เพื่อให้ผลลัพธ์ตรงกันเสมอ
รูปแบบกราฟ:  (User)-[:LIKES]->(Book)-[:IN_GENRE]->(Genre)
"""
from collections import OrderedDict

from neo4j import GraphDatabase

# ---- คำสั่ง Cypher ทั้งหมดของระบบ (ใช้ซ้ำได้ทุกที่) ----
Q_STATS = """
MATCH (u:User) WITH count(u) AS users
MATCH (b:Book) WITH users, count(b) AS books
MATCH ()-[r:LIKES]->() WITH users, books, count(r) AS likes
MATCH (g:Genre) RETURN users, books, likes, count(g) AS genres
"""

Q_RESET = "MATCH (n) DETACH DELETE n"

Q_CONSTRAINTS = [
    "CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.user IS UNIQUE",
    "CREATE CONSTRAINT book_id IF NOT EXISTS FOR (b:Book) REQUIRE b.book_id IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
]

Q_LOAD_USERS = """
UNWIND $rows AS row
MERGE (u:User {user: row.user})
SET u.age = row.age, u.group = row.group,
    u.node_type = 'user'
RETURN count(u) AS users
"""

Q_LOAD_BOOKS = """
UNWIND $rows AS row
MERGE (b:Book {book_id: row.book_id})
SET b.title = row.title, b.author = row.author, b.genre = row.genre,
    b.isbn = row.isbn, b.year = row.year, b.cover_url = row.cover_url,
    b.cover_file = row.cover_file, b.node_type = 'book'
MERGE (g:Genre {name: row.genre})
MERGE (b)-[:IN_GENRE]->(g)
RETURN count(b) AS books
"""

Q_LOAD_LIKES = """
UNWIND $rows AS row
MATCH (u:User {user: row.user})
MATCH (b:Book {book_id: row.book_id})
MERGE (u)-[:LIKES]->(b)
RETURN count(*) AS likes
"""

Q_LIKED_BOOKS = """
MATCH (u:User {user: $user})-[:LIKES]->(b:Book)
OPTIONAL MATCH (b)-[:IN_GENRE]->(g:Genre)
RETURN b.book_id AS book_id, b.title AS title, b.author AS author,
       b.cover_url AS cover_url, b.cover_file AS cover_file,
       collect(g.name) AS genres
ORDER BY b.title
"""

Q_SIMILAR_USERS = """
MATCH (me:User {user: $user})-[:LIKES]->(shared:Book)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.book_id) AS common
MATCH (me)-[:LIKES]->(mine:Book)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Book)
WITH other, common, n_mine, count(DISTINCT theirs) AS n_theirs
RETURN other.user AS user, size(common) AS common_count, common,
       n_mine, n_theirs,
       toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard
ORDER BY jaccard DESC, user
"""

# 1 เสียง/คน/เล่ม (Cypher รวมผลแบบไม่นับซ้ำให้เอง เพราะ aggregate บนคู่ที่แตกต่างกัน)
Q_RECO_VOTES = """
MATCH (me:User {user: $user})-[:LIKES]->(shared:Book)<-[:LIKES]-(other:User)-[:LIKES]->(rec:Book)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.book_id AS book_id, rec.title AS title, rec.author AS author,
       rec.genre AS genre, rec.cover_url AS cover_url, rec.cover_file AS cover_file,
       count(DISTINCT other) AS votes,
       collect(DISTINCT other.user) AS voters,
       collect(DISTINCT shared.title) AS via_books
ORDER BY votes DESC, title
"""

# ให้คะแนนถ่วงน้ำหนักด้วย Jaccard similarity ของคนที่ชอบ (คนรสนิยมใกล้มีน้ำหนักมากกว่า)
Q_RECO_WEIGHTED = """
MATCH (me:User {user: $user})-[:LIKES]->(shared:Book)<-[:LIKES]-(other:User)
WITH me, other, collect(DISTINCT shared.book_id) AS common
MATCH (me)-[:LIKES]->(mine:Book)
WITH me, other, common, count(DISTINCT mine) AS n_mine
MATCH (other)-[:LIKES]->(theirs:Book)
WITH me, other, common, n_mine, count(DISTINCT theirs) AS n_theirs
WITH me, other, toFloat(size(common)) / (n_mine + n_theirs - size(common)) AS jaccard, common
MATCH (other)-[:LIKES]->(rec:Book)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.book_id AS book_id, rec.title AS title, rec.author AS author,
       rec.genre AS genre, rec.cover_url AS cover_url, rec.cover_file AS cover_file,
       round(sum(jaccard) * 1000) / 1000.0 AS score,
       count(DISTINCT other) AS votes,
       collect(DISTINCT other.user) AS voters,
       collect(DISTINCT rec.genre) AS genres
ORDER BY score DESC, title
"""

# อีกสัญญาณหนึ่ง: หมวดที่ผู้ใช้ชอบ (content-based ผ่านโหนด Genre)
Q_RECO_CONTENT = """
MATCH (me:User {user: $user})-[:LIKES]->(:Book)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec:Book)
WHERE NOT (me)-[:LIKES]->(rec)
RETURN rec.book_id AS book_id, rec.title AS title, rec.author AS author, rec.genre AS genre,
       rec.cover_url AS cover_url, rec.cover_file AS cover_file,
       collect(DISTINCT g.name) AS genres,
       count(DISTINCT g) AS genre_hits
ORDER BY genre_hits DESC, title
"""

Q_POPULAR = """
MATCH (b:Book)<-[:LIKES]-(u:User)
RETURN b.book_id AS book_id, b.title AS title, b.cover_url AS cover_url,
       b.cover_file AS cover_file, count(u) AS likes
ORDER BY likes DESC, title LIMIT 5
"""

Q_GRAPH_EDGES = """
MATCH (a)-[r:LIKES|IN_GENRE]->(b)
RETURN labels(a)[0] AS a_type, coalesce(a.user, a.title, a.name) AS a_label, a.book_id AS a_id,
       type(r) AS rel,
       labels(b)[0] AS b_type, coalesce(b.title, b.name, b.user) AS b_label, b.book_id AS b_id
"""


class BookRecommender:
    """โหมด TH: เชื่อมต่อ Neo4j + ให้คำแนะนำที่อธิบายย้อนหลังได้"""

    def __init__(self, uri, user="neo4j", password=None, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def _run(self, query, **params):
        with self.driver.session(database=self.database) as s:
            return [r.data() for r in s.run(query, **params)]

    # ---------- ข้อมูลตั้งต้น ----------
    def reset(self):
        self._run(Q_RESET)

    def ensure_constraints(self):
        for q in Q_CONSTRAINTS:
            self._run(q)

    def import_data(self, users, books, likes):
        self._run(Q_LOAD_USERS, rows=[{"user": u["user"], "age": u["age"], "group": u["group"]}
                                      for u in users])
        self._run(Q_LOAD_BOOKS, rows=books)
        self._run(Q_LOAD_LIKES, rows=[{"user": u, "book_id": b} for u, b in likes])

    def stats(self):
        row = self._run(Q_STATS)[0]
        return {"users": row["users"], "books": row["books"],
                "likes": row["likes"], "genres": row["genres"]}

    def users(self):
        return [r["user"] for r in
                self._run("MATCH (u:User) RETURN u.user AS user ORDER BY u.user")]

    def books(self):
        return self._run("""
            MATCH (b:Book) OPTIONAL MATCH (b)-[:IN_GENRE]->(g:Genre)
            OPTIONAL MATCH (b)<-[:LIKES]-(u:User)
            RETURN b.book_id AS book_id, b.title AS title, b.author AS author,
                   b.genre AS genre, b.isbn AS isbn, b.year AS year,
                   b.cover_url AS cover_url, b.cover_file AS cover_file,
                   count(DISTINCT u) AS likes
            ORDER BY likes DESC, title""")

    # ---------- คำถามพื้นฐาน ----------
    def liked_books(self, user):
        return self._run(Q_LIKED_BOOKS, user=user)

    def similar_users(self, user):
        return self._run(Q_SIMILAR_USERS, user=user)

    # ---------- คำแนะนำ 3 วิธี ----------
    def recommend_votes(self, user, top_n=5):
        return self._run(Q_RECO_VOTES, user=user)[:top_n]

    def recommend_weighted(self, user, top_n=5):
        return self._run(Q_RECO_WEIGHTED, user=user)[:top_n]

    def recommend_content(self, user, top_n=5):
        return self._run(Q_RECO_CONTENT, user=user)[:top_n]

    def recommend_hybrid(self, user, top_n=5, weight_collab=0.6):
        """รวมสัญญาณเพื่อน (ถ่วง Jaccard) กับสัญญาณหมวดหนังสือ แล้ว normalize เป็น 0-1"""
        collab = {r["book_id"]: r for r in self._run(Q_RECO_WEIGHTED, user=user)}
        content = {r["book_id"]: r for r in self._run(Q_RECO_CONTENT, user=user)}
        max_c = max([r["score"] for r in collab.values()] or [0]) or 1
        max_g = max([r["genre_hits"] for r in content.values()] or [0]) or 1
        out = OrderedDict()
        for bid in set(collab) | set(content):
            c = collab.get(bid, {})
            g = content.get(bid, {})
            base = c or g
            out[bid] = {
                "book_id": bid, "title": base["title"], "author": base["author"],
                "genre": base.get("genre"), "cover_url": base.get("cover_url"),
                "cover_file": base.get("cover_file"),
                "score": round(weight_collab * c.get("score", 0) / max_c
                               + (1 - weight_collab) * g.get("genre_hits", 0) / max_g, 3),
                "collab": round(c.get("score", 0), 3),
                "genre_hits": g.get("genre_hits", 0),
                "voters": c.get("voters", []),
                "via_books": c.get("via_books", []),
                "because": ("เพื่อน + หมวดที่คุณชอบ" if c and g else
                            "เพื่อนที่รสนิยมใกล้ชอบ" if c else "หมวดหนังสือที่คุณชอบ"),
            }
        return sorted(out.values(), key=lambda r: (-r["score"], r["title"]))[:top_n]

    def popular(self, top_n=5):
        return self._run(Q_POPULAR)[:top_n]

    def graph_edges(self):
        return self._run(Q_GRAPH_EDGES)

    # ---------- เดโมสด: เพิ่มความชอบแล้วคำแนะนำเปลี่ยนทันที ----------
    def add_like(self, user, book_id):
        self._run("""
            MERGE (u:User {user: $user}) SET u.node_type = 'user'
            WITH u MATCH (b:Book {book_id: $book_id})
            MERGE (u)-[:LIKES]->(b)""", user=user, book_id=book_id)

    def remove_like(self, user, book_id):
        self._run("""
            MATCH (u:User {user: $user})-[r:LIKES]->(b:Book {book_id: $book_id})
            DELETE r""", user=user, book_id=book_id)
