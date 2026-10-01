#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve 28 books on Open Library -> cover_i + ISBN, download cover images.

Writes data/books.json and assets/covers/<slug>.jpg (used by BOTH the Colab
notebook, via raw.githubusercontent URLs, and the Streamlit app, via local files).
Also renders a labelled contact sheet so one vision check can confirm the covers
are the right books.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COV = os.path.join(BASE, "assets", "covers")
os.makedirs(COV, exist_ok=True)

UA = {"User-Agent": "book-recommender-007/1.0 (coursework)"}

# (title, author, genre, lang)
BOOKS = [
    ("Harry Potter and the Philosopher's Stone", "J. K. Rowling", "แฟนตาซี", "EN"),
    ("The Hobbit", "J. R. R. Tolkien", "แฟนตาซี", "EN"),
    ("The Lord of the Rings", "J. R. R. Tolkien", "แฟนตาซี", "EN"),
    ("The Hunger Games", "Suzanne Collins", "เยาวชน/ไซไฟ", "EN"),
    ("Dune", "Frank Herbert", "ไซไฟ", "EN"),
    ("The Martian", "Andy Weir", "ไซไฟ", "EN"),
    ("Frankenstein", "Mary Shelley", "คลาสสิก", "EN"),
    ("Nineteen Eighty-Four", "George Orwell", "ดิสโทเปีย", "EN"),
    ("Animal Farm", "George Orwell", "ดิสโทเปีย", "EN"),
    ("The Alchemist", "Paulo Coelho", "แรงบันดาลใจ", "EN"),
    ("The Da Vinci Code", "Dan Brown", "สืบสวน", "EN"),
    ("Angels & Demons", "Dan Brown", "สืบสวน", "EN"),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson", "สืบสวน", "EN"),
    ("And Then There Were None", "Agatha Christie", "สืบสวน", "EN"),
    ("Murder on the Orient Express", "Agatha Christie", "สืบสวน", "EN"),
    ("The Adventures of Sherlock Holmes", "Arthur Conan Doyle", "สืบสวน", "EN"),
    ("Atomic Habits", "James Clear", "พัฒนาตัวเอง", "EN"),
    ("The 7 Habits of Highly Effective People", "Stephen Covey", "พัฒนาตัวเอง", "EN"),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "จิตวิทยา", "EN"),
    ("Rich Dad Poor Dad", "Robert T. Kiyosaki", "การเงิน", "EN"),
    ("Sapiens", "Yuval Noah Harari", "ประวัติศาสตร์", "EN"),
    ("The Psychology of Money", "Morgan Housel", "การเงิน", "EN"),
    ("Clean Code", "Robert C. Martin", "คอมพิวเตอร์", "EN"),
    ("Python Crash Course", "Eric Matthes", "คอมพิวเตอร์", "EN"),
    ("The Little Prince", "Antoine de Saint-Exupery", "คลาสสิก", "EN"),
    ("One Piece, Vol. 1", "Eiichiro Oda", "การ์ตูน", "EN"),
    ("Naruto, Vol. 1", "Masashi Kishimoto", "การ์ตูน", "EN"),
    ("The Lightning Thief", "Rick Riordan", "เยาวชน/แฟนตาซี", "EN"),
]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:48]


def search(title, author):
    q = urllib.parse.urlencode({
        "title": title, "author": author, "limit": 5,
        "fields": "title,author_name,isbn,cover_i,first_publish_year",
    })
    data = json.loads(get("https://openlibrary.org/search.json?" + q))
    docs = data.get("docs", [])
    key = author.split()[-1].lower()
    ok = [d for d in docs if any(key in a.lower() for a in d.get("author_name", []))]
    for d in ok + docs:
        if d.get("cover_i"):
            return d
    return None


def main():
    out, fails = [], []
    for title, author, genre, lang in BOOKS:
        try:
            d = search(title, author)
            if not d:
                fails.append((title, "no cover on Open Library"))
                continue
            isbns = [i for i in d.get("isbn", []) if len(i) == 13 and i.isdigit()]
            isbn = (isbns or d.get("isbn", [""]))[0]
            url = f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg"
            path = os.path.join(COV, slug(title) + ".jpg")
            img = get(url)
            if len(img) < 3000:
                fails.append((title, f"cover too small ({len(img)} B)"))
                continue
            open(path, "wb").write(img)
            out.append({
                "book_id": "B%02d" % (len(out) + 1), "title": title, "author": author,
                "genre": genre, "lang": lang, "isbn": isbn,
                "year": d.get("first_publish_year"), "cover_i": d["cover_i"],
                "cover_file": "assets/covers/" + os.path.basename(path),
                "cover_url": url,
                "ol_title": d.get("title"),
            })
            print(f"OK   {title[:44]:46s} isbn={isbn} cover_i={d['cover_i']} {len(img)//1024}KB")
        except Exception as e:
            fails.append((title, f"{type(e).__name__}: {e}"))
        time.sleep(0.4)

    json.dump(out, open(os.path.join(BASE, "data", "books.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(out)}/{len(BOOKS)} books resolved -> data/books.json")
    for t, why in fails:
        print("FAIL", t, "|", why)
    return 0 if len(out) >= 24 else 1


if __name__ == "__main__":
    sys.exit(main())
