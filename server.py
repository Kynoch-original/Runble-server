from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import json

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        port=os.environ.get("DB_PORT")
    )

@app.route("/score", methods=["POST"])
def post_score():
    data = request.get_json()
    nick = data.get("nick")
    score = data.get("score")
    user_id = data.get("user_id")

    if not nick or score is None or not user_id:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT score FROM best_score WHERE nick = %s AND user_id = %s", (nick, user_id))
    row = cur.fetchone()

    if row:
        best_score = row[0]
        if score > best_score:
            cur.execute("UPDATE best_score SET score = %s, last_score = %s WHERE nick = %s AND user_id = %s",
                        (score, score, nick, user_id))
        else:
            cur.execute("UPDATE best_score SET last_score = %s WHERE nick = %s AND user_id = %s",
                        (score, nick, user_id))
    else:
        cur.execute("INSERT INTO best_score (nick, score, last_score, user_id) VALUES (%s, %s, %s, %s)",
                    (nick, score, score, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Score saved successfully"})

@app.route("/save_progress", methods=["POST"])
def save_progress():
    data = request.get_json()
    nick = data.get("nick", "unnamed")
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Отримання значень або дефолт
    score = data.get("score", 0)
    level = data.get("level", 1)
    damage = data.get("damage", 0)
    fire_rate = data.get("fire_rate", 1.0)
    spawn_wait = data.get("spawn_wait", 0.5)
    max_health = data.get("max_health", 100)
    xp = data.get("xp_bar_value", 0)
    hp = data.get("health_bar_value", 0)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO best_score (nick, user_id, score, last_score, level, damage, fire_rate, spawn_wait, max_health, xp_bar_value, health_bar_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            nick = EXCLUDED.nick,
            score = GREATEST(best_score.score, EXCLUDED.score),
            last_score = EXCLUDED.last_score,
            level = EXCLUDED.level,
            damage = EXCLUDED.damage,
            fire_rate = EXCLUDED.fire_rate,
            spawn_wait = EXCLUDED.spawn_wait,
            max_health = EXCLUDED.max_health,
            xp_bar_value = EXCLUDED.xp_bar_value,
            health_bar_value = EXCLUDED.health_bar_value
    """, (nick, user_id, score, score, level, damage, fire_rate, spawn_wait, max_health, xp, hp))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/load_progress", methods=["POST"])
def load_progress():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id missing"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT nick, score, level, damage, fire_rate, spawn_wait, max_health, xp_bar_value, health_bar_value
        FROM best_score WHERE user_id = %s
    """, (user_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({
            "nick": row[0],
            "score": row[1],
            "level": row[2],
            "damage": row[3],
            "fire_rate": row[4],
            "spawn_wait": row[5],
            "max_health": row[6],
            "xp_bar_value": row[7],
            "health_bar_value": row[8]
        }), 200
    else:
        return jsonify({"error": "no_progress"}), 404

@app.route("/has_progress", methods=["POST"])
def has_progress():
    data = request.get_json()
    nick = data.get("nick", "").strip()
    user_id = data.get("user_id", "").strip()

    if not nick or not user_id:
        return jsonify({"has_progress": False}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM best_score WHERE nick = %s AND user_id = %s LIMIT 1", (nick, user_id))
    result = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({"has_progress": bool(result)}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
