from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "score.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE best_score (
                id INTEGER PRIMARY KEY,
                score INTEGER NOT NULL
            )
        ''')
        cursor.execute("INSERT INTO best_score (id, score) VALUES (?, ?)", (1, 0))
        conn.commit()
        conn.close()
        print("[✅] Локальна база створена.")
    else:
        print("[📁] База вже існує.")

@app.route("/scores", methods=["GET"])
def get_top_scores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nick, score FROM best_score ORDER BY score DESC LIMIT 5")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = [{"nickname": row[0], "score": row[1]} for row in rows]
    return jsonify(result)



@app.route("/score", methods=["POST"])
def post_score():
    data = request.get_json()
    nick = data.get("nick")
    score = data.get("score")

    if not nick or score is None:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT score FROM best_score WHERE nick = %s", (nick,))
    row = cur.fetchone()

    if row:
        current_score = row[0]
        if score > current_score:
            cur.execute("UPDATE best_score SET score = %s, last_score = %s WHERE nick = %s", (score, score, nick))
        else:
            cur.execute("UPDATE best_score SET last_score = %s WHERE nick = %s", (score, nick))
    else:
        cur.execute("INSERT INTO best_score (nick, score, last_score) VALUES (%s, %s, %s)", (nick, score, score))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Score saved successfully"}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)

