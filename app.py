#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ระบบแนะนำหนังสือ (Book Recommender System) — Neo4j + Streamlit
รหัส 007 · วิชา … (งาน: พัฒนาระบบแนะนำเป็นระบบของตัวเอง)

รัน: streamlit run app.py
"""
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "data"))

st.set_page_config(page_title="ระบบแนะนำหนังสือ | Neo4j + Streamlit",
                   page_icon="📚", layout="wide")

# ---------------------------------------------------------------- engine
def _secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return os.environ.get(key, default)


@st.cache_resource(show_spinner="กำลังเชื่อมต่อฐานข้อมูลกราฟ…")
def get_engine():
    """พยายามใช้ Neo4j ก่อน ถ้าต่อไม่ได้ให้ใช้ backend สำรองในหน่วยความจำ (ข้อมูลชุดเดียวกัน)"""
    from recommender import BookRecommender
    from graph_fallback import from_files

    uri = _secret("NEO4J_URI", os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"))
    user = _secret("NEO4J_USER", os.environ.get("NEO4J_USER", "neo4j"))
    pw = _secret("NEO4J_PASSWORD", os.environ.get("NEO4J_PASSWORD", ""))
    try:
        eng = BookRecommender(uri, user, pw)
        eng.stats()                       # ยิงคำสั่งจริงเพื่อยืนยันว่าต่อได้
        return eng, "neo4j", f"Neo4j ({uri})"
    except Exception as e:
        err = f"{type(e).__name__}"
        return from_files(), "local", f"โหมดสำรองในหน่วยความจำ (ต่อ Neo4j ไม่ได้: {err})"


@st.cache_resource(show_spinner=False)
def thai_font():
    """โหลดฟอนต์ไทย Sarabun สำหรับวาดกราฟ (ไม่ต้องติดตั้งในเครื่อง/ไม่ต้องมีสิทธิ์ admin)"""
    import urllib.request
    from matplotlib import font_manager as fm
    d = os.path.join(ROOT, "assets", "fonts")
    os.makedirs(d, exist_ok=True)
    try:
        for fn in ("Sarabun-Regular.ttf", "Sarabun-Bold.ttf"):
            p = os.path.join(d, fn)
            if not os.path.exists(p):
                urllib.request.urlretrieve(
                    "https://github.com/google/fonts/raw/main/ofl/sarabun/" + fn, p)
            fm.fontManager.addfont(p)
        return fm.FontProperties(fname=os.path.join(d, "Sarabun-Regular.ttf")).get_name()
    except Exception:
        return "DejaVu Sans"


def cover_source(row):
    """ไฟล์ในโปรเจกต์ก่อน (ออฟไลน์ก็เห็นภาพ) ถ้าไม่มีค่อยใช้ URL"""
    rel = row.get("cover_file") or ""
    p = os.path.join(ROOT, rel)
    return p if rel and os.path.exists(p) else row.get("cover_url")


def show_cover(row, width=None):
    src = cover_source(row)
    if not src:
        st.info("ไม่มีภาพปก")
        return
    try:
        st.image(src, width=width)
    except Exception:
        st.image(row.get("cover_url"), width=width)


# ---------------------------------------------------------------- sidebar
engine, backend, backend_label = get_engine()
stat = engine.stats()

with st.sidebar:
    st.markdown("## 📚 ระบบแนะนำหนังสือ")
    st.caption("Neo4j (กราฟ) + Streamlit · รหัส 007")
    if backend == "neo4j":
        st.success("ฐานข้อมูล: " + backend_label, icon="🗄️")
    else:
        st.warning(backend_label, icon="⚠️")
    st.metric("ผู้ใช้ในระบบ", stat["users"])
    c1, c2, c3 = st.columns(3)
    c1.metric("หนังสือ", stat["books"])
    c2.metric("ความชอบ", stat["likes"])
    c3.metric("หมวด", stat["genres"])

    users = engine.users()
    who = st.selectbox("เลือกผู้ใช้ที่จะแนะนำหนังสือให้", users,
                       index=users.index("สมชาย") if "สมชาย" in users else 0)
    mode = st.radio("วิธีให้คะแนน", [
        "ถ่วงน้ำหนัก (Jaccard)",
        "นับโหวตเพื่อน",
        "ตามหมวดหนังสือ",
        "ผสม: เพื่อน + หมวด",
    ])
    top_n = st.slider("จำนวนที่แนะนำ", 1, 8, 3)
    st.divider()
    st.caption("อัลกอริทึม: Collaborative Filtering บนกราฟ (เดิน 3 hop) + "
               "Content-based ผ่านโหนด Genre")

MODE = {"ถ่วงน้ำหนัก (Jaccard)": "weighted", "นับโหวตเพื่อน": "votes",
        "ตามหมวดหนังสือ": "content", "ผสม: เพื่อน + หมวด": "hybrid"}[mode]

recs = {"weighted": engine.recommend_weighted, "votes": engine.recommend_votes,
        "content": engine.recommend_content, "hybrid": engine.recommend_hybrid}[MODE](who, top_n)

st.title("📚 ระบบแนะนำหนังสือ")
st.caption(f"คำแนะนำสำหรับ **{who}** · วิธี: **{mode}** · "
           f"แสดง {len(recs)} เล่มจาก {stat['books']} เล่มในระบบ")

tabs = st.tabs(["🎯 แนะนำหนังสือ", "📚 คลังหนังสือ", "🕸️ โครงสร้างกราฟ",
                "🧪 เดโมสด: เพิ่มความชอบ", "ℹ️ เกี่ยวกับระบบ"])

# ---------------------------------------------------------------- tab 1
with tabs[0]:
    liked = engine.liked_books(who)
    left, right = st.columns([1.05, 3])
    with left:
        st.markdown("#### ชอบอยู่แล้ว")
        st.caption(f"หนังสือตั้งต้นของ {who} — ใช้เป็นจุดเริ่มของกราฟ ({len(liked)} เล่ม)")
        for b in liked:
            with st.container(border=True):
                cc1, cc2 = st.columns([1, 2.4], vertical_alignment="center")
                with cc1:
                    show_cover(b, width=105)
                with cc2:
                    st.markdown(f"**{b['title']}**")
                    st.caption(b["author"] + " · " + ", ".join(b["genres"]))
    with right:
        if not recs:
            st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้ (ข้อมูลน้อยเกินไป — cold start)")
        else:
            st.markdown("#### หนังสือที่ระบบแนะนำ")
            st.caption(f"คัดจากหนังสือ {stat['books']} เล่มที่ {who} ยังไม่เคยอ่าน "
                       f"— เรียงตามคะแนนของวิธี “{mode}”")
            cols = st.columns(3)
            for i, r in enumerate(recs):
                with cols[i % 3]:
                    with st.container(border=True):
                        show_cover(r, width=180)
                        st.markdown(f"**{r['title']}**")
                        st.caption(f"{r['author']} · {r.get('genre','')}")
                        if MODE == "votes":
                            st.markdown(f"🔢 **{r['votes']} โหวต** จาก " +
                                        ", ".join(r["voters"]))
                        elif MODE == "content":
                            st.markdown(f"🏷️ ตรงหมวด **{r.get('genre','')}**")
                        else:
                            st.markdown(f"⭐ คะแนน **{r['score']}**")
                            if r.get("voters"):
                                st.caption("เพื่อนที่ชอบ: " + ", ".join(r["voters"]))
                        if r.get("via_books"):
                            st.caption("เพราะคุณชอบ: " + ", ".join(r["via_books"]))

    st.divider()
    st.markdown("#### ใครมีรสนิยมใกล้ " + who + " (Jaccard similarity)")
    sims = engine.similar_users(who)
    if sims:
        st.dataframe([{"ผู้ใช้": s["user"], "ชอบร่วมกัน (เล่ม)": s["common_count"],
                       "หนังสือที่ชอบร่วม": ", ".join(s["common"]),
                       "Jaccard": round(s["jaccard"], 3)} for s in sims],
                     hide_index=True)
    st.caption("Jaccard = |หนังสือที่ชอบร่วม| ÷ |หนังสือทั้งหมดของสองคน| "
               "→ ยิ่งใกล้ 1 ยิ่งรสนิยมเหมือนกัน น้ำหนักโหวตของคนนั้นยิ่งมาก")

# ---------------------------------------------------------------- tab 2
with tabs[1]:
    st.markdown("#### หนังสือทั้งหมดในระบบ")
    q = st.text_input("ค้นหา (ชื่อเรื่อง / นักเขียน / หมวด)", "")
    books = engine.books()
    if q:
        ql = q.lower()
        books = [b for b in books if ql in b["title"].lower()
                 or ql in b["author"].lower() or ql in b["genre"].lower()]
    st.caption(f"พบ {len(books)} เล่ม")
    for i in range(0, len(books), 5):
        cols = st.columns(5)
        for c, b in zip(cols, books[i:i + 5]):
            with c, st.container(border=True):
                show_cover(b, width=140)
                st.markdown(f"**{b['title']}**")
                st.caption(f"{b['author']}")
                st.caption(f"🏷️ {b['genre']} · ❤️ {b['likes']} คน")
    st.caption("ภาพปกทั้งหมดดึงจาก Open Library แล้วเก็บไว้ในโปรเจกต์ (assets/covers) "
               "จึงแสดงได้แม้ไม่มีอินเทอร์เน็ต")

# ---------------------------------------------------------------- tab 3
with tabs[2]:
    import graph_view

    st.markdown("#### กราฟความสัมพันธ์ (ผู้ใช้ ↔ หนังสือ)")
    st.caption("โหนดส้ม = ผู้ใช้ที่เลือก · ฟ้า = ผู้ใช้ที่รสนิยมใกล้ · เหลือง = หนังสือที่ชอบแล้ว · "
               "เขียว = หนังสือที่ระบบแนะนำ · เส้นประเขียว = เส้นทาง 3 hop ที่ระบบเดิน")
    fig = graph_view.draw(engine, who, recs, font=thai_font(),
                          title=f"กราฟคำแนะนำสำหรับ {who} · {mode}")
    st.pyplot(fig)
    import matplotlib.pyplot as plt
    plt.close(fig)

    st.markdown("##### เส้นทางการตัดสินใจของคำแนะนำอันดับ 1")
    if recs:
        r = recs[0]
        via = r.get("via_books") or [f"(หมวด {r.get('genre')})"]
        voters = r.get("voters") or ["(ตรงกับหมวดที่ชอบ)"]
        st.markdown(f"""
        ```
        {who} ──ชอบ──► {", ".join(via)}
                          │
                          ▼  มีคนชอบหนังสือเล่มเดียวกัน (รสนิยมใกล้กัน)
        {", ".join(voters)}
                          │
                          ▼  คนกลุ่มนี้ชอบเล่มอื่นที่ {who} ยังไม่ชอบ
        แนะนำ ► {r["title"]}
        ```
        """)

with tabs[3]:
    st.markdown("#### เดโมสด: เพิ่มหนังสือที่ชอบ แล้วดูว่าคำแนะนำเปลี่ยนทันที")
    st.caption("แก้ข้อมูลในฐานข้อมูลกราฟจริง แล้วคำนวณใหม่ทันที — ระบบไม่ต้องเทรนโมเดลใหม่")
    state = st.session_state.setdefault("before", None)
    allbooks = engine.books()
    cc1, cc2, cc3 = st.columns([2, 2, 1])
    with cc1:
        pick = st.selectbox("เลือกเล่มที่ " + who + " เพิ่มว่าชอบ",
                            [f"{b['book_id']} · {b['title']}" for b in allbooks])
    with cc2:
        st.write("ผลก่อน–หลังจะแสดงด้านล่าง")
    with cc3:
        if st.button("➕ เพิ่มความชอบ"):
            state = {"recs": engine.recommend_weighted(who, top_n),
                     "books": [b["title"] for b in engine.liked_books(who)]}
            st.session_state["before"] = state
            engine.add_like(who, pick.split(" · ")[0])
            st.rerun()
    if state:
        now = engine.recommend_weighted(who, top_n)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**ก่อนเพิ่ม**")
            st.dataframe([{"หนังสือ": r["title"], "คะแนน": r["score"]} for r in state["recs"]],
                         hide_index=True)
        with c2:
            st.markdown("**หลังเพิ่ม**")
            st.dataframe([{"หนังสือ": r["title"], "คะแนน": r["score"]} for r in now],
                         hide_index=True)
        changed = [r["title"] for r in now if r["title"] not in
                   [x["title"] for x in state["recs"]]]
        st.success("รายการที่โผล่ใหม่หลังเพิ่มข้อมูล: " + (", ".join(changed) or "ไม่เปลี่ยน"))
    st.divider()
    st.markdown("##### แก้ข้อมูลตั้งต้นของ " + who)
    for b in engine.liked_books(who):
        b1, b2 = st.columns([4, 1])
        b1.write(f"❤️ {b['title']}")
        if b2.button("ลบ", key="del_" + b["book_id"]):
            engine.remove_like(who, b["book_id"])
            st.rerun()

# ---------------------------------------------------------------- tab 5
with tabs[4]:
    st.markdown("#### ระบบนี้ทำงานอย่างไร")
    st.markdown(f"""
