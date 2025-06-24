import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify

app = Flask(__name__)

# Параметри з’єднання з БД через змінні середовища (або дефолтні)
DB_NAME     = os.environ.get("PG_DB",       "runble_db")
DB_USER     = os.environ.get("PG_USER",     "runble_db_user")
DB_PASSWORD = os.environ.get("PG_PASSWORD", "SUJo613ghabacOOrpOe4rdPSdtn2Dsxy")
DB_HOST     = os.environ.get("PG_HOST",     "dpg-d17vc5vdiees73f7o79g-a")
DB_PORT     = os.environ.get("PG_PORT",     "5432")

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def init_db():
    """Створює таблицю best_score, якщо її ще немає."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS best_score (
            nick        TEXT PRIMARY KEY,
            score       INTEGER NOT NULL,
            last_score  INTEGER NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Ініціалізуємо БД відразу при старті модуля
init_db()

@app.route("/scores", methods=["GET"])
def get_top_scores():
    """
    Повертає JSON-масив з топ-5 гравців за полем score.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT nick   AS nickname,
               score
          FROM best_score
         ORDER BY score DESC
         LIMIT 5;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200

@app.route("/score", methods=["POST"])
def post_score():
    """
    Приймає JSON { "nick": "...", "score": 123 }.
    Якщо гравець новий — додає рядок.
    Якщо існує — оновлює last_score і приймає новий score лише якщо він більший.
    """
    data = request.get_json(force=True)
    nick  = data.get("nick")
    score = data.get("score")

    if not nick or score is None:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO best_score(nick, score, last_score)
        VALUES (%s, %s, %s)
        ON CONFLICT (nick) DO UPDATE
          SET last_score = EXCLUDED.score,
              score      = GREATEST(best_score.score, EXCLUDED.score);
    """, (nick, score, score))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Score saved successfully"}), 200

if __name__ == "__main__":
    # Для локального запуску через flask run або python server.py
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
