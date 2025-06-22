from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    print("🟡 DB config:",
          os.environ.get("DB_HOST"),
          os.environ.get("DB_USER"),
          os.environ.get("DB_NAME"),
          os.environ.get("DB_PORT"),
          os.environ.get("DB_PASS"))  # додай для дебагу

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
    cur.execute("SELECT best_score FROM player_progress WHERE nick = %s AND user_id = %s", (nick, user_id))
    row = cur.fetchone()

    if row:
        best_score = row[0]
        if score > best_score:
            cur.execute("UPDATE player_progress SET best_score = %s, last_score = %s WHERE nick = %s AND user_id = %s",
                        (score, score, nick, user_id))
        else:
            cur.execute("UPDATE player_progress SET last_score = %s WHERE nick = %s AND user_id = %s",
                        (score, nick, user_id))
    else:
        cur.execute("INSERT INTO player_progress (nick, best_score, last_score, user_id) VALUES (%s, %s, %s, %s)",
                    (nick, score, score, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Score saved successfully"})

@app.route("/scores", methods=["GET"])
def get_scores():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT nick, score 
            FROM best_score 
            WHERE nick IS NOT NULL AND score IS NOT NULL
            ORDER BY score DESC LIMIT 5
        """)
        rows = cur.fetchall()
        result = [{"nick": row[0], "score": row[1]} for row in rows]
        return jsonify(result)
    except Exception as e:
        print("❌ Server error in get_scores:", e)
        return jsonify({"error": "Server error"}), 500
    finally:
        cur.close()
        conn.close()

@app.route("/save_progress", methods=["POST"])
def save_progress():
    data = request.get_json()
    nickname = data.get("nickname")
    user_id = data.get("user_id")
    print("📦 upgrades =", data.get("upgrades"))
    upgrades = json.dumps(data.get("upgrades", {}))
    xp = data.get("xp_bar_value", 0)
    hp = data.get("health_bar_value", 0)

    conn = get_db_connection()
    cur = conn.cursor()

    # Спроба оновити, або вставити якщо немає
    cur.execute("""
        INSERT INTO player_progress (nickname, user_id, upgrades, xp_bar_value, health_bar_value)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            nickname = EXCLUDED.nickname,
            upgrades = EXCLUDED.upgrades,
            xp_bar_value = EXCLUDED.xp_bar_value,
            health_bar_value = EXCLUDED.health_bar_value
    """, (nickname, user_id, upgrades, xp, hp))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route("/load_progress", methods=["POST"])
def load_progress():
    data = request.get_json()
    user_id = data.get("user_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nickname, upgrades, xp_bar_value, health_bar_value FROM player_progress WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        nickname, upgrades_json, xp, hp = row
        return jsonify({
            "nickname": nickname,
            "upgrades": upgrades_json,
            "xp_bar_value": xp,
            "health_bar_value": hp
        }), 200
    else:
        return jsonify({"error": "no_progress"}), 404

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
            SELECT 1 FROM best_score
            WHERE nick = %s AND user_id = %s LIMIT 11
    """, (nick, user_id))
    result = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({"has_progress": bool(result)}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
