#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robust cover fetch: retries + PIL validity check. Used to repair placeholder covers."""
import io, json, os, sys, time, urllib.request
from PIL import Image

UA = {"User-Agent": "book-recommender-007/1.0 (coursework)"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def fetch(url, tries=4):
    for i in range(tries):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            im = Image.open(io.BytesIO(raw)); im.load()
            if len(raw) < 2500:
                raise ValueError("too small %d B" % len(raw))
            return raw, im
        except Exception as e:
            print("   retry %d %s: %s" % (i + 1, url[-46:], type(e).__name__))
            time.sleep(2 + 2 * i)
    return None, None


def variance(im):                      # placeholder/plain cover detector
    g = im.convert("L").resize((64, 96))
    px = list(g.getdata())
    m = sum(px) / len(px)
    return (sum((p - m) ** 2 for p in px) / len(px)) ** 0.5


def grab(url, path):
    raw, im = fetch(url)
    if raw is None:
        if os.path.exists(path):
            os.remove(path)
        return None
    open(path, "wb").write(raw)
    return round(variance(im), 1)


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1], encoding="utf-8"))
    for path, url in jobs:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        v = grab(url, path)
        print(("OK   var=%-6s " % v if v else "FAIL          ") + path)
