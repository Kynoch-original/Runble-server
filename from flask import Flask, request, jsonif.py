from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "scores.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL UNIQUE,
                score INTEGER NOT NULL,
                user_id TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("[✅] Базу створено вперше.")
    else:
        print("[📁] База вже існує. Перезапуск без втрати даних.")
    print("📂 База створена за адресою:", os.path.abspath(DB_PATH))


@app.route("/scores", methods=["GET"])
def get_scores():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, score FROM scores ORDER BY score DESC LIMIT 5")
    results = cursor.fetchall()
    conn.close()
    return jsonify([{"nickname": row[0], "score": row[1]} for row in results])


@app.route("/scores", methods=["POST"])
def post_score():
    data = request.get_json(force=True)
    print("[📥] Отримано JSON:", data)

    nickname = data.get("nickname")
    score = data.get("score")
    user_id = data.get("user_id")

    print(f"[+] Отримано результат: {nickname} — {score} від {user_id}")
    print(f"[📡] Надійшов POST-запит на /scores")

    if not nickname or not user_id:
        return jsonify({"error": "Missing nickname or user_id"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT score, user_id FROM scores WHERE nickname = ?", (nickname,))
    existing = cursor.fetchone()

    if existing:
        existing_score, existing_user_id = existing
        if user_id != existing_user_id:
            conn.close()
            print(f"[🚫] Нікнейм {nickname} вже зайнятий іншим користувачем.")
            return jsonify({"error": "Nickname already taken by another user"}), 403

        if score > existing_score:
            cursor.execute("UPDATE scores SET score = ? WHERE nickname = ?", (score, nickname))
            print(f"[⬆] Оновлено рекорд для {nickname}: {score}")
        else:
            print(f"[⚠] Старий рекорд кращий ({existing_score}). Нічого не змінено.")
    else:
        cursor.execute("INSERT INTO scores (nickname, score, user_id) VALUES (?, ?, ?)", (nickname, score, user_id))
        print(f"[➕] Додано нового гравця: {nickname} → {score} | ID: {user_id}")

    conn.commit()
    conn.close()

    return jsonify({"message": "Score processed", "nickname": nickname}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
