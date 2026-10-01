# ตั้ง Neo4j ในเครื่องสำหรับทดสอบ (Windows, ไม่ต้องใช้ Docker / ไม่ต้องสิทธิ์ admin)

สคริปต์นี้ใช้ไฟล์ที่ **Neo4j Desktop 2** โหลดไว้แล้วในเครื่อง (`~/.Neo4jDesktop2/Cache/dbmss`)
จึงไม่ต้องดาวน์โหลดอะไรใหม่ และไม่ต้องติดตั้ง service ใด ๆ

```bash
# 1) คัดลอก dist ที่แคชไว้ไปไว้ในโฟลเดอร์ชั่วคราว (Cache ต้นทางห้ามแก้)
NX="$TMPDIR/nx"; rm -rf "$NX"; mkdir -p "$NX"
cp -r "$USERPROFILE/.Neo4jDesktop2/Cache/dbmss/neo4j-enterprise-2026.08.1/." "$NX/"

# 2) ใช้ JRE ที่แถมมากับ Desktop (Java 21) — Java 8 ของเครื่องรันตัวนี้ไม่ได้
export JAVA_HOME='C:\Users\USER\.Neo4jDesktop2\Cache\runtime\zulu21.50.19-ca-jre21.0.11-win_x64'
export PATH="/c/Users/USER/.Neo4jDesktop2/Cache/runtime/zulu21.50.19-ca-jre21.0.11-win_x64/bin:$PATH"
export NEO4J_ACCEPT_LICENSE_AGREEMENT=yes      # รุ่น enterprise ต้องมีตัวนี้ก่อนสตาร์ท

# 3) ตั้งรหัสผ่าน (ต้องตั้งก่อนสตาร์ทครั้งแรกเท่านั้น)
cd "$NX/bin" && ./neo4j-admin.bat dbms set-initial-password bookrec007

# 4) สตาร์ท — รอข้อความ "Started." ในไฟล์ logs/neo4j.log (ไม่ใช่รอที่ port)
./neo4j.bat console
```

จากนั้นโหลดข้อมูลและตรวจสอบ:

```bash
py -3.13 tools/load_neo4j.py bolt://127.0.0.1:7687 neo4j bookrec007
py -3.13 tools/consistency_test.py bolt://127.0.0.1:7687 neo4j bookrec007
```

## หยุดและเก็บกวาด
```bash
PID=$(netstat -ano | grep ":8777" | grep LISTENING | awk '{print $NF}' | head -1)   # ตัวอย่างสำหรับ streamlit
powershell -NoProfile -Command "Stop-Process -Id <PID ของ java> -Force"
rm -rf "$TMPDIR/nx"        # ลบ dist 458 MB ที่คัดลอกไว้
```

## หมายเหตุที่เจอจริง
- **Neo4j 2026.x ต้องใช้ Java 21** — ถ้าใช้ Java 8 ของเครื่องจะได้
  `UnsupportedClassVersionError: class file version 65.0`
- **รันสคริปต์ซ้ำ** ต้อง `MATCH (n) DETACH DELETE n` ก่อน (สคริปต์โหลดข้อมูลทำให้แล้ว)
  ไม่งั้นข้อมูลเดิมจะค้างและตัวเลขจะไม่ตรง
- ถ้าใช้ **Aura** แทน ให้ใส่ URI แบบ `neo4j+s://<id>.databases.neo4j.io` และรหัสผ่านที่ตั้งตอนสร้าง instance
