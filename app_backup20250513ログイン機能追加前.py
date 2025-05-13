from datetime import datetime
from flask import Flask, render_template, request, redirect
import csv
import os
import sqlite3

app = Flask(__name__)
CSV_FILE = "data/manuals.csv"

# トップページ（一覧表示）
@app.route("/", methods=["GET"])
def index():
    keyword = request.args.get("q", "")
    sort = request.args.get("sort", "desc")
    page = int(request.args.get("page", 1))  # ←★ページ番号（1始まり）
    per_page = 5  # ←★1ページあたりの表示数

    offset = (page - 1) * per_page

    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()

    order_clause = "ORDER BY datetime(created_at) DESC" if sort == "desc" else "ORDER BY datetime(created_at) ASC"

    if keyword:
        query = f"""
        SELECT rowid, name, category, idea, note, created_at
        FROM ideas
        WHERE name LIKE ? OR category LIKE ? OR idea LIKE ? OR note LIKE ?
        {order_clause}
        LIMIT ? OFFSET ?
        """
        like_keyword = f"%{keyword}%"
        c.execute(query, (like_keyword, like_keyword, like_keyword, like_keyword, per_page, offset))
    else:
        query = f"""
        SELECT rowid, name, category, idea, note, created_at
        FROM ideas
        {order_clause}
        LIMIT ? OFFSET ?
        """
        c.execute(query, (per_page, offset))

    manuals = c.fetchall()

    # 全件数を取得して最大ページ数を算出
    c.execute("SELECT COUNT(*) FROM ideas")
    total_count = c.fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page

    conn.close()
    return render_template("index.html", manuals=manuals, keyword=keyword, sort=sort,
                           page=page, total_pages=total_pages)

# 投稿ページ

from datetime import datetime

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        steps = request.form.get("steps")
        notes = request.form.get("notes")
        created_at = datetime.now().isoformat()

        if not title or not category or not steps:
            return "タイトル・カテゴリ・手順は必須です", 400

        conn = sqlite3.connect("ideas.db")
        c = conn.cursor()
        c.execute("INSERT INTO ideas (name, category, idea, note, created_at) VALUES (?, ?, ?, ?, ?)",
                  (title, category, steps, notes, created_at))
        conn.commit()
        conn.close()

        return redirect("/")

    # ← ここがポイント（GET時）
    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM ideas ORDER BY category ASC")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    
    return render_template("add.html", categories=categories)


# 編集ページ
@app.route("/edit/<int:manual_id>", methods=["GET", "POST"])
def edit(manual_id):
    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        steps = request.form.get("steps")
        notes = request.form.get("notes")

        if not name or not category or not steps:
            return "タイトル・カテゴリ・手順は必須です", 400

        c.execute("UPDATE ideas SET name = ?, category = ?, idea = ?, note = ? WHERE rowid = ?",
                  (name, category, steps, notes, manual_id))
        conn.commit()
        conn.close()
        return redirect("/")

    # GET時：編集フォームを表示
    c.execute("SELECT rowid, name, category, idea, note FROM ideas WHERE rowid = ?", (manual_id,))
    row = c.fetchone()
    manual = {
        "rowid": row[0],
        "name": row[1],
        "category": row[2],
        "idea": row[3],
        "note": row[4]
    }

    # 全カテゴリ一覧を取得
    c.execute("SELECT DISTINCT category FROM ideas ORDER BY category ASC")
    categories = [row[0] for row in c.fetchall()]
    conn.close()

    return render_template("edit.html", manual=manual, categories=categories)

#削除機能
@app.route("/delete/<int:manual_id>")
def delete(manual_id):
    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()
    c.execute("DELETE FROM ideas WHERE rowid = ?", (manual_id,))
    conn.commit()
    conn.close()
    return redirect("/")

 #カテゴリ別表示
@app.route("/category/<category>")
def category_view(category):
    sort = request.args.get("sort", "desc")  # クエリから並び順を取得（デフォルト：降順）

    order_clause = "ORDER BY datetime(created_at) DESC" if sort == "desc" else "ORDER BY datetime(created_at) ASC"

    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()
    query = f"""
        SELECT rowid, name, category, idea, note, created_at
        FROM ideas
        WHERE category = ?
        {order_clause}
    """
    c.execute(query, (category,))
    manuals = c.fetchall()
    conn.close()
    return render_template("category.html", manuals=manuals, category=category, sort=sort)

# カテゴリ一覧ページ
@app.route("/categories")
def category_list():
    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM ideas ORDER BY category ASC")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return render_template("categories.html", categories=categories)

@app.route("/categories/add", methods=["POST"])
def add_category():
    new_category = request.form.get("new_category")
    if new_category:
        conn = sqlite3.connect("ideas.db")
        c = conn.cursor()
        # 重複チェック
        c.execute("SELECT DISTINCT category FROM ideas WHERE category = ?", (new_category,))
        if not c.fetchone():
            # 空のマニュアルでも1件挿入してカテゴリを作る or 何らかの登録方法に変えてもOK
            c.execute("INSERT INTO ideas (name, category, idea, note, created_at) VALUES (?, ?, ?, ?, ?)",
                      ("", new_category, "", "", datetime.now().isoformat()))
            conn.commit()
        conn.close()
    return redirect("/categories")


@app.route("/categories/edit", methods=["POST"])
def edit_category():
    old = request.form.get("old_category")
    new = request.form.get("new_category")
    if old and new and old != new:
        conn = sqlite3.connect("ideas.db")
        c = conn.cursor()
        c.execute("UPDATE ideas SET category = ? WHERE category = ?", (new, old))
        conn.commit()
        conn.close()
    return redirect("/categories")


@app.route("/categories/delete", methods=["POST"])
def delete_category():
    delete = request.form.get("delete_category")
    if delete:
        conn = sqlite3.connect("ideas.db")
        c = conn.cursor()
        c.execute("DELETE FROM ideas WHERE category = ?", (delete,))
        conn.commit()
        conn.close()
    return redirect("/categories")

if __name__ == "__main__":

    import sqlite3

def add_created_at_column():
    conn = sqlite3.connect("ideas.db")
    c = conn.cursor()
    try:
        # すでに存在していたらエラーになるが、それを握りつぶす
        c.execute("ALTER TABLE ideas ADD COLUMN created_at TEXT")
        print("カラム 'created_at' を追加しました。")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("カラム 'created_at' はすでに存在します。")
        else:
            raise
    finally:
        conn.commit()
        conn.close()

import os

if __name__ == "__main__":
    add_created_at_column()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