**สถาปัตยกรรม** — ข้อมูลเก็บใน **Neo4j** (ฐานข้อมูลกราฟ) มี 3 ชนิดโหนด:
`User` ({stat['users']} คน) · `Book` ({stat['books']} เล่ม) · `Genre` ({stat['genres']} หมวด)
และ 2 ชนิดความสัมพันธ์: `LIKES` ({stat['likes']} เส้น) และ `IN_GENRE`

**การทำงานของระบบแนะนำ (เดิน 3 hop)**
1. `(ผู้ใช้)-[:LIKES]->(หนังสือ)` — ดูว่าผู้ใช้คนนี้ชอบอะไร
2. `(หนังสือ)<-[:LIKES]-(คนอื่น)` — หาคนที่ชอบหนังสือเล่มเดียวกัน = รสนิยมใกล้กัน
3. `(คนอื่น)-[:LIKES]->(หนังสือเล่มใหม่)` — เก็บเล่มที่ผู้ใช้ยังไม่ชอบ แล้วจัดอันดับ

**สูตรให้คะแนน 2 แบบ**
- นับโหวต: `คะแนน = จำนวนคนที่ชอบเล่มนั้น` (1 คน = 1 เสียง)
- ถ่วงน้ำหนัก: `คะแนน = Σ Jaccard(เรา, คนนั้น)` โดย
  `Jaccard = |ชอบร่วม| ÷ |หนังสือทั้งหมดของสองคน|`
