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

    @app.route("/score", methods=["POST"])
    def post_score():
        data = request.get_json()
        user_id = data.get("user_id")
        nick = data.get("nick")
        score = data.get("score")

        if not user_id or score is None:
            return jsonify({"status": "error", "message": "Missing user_id or score"}), 400

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM best_score WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        if row:
            if score > row[0]:
                cursor.execute("UPDATE best_score SET score = %s WHERE user_id = %s", (score, user_id))
        else:
            cursor.execute("""
                INSERT INTO best_score (user_id, nick, score, last_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, nick, score, score))

        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})

    @app.route("/scores", methods=["GET"])
    def get_top_scores():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, nick, score FROM best_score
            ORDER BY score DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        conn.close()

        top_scores = []
        for row in rows:
            top_scores.append({
                "user_id": row[0],
                "nick": row[1],
                "score": row[2]
            })

        return jsonify({"top_scores": top_scores}), 200

    @app.route("/save_progress", methods=["POST"])
    def save_progress():
        data = request.get_json()
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        nick = data.get("nick")
        new_score = data.get("score", 0)
        damage = data.get("damage", 1)
        max_health = data.get("max_health", 100)
        fire_rate = data.get("fire_rate", 0.5)
        spawn_wait = data.get("spawn_wait", 1.0)
        level = data.get("level", 1)
        xp_bar_value = data.get("xp_bar_value", 0.0)
        health_bar_value = data.get("health_bar_value", 0.0)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM best_score WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        if row:
            current_best = row[0]
            if new_score > current_best:
                cursor.execute("""
                    UPDATE best_score SET
                        score = %s, last_score = %s,
                        damage = %s, max_health = %s, fire_rate = %s,
                        spawn_wait = %s, level = %s,
                        xp_bar_value = %s, health_bar_value = %s,
                        nick = %s
                    WHERE user_id = %s
                """, (new_score, new_score, damage, max_health, fire_rate,
                      spawn_wait, level, xp_bar_value, health_bar_value, nick, user_id))
            else:
                cursor.execute("""
                    UPDATE best_score SET
                        last_score = %s,
                        damage = %s, max_health = %s, fire_rate = %s,
                        spawn_wait = %s, level = %s,
                        xp_bar_value = %s, health_bar_value = %s,
                        nick = %s
                    WHERE user_id = %s
                """, (new_score, damage, max_health, fire_rate,
                      spawn_wait, level, xp_bar_value, health_bar_value, nick, user_id))
        else:
            cursor.execute("""
                INSERT INTO best_score (
                    user_id, nick, score, last_score, damage, max_health,
                    fire_rate, spawn_wait, level,
                    xp_bar_value, health_bar_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, nick, new_score, new_score, damage, max_health,
                  fire_rate, spawn_wait, level, xp_bar_value, health_bar_value))

        conn.commit()
        conn.close()
        return jsonify({"status": "saved"}), 200

    @app.route("/load_progress", methods=["POST"])
    def load_progress():
        data = request.get_json()
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT score, last_score, damage, max_health, fire_rate,
                spawn_wait, level, xp_bar_value, health_bar_value, nick
            FROM best_score WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            (
                score, last_score, damage, max_health, fire_rate,
                spawn_wait, level, xp_bar_value, health_bar_value, nick
            ) = row

            return jsonify({
                "score": last_score,
                "best_score": score,
                "damage": damage,
                "max_health": max_health,
                "fire_rate": fire_rate,
                "spawn_wait": spawn_wait,
                "level": level,
                "xp_bar_value": xp_bar_value,
                "health_bar_value": health_bar_value,
                "nick": nick
            }), 200
        else:
            return jsonify({"error": "Not found"}), 404

    @app.route("/reset_progress", methods=["DELETE"])
    def reset_progress():
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM best_score WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

        return jsonify({"status": "reset"}), 200

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
