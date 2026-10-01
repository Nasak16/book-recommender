#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backend สำรอง: คิดคำแนะนำในหน่วยความจำด้วยตรรกะเดียวกับ Cypher ใน recommender.py

ใช้เมื่อ "ไม่มี Neo4j" (เช่น ตอน deploy บน Streamlit Cloud ที่ยังไม่ได้ตั้งค่า Aura)
ตรรกะการให้คะแนนถูกเขียนให้ตรงกับ Cypher ทีละบรรทัด และมี tools/consistency_test.py
ไว้พิสูจน์ว่า 2 backend ให้ผล top-5 เหมือนกันทุกคน
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


class LocalGraphRecommender:
    def __init__(self, users, books, likes):
        self.users_list = [dict(u) for u in users]
        self.books_list = [dict(b) for b in books]
        self.by_id = {b["book_id"]: b for b in self.books_list}
        self.likes = {u["user"]: set() for u in self.users_list}
        for u, b in likes:
            self.likes.setdefault(u, set()).add(b)

    # ---------- ข้อมูล ----------
    def close(self):
        pass

    def stats(self):
        return {"users": len(self.users_list), "books": len(self.books_list),
                "likes": sum(len(v) for v in self.likes.values()),
                "genres": len({b["genre"] for b in self.books_list})}

    def users(self):
        return sorted(self.likes)

    def books(self):
        out = []
        for b in self.books_list:
            d = dict(b)
            d["likes"] = sum(1 for v in self.likes.values() if b["book_id"] in v)
            d.pop("cover_i", None)
            out.append(d)
        return sorted(out, key=lambda r: (-r["likes"], r["title"]))

    def liked_books(self, user):
        return sorted([
            {"book_id": b["book_id"], "title": b["title"], "author": b["author"],
             "cover_url": b["cover_url"], "cover_file": b["cover_file"],
             "genres": [b["genre"]]}
            for bid in self.likes.get(user, ())
            for b in [self.by_id[bid]]
        ], key=lambda r: r["title"])

    # ---------- ความคล้าย ----------
    def similar_users(self, user):
        mine = self.likes.get(user, set())
        rows = []
        for other, theirs in self.likes.items():
            if other == user:
                continue
            common = sorted(mine & theirs)
            if not common:
                continue
            union = len(mine) + len(theirs) - len(common)
            rows.append({"user": other, "common_count": len(common), "common": common,
                         "n_mine": len(mine), "n_theirs": len(theirs),
                         "jaccard": len(common) / union})
        return sorted(rows, key=lambda r: (-r["jaccard"], r["user"]))

    # ---------- คำแนะนำ ----------
    def recommend_votes(self, user, top_n=5):
        return self._score(user)[:top_n]

    def _score(self, user):
        mine = self.likes.get(user, set())
        votes, voters, via, score = {}, {}, {}, {}
        for other, theirs in self.likes.items():
            if other == user:
                continue
            common = mine & theirs
            if not common:
                continue
            jac = len(common) / (len(mine) + len(theirs) - len(common))
            for bid in theirs - mine:
                votes[bid] = votes.get(bid, 0) + 1
                voters.setdefault(bid, []).append(other)
                via.setdefault(bid, set()).update(common)
                score[bid] = score.get(bid, 0.0) + jac
        rows = []
        for bid in votes:
            b = self.by_id[bid]
            rows.append({
                "book_id": bid, "title": b["title"], "author": b["author"], "genre": b["genre"],
                "cover_url": b["cover_url"], "cover_file": b["cover_file"],
                "votes": votes[bid], "voters": sorted(voters[bid]),
                "score": round(score[bid], 3),
                "via_books": sorted(self.by_id[x]["title"] for x in via[bid]),
                "genres": [b["genre"]],
            })
        return sorted(rows, key=lambda r: (-r["score"], r["title"]))

    def recommend_weighted(self, user, top_n=5):
        return self._score(user)[:top_n]

    def recommend_content(self, user, top_n=5):
        mine = self.likes.get(user, set())
        genres = {self.by_id[b]["genre"] for b in mine}
        rows = []
        for bid, b in self.by_id.items():
            if bid in mine or b["genre"] not in genres:
                continue
            rows.append({"book_id": bid, "title": b["title"], "author": b["author"],
                         "genre": b["genre"], "cover_url": b["cover_url"],
                         "cover_file": b["cover_file"], "genres": [b["genre"]],
                         "genre_hits": 1})
        return sorted(rows, key=lambda r: (-r["genre_hits"], r["title"]))[:top_n]

    def recommend_hybrid(self, user, top_n=5, weight_collab=0.6):
        collab = {r["book_id"]: r for r in self._score(user)}
        content = {r["book_id"]: r for r in self.recommend_content(user, top_n=999)}
        max_c = max([r["score"] for r in collab.values()] or [0]) or 1
        max_g = max([r["genre_hits"] for r in content.values()] or [0]) or 1
        out = {}
        for bid in set(collab) | set(content):
            c, g = collab.get(bid, {}), content.get(bid, {})
            base = c or g
            out[bid] = {
                "book_id": bid, "title": base["title"], "author": base["author"],
                "genre": base.get("genre"), "cover_url": base.get("cover_url"),
                "cover_file": base.get("cover_file"),
                "score": round(weight_collab * c.get("score", 0) / max_c
                               + (1 - weight_collab) * g.get("genre_hits", 0) / max_g, 3),
                "collab": round(c.get("score", 0), 3),
                "genre_hits": g.get("genre_hits", 0),
                "voters": c.get("voters", []), "via_books": c.get("via_books", []),
                "because": ("เพื่อน + หมวดที่คุณชอบ" if c and g else
                            "เพื่อนที่รสนิยมใกล้ชอบ" if c else "หมวดหนังสือที่คุณชอบ"),
            }
        return sorted(out.values(), key=lambda r: (-r["score"], r["title"]))[:top_n]

    def popular(self, top_n=5):
        out = []
        for b in self.books_list:
            n = sum(1 for v in self.likes.values() if b["book_id"] in v)
            out.append({"book_id": b["book_id"], "title": b["title"], "likes": n,
                        "cover_url": b["cover_url"], "cover_file": b["cover_file"]})
        return sorted(out, key=lambda r: (-r["likes"], r["title"]))[:top_n]

    def graph_edges(self):
        edges = []
        for user, books in self.likes.items():
            for bid in books:
                edges.append({"a_type": "User", "a_label": user, "a_id": None,
                              "rel": "LIKES", "b_type": "Book",
                              "b_label": self.by_id[bid]["title"], "b_id": bid})
        for b in self.books_list:
            edges.append({"a_type": "Book", "a_label": b["title"], "a_id": b["book_id"],
                          "rel": "IN_GENRE", "b_type": "Genre", "b_label": b["genre"],
                          "b_id": None})
        return edges

    # ---------- แก้ข้อมูลชั่วคราว (เดโม) ----------
    def add_like(self, user, book_id):
        self.likes.setdefault(user, set()).add(book_id)
        if user not in [u["user"] for u in self.users_list]:
            self.users_list.append({"user": user, "age": None, "group": "ผู้ใช้ใหม่"})

    def remove_like(self, user, book_id):
        self.likes.get(user, set()).discard(book_id)


def from_files():
    """อ่านข้อมูลชุดเดียวกับที่โหลดเข้า Neo4j"""
    import seed_data
    users, books, likes = seed_data.graph_data()
    return LocalGraphRecommender(users, books, likes)
