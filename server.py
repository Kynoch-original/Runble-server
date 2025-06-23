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

@app.route("/score", methods=["GET"])
def get_score():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM best_score WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    return jsonify({"best_score": result[0] if result else 0})

@app.route("/score", methods=["POST"])
def post_score():
    data = request.get_json(force=True)
    new_score = data.get("score")

    if new_score is None:
        return jsonify({"error": "Missing score"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT score FROM best_score WHERE id = 1")
    current_score = cursor.fetchone()[0]

    if new_score > current_score:
        cursor.execute("UPDATE best_score SET score = ? WHERE id = 1", (new_score,))
        conn.commit()
        updated = True
    else:
        updated = False

    conn.close()

    return jsonify({
        "message": "Score updated" if updated else "Score not higher",
        "current_best": max(current_score, new_score)
    }), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)

