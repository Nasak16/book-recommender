#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""รันทุก code cell ของโน๊ตบุ๊กในเนมสเปซเดียว แล้วฝัง output จริงกลับลงไฟล์

    py -3.13 tools/run_notebook.py <src.ipynb> <dst.ipynb>

- ตัดบรรทัด `!pip ...` / `%magic` (รันบน Jupyter เท่านั้น) ออกก่อนรัน
- stdout -> output แบบ stream
- สิ่งที่ `display(...)` (HTML การ์ดหนังสือ) -> output แบบ display_data text/html
- นิพจน์บรรทัดสุดท้าย -> execute_result (เหมือน Jupyter)
ใช้คู่กับ tools/verify_ipynb_cells.py (ตรวจว่ารันผ่านจริง)
"""
import argparse, ast, contextlib, io, json, pathlib, sys

CAPTURED = []


def _install_display_hook():
    """ดักจับ display() เพื่อเก็บ HTML ของการ์ดหนังสือลง output ของเซลล์"""
    import IPython.display as D

    def fake_display(*objs, **kw):
        for o in objs:
            if hasattr(o, "data") and hasattr(o, "_repr_html_"):
                CAPTURED.append(("text/html", o.data))
            elif hasattr(o, "_repr_html_"):
                CAPTURED.append(("text/html", o._repr_html_()))
            else:
                CAPTURED.append(("text/plain", repr(o)))

    D.display = fake_display
    try:                       # ให้ `from IPython.display import display` ในเซลล์ได้ตัวที่ดักไว้
        import builtins
        builtins.display = fake_display
    except Exception:
        pass


def run_cell(src, ns):
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("!", "%")))
    if not code.strip():
        return "", None
    tree = ast.parse(code + "\n")
    body, last = tree.body, None
    if body and isinstance(body[-1], ast.Expr):
        last = body.pop()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if body:
            exec(compile(ast.Module(body=body, type_ignores=[]), "<cell>", "exec"), ns)
        res = None
        if last is not None:
            res = eval(compile(ast.Expression(last.value), "<cell>", "eval"), ns)
    return buf.getvalue(), (None if res is None else
                            (res if isinstance(res, str) else repr(res)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    a = ap.parse_args()
    _install_display_hook()

    nb = json.loads(pathlib.Path(a.src).read_text(encoding="utf-8"))
    ns = {"__name__": "__main__"}
    n = 0
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        n += 1
        source = "".join(cell["source"])
        CAPTURED.clear()
        text, rep = run_cell(source, ns)
        outputs = []
        if text:
            outputs.append({"name": "stdout", "output_type": "stream",
                            "text": text.splitlines(keepends=True)})
        for mime, data in CAPTURED:
            outputs.append({"data": {mime: data}, "metadata": {},
                            "output_type": "display_data"})
        if rep is not None:
            outputs.append({"data": {"text/plain": rep.splitlines(keepends=True)},
                            "execution_count": n, "metadata": {},
                            "output_type": "execute_result"})
        cell["outputs"] = outputs
        cell["execution_count"] = n
        head = source.strip().splitlines()[0][:64] if source.strip() else "(ว่าง)"
        html = sum(1 for m, _ in CAPTURED if m == "text/html")
        print("[%2d] %-66s out=%3dB html=%d %s"
              % (n, head, len(text), html, ("=> " + (rep or "")[:40]) if rep else ""))
    pathlib.Path(a.dst).write_text(json.dumps(nb, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    print("รันครบ %d เซลล์ -> %s" % (n, a.dst))


if __name__ == "__main__":
    main()