- Hybrid: รวมคะแนนเพื่อน (normalize แล้ว) 60% กับสัญญาณหมวดหนังสือ 40%
  → หนังสือที่ทั้งเพื่อนและหมวดตรงจะได้คะแนนสูงสุด

**ทำไมต้องมีโหนด Genre** — ช่วยแก้ปัญหา cold start: ผู้ใช้ใหม่ที่ยังมีข้อมูลน้อย
ยังได้รับคำแนะนำจากหมวดที่ตัวเองชอบได้ แม้จะยังไม่มีความคล้ายกับใครเลย
    """)
    st.markdown("##### สถานะการเชื่อมต่อ")
    st.write(f"- backend ที่ใช้อยู่: **({'Neo4j' if backend == 'neo4j' else 'หน่วยความจำสำรอง'})** "
             f"· {backend_label}")
    st.write("- ตรวจความถูกต้องของสอง backend: `py -3.13 tools/consistency_test.py <uri> "
             "neo4j <password>` → ผลตรงกัน 12 คน × 5 การตรวจ")

st.divider()
st.caption("ระบบแนะนำหนังสือ · จัดทำโดย รหัส 007 · ข้อมูลและภาพปกจาก Open Library (ฟรี) · "
           "กราฟ: Neo4j · ส่วนติดต่อผู้ใช้: Streamlit")