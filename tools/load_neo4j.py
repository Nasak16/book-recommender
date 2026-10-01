#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""โหลดข้อมูลหนังสือ/ผู้ใช้/ความชอบ เข้า Neo4j แล้วพิมพ์ผลตรวจสอบ

    py -3.13 tools/load_neo4j.py bolt://127.0.0.1:7687 neo4j <password>
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))

from recommender import BookRecommender            # noqa: E402
import seed_data                                   # noqa: E402

URI = sys.argv[1] if len(sys.argv) > 1 else "bolt://127.0.0.1:7687"
USER = sys.argv[2] if len(sys.argv) > 2 else "neo4j"
PW = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("NEO4J_PASSWORD", "")

users, books, likes = seed_data.graph_data()
rec = BookRecommender(URI, USER, PW)
print("เชื่อมต่อ:", URI)
print("server:", rec.driver.get_server_info().agent)
rec.reset()
rec.ensure_constraints()
rec.import_data(users, books, likes)

st = rec.stats()
print("ข้อมูลในกราฟ:", st)

target = "สมชาย"
print(f"\n--- {target} ชอบ (จาก Cypher) ---")
for b in rec.liked_books(target):
    print("   ", b["book_id"], b["title"], "|", ",".join(b["genres"]))

print(f"\n--- ใครรสนิยมใกล้ {target} (Jaccard) ---")
for r in rec.similar_users(target):
    print(f"    {r['user']:8s} ชอบร่วม {r['common_count']} เล่ม {r['common']} | "
          f"Jaccard {r['jaccard']:.3f}")

print(f"\n--- แนะนำให้ {target}: นับโหวต ---")
for r in rec.recommend_votes(target, 5):
    print(f"    {r['title'][:38]:40s} votes={r['votes']} voters={r['voters']}")

print(f"\n--- แนะนำให้ {target}: ถ่วงน้ำหนัก Jaccard ---")
for r in rec.recommend_weighted(target, 5):
    print(f"    {r['title'][:38]:40s} score={r['score']} voters={r['voters']}")

print(f"\n--- แนะนำให้ {target}: ตามหมวดหนังสือ ---")
for r in rec.recommend_content(target, 5):
    print(f"    {r['title'][:38]:40s} hits={r['genre_hits']} genres={r['genres']}")

print(f"\n--- แนะนำให้ {target}: ผสมสองสัญญาณ (hybrid) ---")
for r in rec.recommend_hybrid(target, 5):
    print(f"    {r['title'][:38]:40s} score={r['score']} collab={r['collab']} "
          f"genre={r['genre_hits']} เพราะ: {r['because']}")

print("\n--- ยอดนิยม (baseline) ---")
for r in rec.popular():
    print(f"    {r['title'][:38]:40s} likes={r['likes']}")

print("\n--- ทุกคนได้อะไร (top-3 weighted) ---")
for u in rec.users():
    top = rec.recommend_weighted(u, 3)
    print(f"    {u:8s} -> " + ", ".join(f"{r['title'][:24]}({r['score']})" for r in top))

rec.close()
