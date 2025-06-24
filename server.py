from flask import Flask, request, jsonify
import os
import psycopg2

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname   = os.environ.get("PGDATABASE", "runble_db"),
        user     = os.environ.get("PGUSER",     "runble_db_user"),
        password = os.environ.get("PGPASSWORD", "SUJo613ghabacOOrpOe4rdPSdtn2Dsxy"),
        host     = os.environ.get("PGHOST",     "dpg-d17vc5vdiees73f7o79g-a"),
        port     = os.environ.get("PGPORT",     "5432"),
    )

def init_db():
    """Створює таблицю best_score у Postgres, якщо її ще немає."""
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS best_score (
            nick       TEXT PRIMARY KEY,
            score      INTEGER NOT NULL DEFAULT 0,
            last_score INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[✅] Таблиця best_score готова в PostgreSQL.")

@app.route("/scores", methods=["GET"])
def get_top_scores():
    """Повертає JSON-список з топ-5 гравців за полем score."""
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT nick, score
          FROM best_score
         ORDER BY score DESC
         LIMIT 5
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([{"nickname": nick, "score": score} for nick, score in rows])

@app.route("/score", methods=["POST"])
def post_score():
    """
    Приймає JSON: {"nick": "...", "score": N}
    Вставляє новий запис або оновлює існуючий:
      - score = max(old_score, new_score)
      - last_score = new_score
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    nick  = data.get("nick")
    score = data.get("score")
    if not isinstance(nick, str) or not isinstance(score, (int, float)):
        return jsonify({"error": "Missing or invalid fields"}), 400

    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO best_score (nick, score, last_score)
             VALUES (%s, %s, %s)
        ON CONFLICT (nick) DO UPDATE
           SET score      = GREATEST(best_score.score, EXCLUDED.score),
               last_score = EXCLUDED.score;
    """, (nick, int(score), int(score)))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Score saved successfully"}), 200

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    # Включіть debug=False у продакшені!
    app.run(debug=True, host="0.0.0.0", port=port)
