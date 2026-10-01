#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ทดสอบว่า backend Neo4j (Cypher) กับ backend สำรอง (หน่วยความจำ) ให้ผลตรงกัน

    py -3.13 tools/consistency_test.py bolt://127.0.0.1:7687 neo4j <password>

ตรวจ 5 อย่างต่อผู้ใช้ 1 คน × 12 คน: similar_users, votes, weighted, content, hybrid
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "data"))

from recommender import BookRecommender      # noqa: E402
from graph_fallback import from_files        # noqa: E402

uri = sys.argv[1] if len(sys.argv) > 1 else "bolt://127.0.0.1:7687"
user = sys.argv[2] if len(sys.argv) > 2 else "neo4j"
pw = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("NEO4J_PASSWORD", "")

db = BookRecommender(uri, user, pw)
loc = from_files()
print("Neo4j :", db.driver.get_server_info().agent)
print("stats ตรงกัน:", db.stats() == loc.stats(), db.stats(), loc.stats())

fails = []
for u in db.users():
    # 1) คนที่รสนิยมใกล้
    a = [(r["user"], round(r["jaccard"], 3), r["common_count"]) for r in db.similar_users(u)]
    b = [(r["user"], round(r["jaccard"], 3), r["common_count"]) for r in loc.similar_users(u)]
    if a != b:
        fails.append((u, "similar_users", a, b))
    # 2) นับโหวต (เทียบแผนที่ title -> votes ทั้งชุด)
    va = {r["title"]: r["votes"] for r in db.recommend_votes(u, 999)}
    vb = {r["title"]: r["votes"] for r in loc.recommend_votes(u, 999)}
    if va != vb:
        fails.append((u, "votes", va, vb))
    # 3) ถ่วงน้ำหนัก Jaccard (top-5 + คะแนน)
    wa = [(r["title"], r["score"]) for r in db.recommend_weighted(u, 5)]
    wb = [(r["title"], r["score"]) for r in loc.recommend_weighted(u, 5)]
    if wa != wb:
        fails.append((u, "weighted", wa, wb))
    # 4) ตามหมวดหนังสือ
    ca = [r["title"] for r in db.recommend_content(u, 5)]
    cb = [r["title"] for r in loc.recommend_content(u, 5)]
    if ca != cb:
        fails.append((u, "content", ca, cb))
    # 5) ผสมสองสัญญาณ
    ha = [(r["title"], r["score"], r["because"]) for r in db.recommend_hybrid(u, 5)]
    hb = [(r["title"], r["score"], r["because"]) for r in loc.recommend_hybrid(u, 5)]
    if ha != hb:
        fails.append((u, "hybrid", ha, hb))

if fails:
    print("\nไม่ตรงกัน %d จุด:" % len(fails))
    for u, what, a, b in fails:
        print(f"  {u} / {what}\n     neo4j : {a}\n     local : {b}")
    sys.exit(1)
print("\nผลตรงกันครบทุกข้อ (12 คน × 5 การตรวจ) — backend สำรองเชื่อถือได้")
db.close()
