from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
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
    cur.execute("SELECT best_score FROM player_progress WHERE nickname = %s AND user_id = %s", (nick, user_id))
    row = cur.fetchone()

    if row:
        best_score = row[0]
        if score > best_score:
            cur.execute("UPDATE player_progress SET best_score = %s, last_score = %s WHERE nickname = %s AND user_id = %s",
                        (score, score, nick, user_id))
        else:
            cur.execute("UPDATE player_progress SET last_score = %s WHERE nickname = %s AND user_id = %s",
                        (score, nick, user_id))
    else:
        cur.execute("INSERT INTO player_progress (nickname, best_score, last_score, user_id) VALUES (%s, %s, %s, %s)",
                    (nick, score, score, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Score saved successfully"})

@app.route("/scores", methods=["GET"])
def get_scores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nickname, best_score FROM player_progress ORDER BY best_score DESC LIMIT 5")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = [{"nickname": row[0], "score": row[1]} for row in rows]
    return jsonify(result)

@app.route("/save_progress", methods=["POST"])
def save_progress():
    data = request.get_json()
    nick = data.get("nick")
    user_id = data.get("user_id")
    score = data.get("score")
    level = data.get("level")
    damage = data.get("damage")
    max_health = data.get("max_health")
    fire_rate = data.get("fire_rate")
    spawn_wait = data.get("spawn_wait")
    xp_bar_value = data.get("xp_bar_value")
    health_bar_value = data.get("health_bar_value")

    if not nick or not user_id:
        return jsonify({"error": "Missing nickname or user_id"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM player_progress WHERE nickname = %s AND user_id = %s", (nick, user_id))
    if cur.fetchone():
        cur.execute("""
            UPDATE player_progress SET score = %s, level = %s, damage = %s, max_health = %s,
            fire_rate = %s, spawn_wait = %s, xp_bar_value = %s, health_bar_value = %s, last_score = %s
            WHERE nickname = %s AND user_id = %s
        """, (score, level, damage, max_health, fire_rate, spawn_wait,
              xp_bar_value, health_bar_value, score, nick, user_id))
    else:
        cur.execute("""
            INSERT INTO player_progress (nickname, user_id, score, level, damage, max_health,
            fire_rate, spawn_wait, xp_bar_value, health_bar_value, best_score, last_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nick, user_id, score, level, damage, max_health, fire_rate, spawn_wait,
              xp_bar_value, health_bar_value, score, score))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Progress saved"})

@app.route("/load_progress", methods=["POST"])
def load_progress():
    data = request.get_json()
    nick = data.get("nick")
    user_id = data.get("user_id")

    if not nick or not user_id:
        return jsonify({"error": "Missing nickname or user_id"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT score, level, damage, max_health, fire_rate, spawn_wait, xp_bar_value, health_bar_value 
        FROM player_progress WHERE nickname = %s AND user_id = %s
    """, (nick, user_id))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        keys = ["score", "level", "damage", "max_health", "fire_rate", "spawn_wait", "xp_bar_value", "health_bar_value"]
        return jsonify(dict(zip(keys, row)))
    else:
        return jsonify({"error": "No progress found"}), 404

@app.route("/has_progress", methods=["POST"])
def has_progress():
    data = request.get_json()
    nick = data.get("nick", "")
    user_id = data.get("user_id", "")

    if not nick or not user_id:
        return jsonify({"has_progress": False}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM player_progress 
        WHERE nickname = %s AND user_id = %s LIMIT 1
    """, (nick, user_id))
    result = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({"has_progress": bool(result)}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
