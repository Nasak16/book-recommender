#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างหน้า index รวมงานทุกชิ้น (GitHub Pages) จาก repo จริงของบัญชี

    py -3.13 tools/build_index.py
ดึงข้อมูล repo สดจาก GitHub API แล้วเขียน index.html + README.md ลงโฟลเดอร์ปลายทาง
"""
import json, os, subprocess, sys

DEST = r"C:\Users\USER\Documents\GitHub\homework"
GID = "247492673b9b3a74dd39bd7d442d398c"
COLAB = f"https://colab.research.google.com/gist/Nasak16/{GID}/BookRecommender_Neo4j_007.ipynb"

# คำอธิบาย/หมวดของแต่ละงาน (เขียนเอง — repo บน GitHub ไม่มี description)
INFO = {
    "book-recommender": ("ระบบแนะนำหนังสือ (Neo4j + Streamlit)", "ฐานข้อมูล",
                         "งานนี้: ระบบแนะนำหนังสือบนฐานข้อมูลกราฟ Neo4j 12 คน × 28 เล่ม "
                         "แสดงภาพปกจริง มีทั้งโน๊ตบุ๊ก Colab และเว็บแอปสาธิต"),
    "GrapDB1": ("GraphBook — ระบบแนะนำหนังสือด้วยกราฟ (งานตัวอย่างในวิชา)", "ฐานข้อมูล",
                "Streamlit + Neo4j Aura: (Student)-[:BORROWED]->(Book) + เพื่อน/หมวด/คะแนนดาว "
                "สูตร hybrid แบบ heuristic"),
    "grafanaDB": ("Dashboard แสดงข้อมูลด้วย Grafana + InfluxDB", "ฐานข้อมูล",
                  "รวบรวมข้อมูลอนุกรมเวลาและทำแดชบอร์ดติดตามสถานะ"),
    "iot-security-dashboard": ("โปรเจกต์จบ: ระบบรักษาความปลอดภัยบ้าน IoT", "IoT",
                               "ESP32 + ESP32-CAM + Firebase + Grafana + LINE Notify "
                               "(repo ส่วนตัว)"),
    "titanic-ml-project": ("Machine Learning: ทำนายผู้รอดชีวิต Titanic", "Machine Learning",
                           "EDA + โมเดลทำนาย และเว็บแอป Streamlit สำหรับทดลองทำนาย"),
    "web_model": ("ทำนายผลการเรียนของนักเรียน", "Machine Learning",
                  "สร้างโมเดลจาก student performance dataset แล้ว deploy ด้วย Streamlit"),
    "forest": ("Machine Learning: จำแนกประเภทข้อมูลป่า", "Machine Learning",
               "ฝึกโมเดลจำแนกประเภทพร้อมวัดผลความแม่นยำ"),
    "mental_ML": ("Machine Learning: วิเคราะห์ข้อมูลสุขภาพจิต", "Machine Learning",
                  "สำรวจข้อมูลและสร้างโมเดลทำนายกลุ่มเสี่ยง"),
    "Boston_ML": ("Machine Learning: ทำนายราคาบ้าน (Boston Housing)", "Machine Learning",
                  "งาน Regression พื้นฐานพร้อมกราฟวิเคราะห์"),
    "DTreeHeart": ("Decision Tree: ทำนายความเสี่ยงโรคหัวใจ", "Decision Tree",
                   "สร้างโมเดล Decision Tree และวัดผลด้วย confusion matrix"),
    "DTwine": ("Decision Tree: จำแนกชนิดไวน์", "Decision Tree",
               "ฝึก Decision Tree กับข้อมูลไวน์และเปรียบเทียบผล"),
    "DecisionTree_ML3": ("Decision Tree (งานที่ 3)", "Decision Tree",
                         "ฝึกสร้างโมเดลต้นไม้ตัดสินใจและปรับพารามิเตอร์"),
    "KNN": ("KNN: จำแนกข้อมูลด้วยเพื่อนบ้านใกล้สุด", "Machine Learning",
            "ฝึกอัลกอริทึม K-Nearest Neighbors พร้อมเลือกค่า k ที่เหมาะสม"),
}
CAT_COLOR = {"ฐานข้อมูล": "#38BDF8", "IoT": "#FF8833", "Machine Learning": "#34D399",
             "Decision Tree": "#FBBF24"}
LATEST = "book-recommender"


def repos():
    out = subprocess.run(["gh", "repo", "list", "Nasak16", "--limit", "60", "--json",
                          "name,visibility,pushedAt,url,primaryLanguage,description"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out)


def main():
    rs = repos()
    rows = []
    for r in rs:
        th, cat, desc = INFO.get(r["name"], (r["name"], "งานอื่น ๆ", r["description"] or ""))
        rows.append({"name": r["name"], "th": th, "cat": cat, "desc": desc,
                     "url": r["url"], "vis": "สาธารณะ" if r["visibility"] == "PUBLIC" else "ส่วนตัว",
                     "lang": (r.get("primaryLanguage") or {}).get("name") or "-",
                     "date": (r.get("pushedAt") or "")[:10],
                     "latest": r["name"] == LATEST})
    rows.sort(key=lambda r: (not r["latest"], r["date"]), reverse=False)
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows.sort(key=lambda r: not r["latest"])            # งานล่าสุดขึ้นก่อน

    cats = ["ทั้งหมด"] + sorted({r["cat"] for r in rows}, key=lambda c: list(CAT_COLOR).index(c)
                                if c in CAT_COLOR else 99)

    def card(r):
        link = (f'<a class="btn" href="{r["url"]}" target="_blank" rel="noopener">เปิด repo →</a>'
                if r["vis"] == "สาธารณะ" else
                '<span class="btn btn-off">repo ส่วนตัว (ให้สิทธิ์เมื่อขอ)</span>')
        extra = ""
        if r["latest"]:
            extra = (f'<div class="extra">'
                     f'<a href="{COLAB}" target="_blank" rel="noopener">📓 โน๊ตบุ๊ก Colab</a>'
                     f'<a href="{r["url"]}/tree/main/slides" target="_blank" rel="noopener">'
                     f'📊 สไลด์นำเสนอ (.pptx/.pdf)</a></div>')
        return f"""      <article class="card" data-cat="{r['cat']}">
        <div class="tag" style="--c:{CAT_COLOR.get(r['cat'], '#9FB0CB')}">{r['cat']}</div>
        <h3>{r['th']}</h3>
        <p>{r['desc']}</p>
        <div class="meta"><code>{r['name']}</code> · {r['lang']} · อัปเดต {r['date']} · {r['vis']}</div>
{extra}        {link}
      </article>"""

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>รวมงานทั้งหมด · รหัส 007</title>
<style>
  :root {{ --bg:#0E1626; --card:#172136; --card2:#1E2A45; --line:#2B3A5C; --text:#E9EFFA;
           --muted:#9FB0CB; --orange:#FF8833; --cyan:#38BDF8; --green:#34D399; --yellow:#FBBF24; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
          font-family:"Leelawadee UI","Noto Sans Thai",system-ui,sans-serif; line-height:1.55; }}
  header {{ padding:56px 24px 30px; border-bottom:1px solid var(--line);
            background:linear-gradient(180deg,#111c30,#0E1626); }}
  .wrap {{ max-width:1180px; margin:0 auto; }}
  .kicker {{ color:var(--orange); font-weight:700; font-size:14px; letter-spacing:.5px; }}
  h1 {{ font-size:40px; margin:8px 0 6px; }}
  .sub {{ color:var(--muted); font-size:16px; max-width:820px; }}
  .stats {{ display:flex; gap:14px; flex-wrap:wrap; margin-top:22px; }}
  .stat {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
           padding:12px 18px; min-width:130px; }}
  .stat b {{ display:block; font-size:24px; color:var(--cyan); }}
  .stat span {{ font-size:12px; color:var(--muted); }}
  .latest {{ max-width:1180px; margin:28px auto 0; border:1px solid var(--line); border-radius:16px;
             background:linear-gradient(135deg,#16233c,#131c2e); padding:22px 24px; }}
  .latest h2 {{ margin:0 0 6px; font-size:22px; color:var(--yellow); }}
  .latest p {{ margin:0 0 14px; color:var(--muted); }}
  .latest a {{ color:var(--cyan); text-decoration:none; margin-right:18px; font-weight:600; }}
  .latest a:hover {{ text-decoration:underline; }}
  .filters {{ max-width:1180px; margin:30px auto 0; display:flex; gap:10px; flex-wrap:wrap; }}
  .chip {{ border:1px solid var(--line); background:var(--card); color:var(--muted);
           padding:8px 15px; border-radius:999px; cursor:pointer; font-size:13.5px; }}
  .chip.on {{ color:#0E1626; background:var(--orange); border-color:var(--orange); font-weight:700; }}
  main {{ max-width:1180px; margin:0 auto; padding:22px 24px 70px;
          display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:18px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:20px;
           display:flex; flex-direction:column; gap:8px; }}
  .card:hover {{ border-color:#3d5480; }}
  .tag {{ align-self:flex-start; font-size:11.5px; font-weight:700; color:var(--c,#9FB0CB);
          border:1px solid color-mix(in srgb,var(--c,#9FB0CB) 45%, transparent);
          background:color-mix(in srgb,var(--c,#9FB0CB) 12%, transparent);
          padding:3px 10px; border-radius:999px; }}
  h3 {{ margin:4px 0 0; font-size:18px; }}
  p {{ margin:0; color:var(--muted); font-size:14px; }}
  .meta {{ font-size:12px; color:#7d8dab; }}
  .meta code {{ color:var(--cyan); }}
  .extra {{ display:flex; gap:14px; flex-wrap:wrap; }}
  .extra a {{ font-size:13px; color:var(--yellow); text-decoration:none; font-weight:600; }}
  .btn {{ margin-top:auto; align-self:flex-start; background:var(--orange); color:#0E1626;
          text-decoration:none; font-weight:700; font-size:13.5px; padding:9px 16px;
          border-radius:9px; }}
  .btn-off {{ background:var(--card2); color:var(--muted); font-weight:600; }}
  footer {{ border-top:1px solid var(--line); color:var(--muted); font-size:13px;
            padding:24px; text-align:center; }}
  a {{ color:var(--cyan); }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="kicker">GITHUB HOMEWORK INDEX · รหัส 007</div>
    <h1>รวมงานทั้งหมดของเรา</h1>
    <p class="sub">หน้านี้รวมทุกชิ้นงานที่ส่งใน GitHub — คลิกการ์ดเพื่อเปิด repo ของแต่ละงาน
      งานล่าสุดคือ “ระบบแนะนำหนังสือ” ซึ่งมีทั้งโน๊ตบุ๊กอธิบายวิธีทำ เว็บแอปสาธิต และสไลด์นำเสนอ</p>
    <div class="stats">
      <div class="stat"><b>{len(rows)}</b><span>งานทั้งหมด</span></div>
      <div class="stat"><b>{len([r for r in rows if r['vis'] == 'สาธารณะ'])}</b><span>repo สาธารณะ</span></div>
      <div class="stat"><b>{len(cats) - 1}</b><span>หมวดงาน</span></div>
      <div class="stat"><b>{max(r['date'] for r in rows)}</b><span>อัปเดตล่าสุด</span></div>
    </div>
  </div>
</header>

<section class="latest">
  <div class="wrap">
    <h2>⭐ งานล่าสุด: ระบบแนะนำหนังสือ (Neo4j + Streamlit)</h2>
    <p>ระบบแนะนำที่พัฒนาขึ้นเอง ข้อมูลของเราเอง 12 คน × 28 เล่ม × 51 ความชอบ — แสดงภาพปกหนังสือจริงในผลการแนะนำ</p>
    <a href="{COLAB}" target="_blank" rel="noopener">📓 เปิดโน๊ตบุ๊กใน Colab</a>
    <a href="https://github.com/Nasak16/book-recommender" target="_blank" rel="noopener">💻 โค้ดระบบ</a>
    <a href="https://github.com/Nasak16/book-recommender/tree/main/slides" target="_blank" rel="noopener">📊 สไลด์ .pptx / .pdf</a>
    <a href="https://github.com/Nasak16/book-recommender/tree/main/notebooks" target="_blank" rel="noopener">📒 ไฟล์ .ipynb สำหรับส่ง</a>
  </div>
</section>

<div class="filters">
  {"".join(f'<button class="chip{" on" if c == "ทั้งหมด" else ""}" data-f="{c}">{c}</button>' for c in cats)}
</div>

<main>
{chr(10).join(card(r) for r in rows)}
</main>

<footer>
  จัดทำโดย รหัส 007 · หน้านี้สร้างจากข้อมูล repo จริงด้วยสคริปต์ (build_index.py) ·
  ภาพปกหนังสือและข้อมูลจาก Open Library (ฟรี)
</footer>

<script>
  document.querySelectorAll('.chip').forEach(function (b) {{
    b.addEventListener('click', function () {{
      document.querySelectorAll('.chip').forEach(function (x) {{ x.classList.remove('on'); }});
      b.classList.add('on');
      var f = b.dataset.f;
      document.querySelectorAll('.card').forEach(function (c) {{
        c.style.display = (f === 'ทั้งหมด' || c.dataset.cat === f) ? '' : 'none';
      }});
    }});
  }});
</script>
</body>
</html>
"""
    os.makedirs(DEST, exist_ok=True)
    with open(os.path.join(DEST, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(DEST, "README.md"), "w", encoding="utf-8") as f:
        f.write("# รวมงานทั้งหมด (Homework Index) — รหัส 007\n\n"
                "หน้าเว็บ index: **https://nasak16.github.io/homework/**\n\n"
                "| งาน | หมวด | repo | อัปเดต |\n|---|---|---|---|\n" +
                "".join(f"| {r['th']} | {r['cat']} | [{r['name']}]({r['url']}) | {r['date']} |\n"
                        for r in rows) +
                "\n## งานล่าสุด: ระบบแนะนำหนังสือ (Neo4j + Streamlit)\n\n"
                f"- โน๊ตบุ๊ก Colab: {COLAB}\n"
                "- โค้ด + สไลด์: https://github.com/Nasak16/book-recommender\n")
    print("เขียน index.html (%d งาน) และ README.md ->" % len(rows), DEST)
    for r in rows:
        print("   %-26s %-20s %s" % (r["name"], r["cat"], r["date"]))


if __name__ == "__main__":
    main()
