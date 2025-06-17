import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

# Отримання параметрів з ENV
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT", 5432)

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def create_app():
    app = Flask(__name__)
    CORS(app)

    def init_db():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS best_score (
                nick TEXT PRIMARY KEY,
                score INTEGER
            )
        """)
        conn.commit()
        conn.close()

    @app.route("/score", methods=["POST"])
    def post_score():
        data = request.get_json()
        nick = data.get("nick")
        score = data.get("score")

        if not nick or score is None:
            return jsonify({"status": "error", "message": "Missing nickname or score"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT score FROM best_score WHERE nick = %s", (nick,))
        row = cursor.fetchone()

        if row:
            if score > row[0]:
                cursor.execute("UPDATE best_score SET score = %s WHERE nick = %s", (score, nick))
        else:
            cursor.execute("INSERT INTO best_score (nick, score) VALUES (%s, %s)", (nick, score))

        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})

    @app.route("/scores", methods=["GET"])
    def get_top_scores():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nick, score FROM best_score ORDER BY score DESC LIMIT 5")
        results = cursor.fetchall()
        conn.close()

        top_scores = [{"nickname": nick, "score": score} for nick, score in results]
        return jsonify(top_scores), 200

    with app.app_context():
        init_db()

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
