from flask import Flask, request, jsonify
# import sqlite3
import os
import psycopg2
import random

app = Flask(__name__)
#DB_PATH = "score.db"

def get_db_connection():
    return psycopg2.connect(
        dbname="runble_db",
        user="runble_db_user",
        password="SUJo613ghabacOOrpOe4rdPSdtn2Dsxy",
        host="dpg-d17vc5vdiees73f7o79g-a",
        port="5432"
    )

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

@app.route("/auth", methods=["POST"])
def auth():
    data = request.get_json()
    nick = data.get("nick")
    code = data.get("code")

    if not nick:
        return jsonify({"error": "Missing nick"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT code FROM best_score WHERE nick = %s", (nick,))
    row = cur.fetchone()

    if row:
        existing_code = row[0]
        if str(code) == str(existing_code):
            result = {"status": "ok", "message": "Access granted"}
        else:
            result = {"status": "error", "message": "wrong_code"}
    else:
        new_code = str(random.randint(1000, 9999))

        cur.execute("""
            INSERT INTO best_score (nick, score, last_score, code)
            VALUES (%s, 0, 0, %s)
        """, (nick, new_code))

        result = {"status": "new_user", "code": new_code}

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(result), 200



if __name__ == "__main__":
    #nit_db()
    app.run(debug=True, host="127.0.0.1", port=5000)

