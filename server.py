import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

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

        # Створюємо таблицю якщо її ще нема
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS best_score (
                nick TEXT PRIMARY KEY,
                score INTEGER,
                damage INTEGER DEFAULT 1,
                max_health INTEGER DEFAULT 100,
                fire_rate REAL DEFAULT 0.5,
                spawn_wait REAL DEFAULT 1.0
            )
        """)

        # Додаємо колонку level, якщо її ще нема
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='best_score' AND column_name='level'
                ) THEN
                    ALTER TABLE best_score ADD COLUMN level INTEGER DEFAULT 1;
                END IF;
            END
            $$;
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
            cursor.execute("""
                INSERT INTO best_score (nick, score)
                VALUES (%s, %s)
                ON CONFLICT (nick) DO NOTHING
            """, (nick, score))

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

    @app.route("/save_progress", methods=["POST"])
    def save_progress():
        data = request.get_json()
        nick = data.get("nick")
        if not nick:
            return jsonify({"error": "Missing nick"}), 400

        new_score = data.get("score", 0)
        damage = data.get("damage", 1)
        max_health = data.get("max_health", 100)
        fire_rate = data.get("fire_rate", 0.5)
        spawn_wait = data.get("spawn_wait", 1.0)
        level = data.get("level", 1)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM best_score WHERE nick = %s", (nick,))
        row = cursor.fetchone()

        if row:
            current_score = row[0]
            if new_score > current_score:
                cursor.execute("""
                    UPDATE best_score SET
                        score = %s,
                        damage = %s,
                        max_health = %s,
                        fire_rate = %s,
                        spawn_wait = %s,
                        level = %s
                    WHERE nick = %s
                """, (new_score, damage, max_health, fire_rate, spawn_wait, level, nick))
            else:
                cursor.execute("""
                    UPDATE best_score SET
                        damage = %s,
                        max_health = %s,
                        fire_rate = %s,
                        spawn_wait = %s,
                        level = %s
                    WHERE nick = %s
                """, (damage, max_health, fire_rate, spawn_wait, level, nick))
        else:
            cursor.execute("""
                INSERT INTO best_score (score, damage, max_health, fire_rate, spawn_wait, level, nick)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (new_score, damage, max_health, fire_rate, spawn_wait, level, nick))

        conn.commit()
        conn.close()
        return jsonify({"status": "saved"}), 200

    @app.route("/load_progress", methods=["POST"])
    def load_progress():
        data = request.get_json()
        nick = data.get("nick")
        if not nick:
            return jsonify({"error": "Missing nick"}), 400

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT score, damage, max_health, fire_rate, spawn_wait, level
            FROM best_score WHERE nick = %s
        """, (nick,))
        row = cursor.fetchone()
        conn.close()

        if row:
            keys = ["score", "damage", "max_health", "fire_rate", "spawn_wait", "level"]
            return jsonify(dict(zip(keys, row))), 200
        else:
            return jsonify({"error": "Not found"}), 404

    with app.app_context():
        init_db()

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
