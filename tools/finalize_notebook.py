#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""รวมร่างสุดท้ายของโน๊ตบุ๊กส่งงาน

1) สร้าง 2 ร่างจากข้อมูลชุดเดียว: ร่างส่งจริง (Neo4j Aura + getpass) และร่างทดสอบ (Neo4j ในเครื่อง)
2) รันร่างทดสอบเพื่อเก็บ output จริง
3) ย้าย output จากร่างทดสอบไปใส่ร่างส่งจริง "ทีละเซลล์" (เซลล์เชื่อมต่อยังเป็นของเรา เพื่อไม่ให้รหัสหลุด)
4) บันทึกเป็น notebooks/BookRecommender_Neo4j_007.ipynb + สำเนาไว้ Downloads
"""
import json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
OUT = os.path.join(ROOT, "tools", "out")
FINAL = os.path.join(ROOT, "notebooks", "BookRecommender_Neo4j_007.ipynb")


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr[-1500:]); sys.exit("คำสั่งล้มเหลว: %s" % " ".join(args))


sh(PY, os.path.join(ROOT, "tools", "build_notebook.py"), "--test")
sh(PY, os.path.join(ROOT, "tools", "build_notebook.py"))
sh(PY, os.path.join(ROOT, "tools", "run_notebook.py"),
   os.path.join(OUT, "BookRecommender_Neo4j_007.ipynb"),
   os.path.join(OUT, "executed.ipynb"))

real = json.load(open(FINAL, encoding="utf-8"))   # ร่างส่งจริง (เขียนโดย build ที่ไม่ใช่ --test)
ran = json.load(open(os.path.join(OUT, "executed.ipynb"), encoding="utf-8"))
assert len(real["cells"]) == len(ran["cells"]), "จำนวนเซลล์ไม่ตรงกัน"
merged = html_cards = 0
for a, b in zip(real["cells"], ran["cells"]):
    assert a["cell_type"] == b["cell_type"], "ชนิดเซลล์ไม่ตรงกัน"
    if a["cell_type"] == "code":
        a["outputs"], a["execution_count"] = b["outputs"], b["execution_count"]
        merged += 1
        html_cards += sum(1 for o in b["outputs"] if o.get("data", {}).get("text/html"))
os.makedirs(os.path.dirname(FINAL), exist_ok=True)
json.dump(real, open(FINAL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

dl = os.path.join(os.path.expanduser("~"), "Downloads", "BookRecommender_Neo4j_007.ipynb")
shutil.copy(FINAL, dl)
conn = [c for c in real["cells"] if c["cell_type"] == "code"][0]
print("\nรวม output แล้ว %d เซลล์ (การ์ดภาพ %d ก้อน)" % (merged, html_cards))
print("เซลล์เชื่อมต่อยังเป็นของเรา :", "neo4j+s://" in "".join(conn["source"]),
      "| ใช้ getpass:", "getpass" in "".join(conn["source"]))
bad = [i for i, c in enumerate(real["cells"])
       if c["cell_type"] == "code" and ("bookrec007" in "".join(c["source"])
                                        or "127.0.0.1" in "".join(c["source"]))]
print("ตรวจไม่ให้มีรหัส/ที่อยู่เครื่องทดสอบหลุด :", "ไม่พบ" if not bad else bad)
print("ไฟล์ส่ง:", FINAL)
print("สำเนา:", dl)
