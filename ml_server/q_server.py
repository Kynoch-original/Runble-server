from flask import Flask, request, jsonify
from ml_agent import QLearningAgent
import os

app = Flask(__name__)

# ✅ Доступні дії
actions = ['up', 'down', 'left', 'right', 'attack']

# ✅ Повний шлях до Q-таблиці
q_table_path = os.path.join(os.path.dirname(__file__), "q_table.json")

# ✅ Ініціалізація агента з діями + завантаження таблиці
agent = QLearningAgent(actions, table_path=q_table_path)
agent.load_q_table()

@app.route("/zombie/act", methods=["POST"])
def zombie_act():
    data = request.get_json()
    state = tuple(data["state"])
    actions = data["actions"]
    action = agent.choose_action(state, actions)
    return jsonify({"action": action})

@app.route("/zombie/train", methods=["POST"])
def zombie_train():
    data = request.get_json()
    state = tuple(data["state"])
    action = data["action"]
    reward = data["reward"]
    next_state = tuple(data["next_state"])
    actions = data["actions"]

    print("🟥 Received training data:", data)

    try:
        agent.learn(state, action, reward, next_state, actions)
        agent.save_q_table()
        print("✅ Learned")
    except Exception as e:
        print("🔥 ERROR in learn:", e)

    return jsonify({"message": "Learned"})


@app.route("/save_q", methods=["POST"])
def save_q():
    agent.save_q_table()
    print("💾 Q-table saved.")
    return jsonify({"message": "Q-table saved"}), 200


@app.route("/load_q", methods=["POST"])
def load_q():
    agent.load_q_table()
    print("📥 Q-table loaded.")
    return jsonify({"message": "Q-table loaded"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
