#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างหน้า index รวมงานทุกชิ้น (GitHub Pages) จาก repo จริงของบัญชี

    py -3.13 tools/build_index.py
ดึงข้อมูล repo สดจาก GitHub API แล้วเขียน index.html + README.md ลงโฟลเดอร์ปลายทาง
ดีไซน์: hub การ์ด dark-neon (ไอคอน + ชื่อ + คำอธิบาย + ปุ่มเปิดเต็มความกว้าง)
"""
import json, os, subprocess, sys

DEST = r"C:\Users\USER\Documents\GitHub\homework"
GID = "8667b219bbff8253335ec78f78b5c79e"
COLAB = f"https://colab.research.google.com/gist/Nasak16/{GID}/PhoneRecommender_Neo4j_007.ipynb"
APP_REPO = "https://github.com/Nasak16/phone-recommender"

# คำอธิบาย/หมวดของแต่ละงาน (เขียนเอง — repo บน GitHub ไม่มี description)
INFO = {
    "phone-recommender": ("ระบบแนะนำมือถือ (Neo4j + Streamlit)", "ฐานข้อมูล",
                          "งานนี้: ระบบแนะนำมือถือบนฐานข้อมูลกราฟ Neo4j — 12 คน × 23 รุ่น × 38 ความสนใจ "
                          "+ 38 คะแนนดาว (RATED) · เว็บแอป 6 หน้า (Dashboard / Recommendations / "
                          "Phone Search / Like & Rate / Graph Explorer / Admin & Setup) · "
                          "5 วิธีให้คะแนน · แสดงภาพสินค้าจริงในการ์ดทุกใบ · มีโน๊ตบุ๊ก Colab + สไลด์ 16 หน้า"),
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
    "homework": ("หน้ารวมงานทั้งหมด (Hub — หน้านี้เอง)", "รวมงาน",
                 "หน้าเว็บรวมลิงก์งานทุกชิ้นไว้ที่เดียว (GitHub Pages) สร้างจากข้อมูล repo จริง "
                 "ด้วยสคริปต์ build_index.py อยู่ใน repo นี้"),
}
CAT_COLOR = {"ฐานข้อมูล": "#38D0FF", "IoT": "#FF8833", "Machine Learning": "#34D399",
             "Decision Tree": "#FBBF24", "รวมงาน": "#A78BFA"}
CAT_ICON = {"ฐานข้อมูล": "🗄️", "IoT": "📡", "Machine Learning": "🤖", "Decision Tree": "🌳",
            "รวมงาน": "🧭"}
# ไอคอนเฉพาะงาน (ถ้าไม่มีใช้ไอคอนตามหมวด)
ICON = {"phone-recommender": "📱", "book-recommender": "📚", "GrapDB1": "📚", "grafanaDB": "📈",
        "iot-security-dashboard": "📡", "titanic-ml-project": "🚢", "web_model": "🎓",
        "forest": "🌲", "mental_ML": "🧠", "Boston_ML": "🏠", "DTreeHeart": "❤️",
        "DTwine": "🍷", "DecisionTree_ML3": "🌳", "KNN": "🔵"}
LATEST = "phone-recommender"
HUB_REPO = "homework"

# การ์ดเด่น 4 ใบ (แบบเดียวกับหน้า hub ตัวอย่าง) — ชี้ไปชิ้นงานของเราเอง
FEATURES = [
    ("🕸️", "โครงสร้างข้อมูล",
     "ออกแบบและสร้างฐานข้อมูลกราฟ Neo4j เอง: โหนดผู้ใช้ / รุ่นมือถือ / ยี่ห้อ / ระดับราคา "
     "ความสัมพันธ์ LIKES + RATED (คะแนนดาว) — ชุดข้อมูลที่สร้างเอง 12 คน × 23 รุ่น × 38 ความสนใจ",
     f"{APP_REPO}/tree/main/data", "เปิดดูข้อมูล →"),
    ("📊", "วิเคราะห์ข้อมูล",
     "โน๊ตบุ๊ก Colab อธิบายวิธีทำทีละขั้น: สร้างกราฟ → เขียน Cypher ถามข้อมูล → ทดลองสูตรแนะนำ "
     "5 วิธี (Jaccard / โหวตเพื่อน / คะแนนดาว) พร้อมผลรันจริงในเซลล์",
     COLAB, "เปิดโน๊ตบุ๊ก →"),
    ("📱", "ระบบแนะนำ (ของเรา)",
     "เว็บแอป Streamlit ต่อ Neo4j จริง 6 หน้า: ให้คะแนนแล้วระบบแนะนำรุ่นที่ใช่ · ค้นหารุ่น · "
     "สำรวจกราฟ · แสดงภาพสินค้าจริงในการ์ดทุกใบ (โค้ด + วิธีรันอยู่ใน README)",
     APP_REPO, "เปิดโค้ด/แอป →"),
    ("🎨", "สไลด์นำเสนอโปรเจกต์",
     "สรุปแนวคิด วิธีทำ และผลลัพธ์ทั้งหมดเป็น 16 สไลด์ (.pptx/.pdf) พร้อมหน้าสาธิตการใช้งาน "
     "สำหรับนำเสนอหน้าชั้นเรียน",
     f"{APP_REPO}/tree/main/slides", "เปิดสไลด์ →"),
]          # repo ของหน้านี้เอง — ใส่เป็นการ์ดปิดท้าย grid


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
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows.sort(key=lambda r: r["name"] == HUB_REPO)      # การ์ด hub ปิดท้าย grid
    rows.sort(key=lambda r: not r["latest"])            # งานล่าสุดขึ้นก่อนสุด

    cats = ["ทั้งหมด"] + sorted({r["cat"] for r in rows}, key=lambda c: list(CAT_COLOR).index(c)
                                if c in CAT_COLOR else 99)

    def card(r):
        c = CAT_COLOR.get(r["cat"], "#9FB0CB")
        ic = ICON.get(r["name"]) or CAT_ICON.get(r["cat"], "📁")
        if r["vis"] == "สาธารณะ":
            link = f'<a class="btn" href="{r["url"]}" target="_blank" rel="noopener">เปิด repo →</a>'
        else:
            link = '<span class="btn btn-off">repo ส่วนตัว (ให้สิทธิ์เมื่อขอ)</span>'
        return f"""    <article class="card" data-cat="{r['cat']}">
      <div class="ic" style="--c:{c}">{ic}</div>
      <div class="tag" style="--c:{c}">{r['cat']}</div>
      <h3>{r['th']}</h3>
      <p>{r['desc']}</p>
      <div class="meta"><code>{r['name']}</code> · {r['lang']} · อัปเดต {r['date']} · {r['vis']}</div>
      {link}
    </article>"""

    features = "".join(
        f'''    <article class="fcard">
      <div class="ic" style="--c:#38D0FF">{ic}</div>
      <h3>{t}</h3>
      <p>{d}</p>
      <a class="btn" href="{u}" target="_blank" rel="noopener">{label}</a>
    </article>''' for ic, t, d, u, label in FEATURES)

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>รวมงานทั้งหมด · รหัส 007</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700;800&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
  :root {{ --bg:#05070F; --card:#0B1220; --line:#1B3A63; --text:#E6F1FF; --muted:#8FA8C8;
           --cyan:#38D0FF; --blue:#2563EB; --violet:#A78BFA; --pink:#F472B6;
           --orange:#FF8833; --green:#34D399; --yellow:#FBBF24; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; color:var(--text); line-height:1.6;
          font-family:"Prompt","Leelawadee UI","Noto Sans Thai",system-ui,sans-serif;
          background:
            radial-gradient(1100px 520px at 12% -8%, rgba(56,208,255,.13), transparent 60%),
            radial-gradient(900px 460px at 88% -12%, rgba(167,139,250,.12), transparent 60%),
            var(--bg); }}
  a {{ color:var(--cyan); }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:0 22px; }}
  header {{ padding:64px 0 26px; text-align:center; }}
  .kicker {{ font-family:Orbitron,sans-serif; font-size:12.5px; letter-spacing:3px;
             color:var(--cyan); text-transform:uppercase; opacity:.9; }}
  h1 {{ font-size:clamp(30px,4.8vw,54px); line-height:1.18; margin:12px 0 10px; font-weight:800;
        background:linear-gradient(90deg,#7DE3FF,#38D0FF 38%,#A78BFA 72%,#F472B6);
        -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
  .sub {{ color:var(--muted); font-size:16.5px; max-width:860px; margin:0 auto; }}
  .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px;
            margin:30px 0 6px; }}
  .stat {{ background:linear-gradient(180deg,#0C1424,#0B1220); border:1px solid var(--line);
           border-radius:14px; padding:14px 16px; }}
  .stat b {{ display:block; font-size:25px; color:var(--cyan);
             font-family:Orbitron,sans-serif; letter-spacing:.5px; }}
  .stat span {{ font-size:12.5px; color:var(--muted); }}
  .feat-h {{ text-align:center; font-size:19px; margin:34px 0 0; color:#E6F1FF; }}
  .feat-h span {{ color:var(--cyan); }}
  .feat {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(252px,1fr)); gap:16px;
           margin:18px 0 6px; }}
  .fcard {{ background:linear-gradient(180deg,#0C1424,#0A1120); border:1px solid var(--line);
            border-radius:18px; padding:20px 18px 16px; display:flex; flex-direction:column; gap:10px;
            min-height:262px; box-shadow:0 4px 15px rgba(0,120,255,.10);
            transition:transform .25s ease, border-color .25s ease, box-shadow .25s ease; }}
  .fcard:hover {{ transform:translateY(-4px); border-color:#00B4FF;
                  box-shadow:0 10px 28px rgba(0,180,255,.26); }}
  .fcard .ic {{ width:52px; height:52px; font-size:26px; }}
  .fcard h3 {{ font-size:19px; }}
  .latest {{ border:1px solid var(--line); border-radius:18px; padding:24px; margin:26px 0 6px;
             background:linear-gradient(135deg,rgba(37,99,235,.16),rgba(5,7,15,.25));
             box-shadow:0 6px 26px rgba(0,140,255,.12); }}
  .latest h2 {{ margin:0 0 8px; font-size:21px; color:var(--yellow); }}
  .latest p {{ margin:0 0 16px; color:var(--muted); font-size:15px; }}
  .acts {{ display:flex; gap:12px; flex-wrap:wrap; }}
  .acts a {{ text-decoration:none; font-weight:700; font-size:13.5px; padding:10px 16px;
             border-radius:10px; color:#04121F;
             background:linear-gradient(90deg,var(--blue),var(--cyan)); }}
  .acts a.ghost {{ background:transparent; color:var(--cyan); border:1px solid var(--line); }}
  .acts a:hover {{ filter:brightness(1.1); }}
  .filters {{ display:flex; gap:10px; flex-wrap:wrap; margin:34px 0 4px; }}
  .chip {{ font-family:inherit; font-size:13.5px; border:1px solid var(--line); background:var(--card);
           color:var(--muted); padding:8px 16px; border-radius:999px; cursor:pointer; }}
  .chip:hover {{ border-color:#2C5B93; color:var(--text); }}
  .chip.on {{ color:#04121F; font-weight:800; border-color:transparent;
              background:linear-gradient(90deg,var(--blue),var(--cyan)); }}
  main {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:18px;
          padding:18px 0 70px; }}
  .card {{ background:linear-gradient(180deg,#0C1424,#0A1120); border:1px solid var(--line);
           border-radius:18px; padding:18px 18px 16px; display:flex; flex-direction:column; gap:9px;
           min-height:266px; box-shadow:0 4px 15px rgba(0,120,255,.10);
           transition:transform .25s ease, border-color .25s ease, box-shadow .25s ease; }}
  .card:hover {{ transform:translateY(-4px); border-color:#00B4FF;
                 box-shadow:0 10px 28px rgba(0,180,255,.26); }}
  .ic {{ width:48px; height:48px; border-radius:13px; display:grid; place-items:center;
         font-size:23px; background:color-mix(in srgb,var(--c,#38D0FF) 12%, transparent);
         border:1px solid color-mix(in srgb,var(--c,#38D0FF) 42%, transparent); }}
  .tag {{ align-self:flex-start; font-size:11.5px; font-weight:700; color:var(--c,#9FB0CB);
          border:1px solid color-mix(in srgb,var(--c,#9FB0CB) 45%, transparent);
          background:color-mix(in srgb,var(--c,#9FB0CB) 12%, transparent);
          padding:3px 10px; border-radius:999px; }}
  h3 {{ margin:2px 0 0; font-size:18px; line-height:1.35; }}
  p {{ margin:0; color:var(--muted); font-size:14px; }}
  .meta {{ font-size:12px; color:#9FB0CB; margin-top:2px; }}
  .meta code {{ color:var(--cyan); }}
  .extra {{ display:flex; gap:14px; flex-wrap:wrap; }}
  .extra a {{ font-size:13px; color:var(--yellow); text-decoration:none; font-weight:600; }}
  .extra a:hover {{ text-decoration:underline; }}
  .btn {{ margin-top:auto; display:block; text-align:center; text-decoration:none; font-weight:800;
          font-size:13.5px; padding:11px 16px; border-radius:11px; color:#04121F;
          background:linear-gradient(90deg,var(--blue),var(--cyan));
          box-shadow:0 4px 14px rgba(56,208,255,.22); }}
  .btn:hover {{ filter:brightness(1.12); }}
  .btn-off {{ background:transparent; color:var(--muted); font-weight:600;
              border:1px solid var(--line); box-shadow:none; }}
  footer {{ border-top:1px solid var(--line); color:var(--muted); font-size:13px;
            padding:26px 22px; text-align:center; }}
</style>
</head>
<body>
<header class="wrap">
  <div class="kicker">Homework Hub · รหัส 007</div>
  <h1>รวมงานทั้งหมดของเรา</h1>
  <p class="sub">ศูนย์รวมงานที่ส่งใน GitHub ทุกชิ้น — กดการ์ดเพื่อเปิด repo ของแต่ละงาน ·
    งานล่าสุดคือ “ระบบแนะนำมือถือ (Neo4j + Streamlit)” ซึ่งมีโน๊ตบุ๊กอธิบายวิธีทำ เว็บแอปสาธิต และสไลด์นำเสนอ</p>
  <div class="stats">
    <div class="stat"><b>{len(rows)}</b><span>งานทั้งหมด</span></div>
    <div class="stat"><b>{len([r for r in rows if r['vis'] == 'สาธารณะ'])}</b><span>repo สาธารณะ</span></div>
    <div class="stat"><b>{len(cats) - 1}</b><span>หมวดงาน</span></div>
    <div class="stat"><b>{max(r['date'] for r in rows)}</b><span>อัปเดตล่าสุด</span></div>
  </div>
</header>

<div class="wrap">
  <h2 class="feat-h">🧩 <span>ชิ้นงานหลักของโปรเจกต์นี้</span> — ระบบแนะนำมือถือ (Neo4j + Streamlit)</h2>
  <div class="feat">
{features}
  </div>

  <div class="filters">
    {"".join(f'<button class="chip{" on" if c == "ทั้งหมด" else ""}" data-f="{c}">{c}</button>' for c in cats)}
  </div>
</div>

<main class="wrap">
{chr(10).join(card(r) for r in rows)}
</main>

<footer>
  จัดทำโดย รหัส 007 · หน้านี้อยู่ใน repo <a href="https://github.com/Nasak16/homework">Nasak16/homework</a>
  และสร้างจากข้อมูล repo จริงด้วยสคริปต์ (build_index.py)
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
        f.write("# รวมงานทั้งหมด (Homework Hub) — รหัส 007\n\n"
                "หน้าเว็บ hub: **https://nasak16.github.io/homework/**\n\n"
                "| งาน | หมวด | repo | อัปเดต |\n|---|---|---|---|\n" +
                "".join(f"| {r['th']} | {r['cat']} | [{r['name']}]({r['url']}) | {r['date']} |\n"
                        for r in rows) +
                "\n## งานล่าสุด: ระบบแนะนำมือถือ (Neo4j + Streamlit)\n\n"
                f"- โน๊ตบุ๊ก Colab: {COLAB}\n"
                f"- โค้ด + สไลด์: {APP_REPO}\n")
    print("เขียน index.html (%d งาน) และ README.md ->" % len(rows), DEST)
    for r in rows:
        print("   %-26s %-20s %s" % (r["name"], r["cat"], r["date"]))


if __name__ == "__main__":
    main()
