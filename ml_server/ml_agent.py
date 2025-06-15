import json
import os
import random
import threading

class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1, table_path="q_table.json"):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.table_path = table_path
        self.load_q_table()
        self.lock = threading.Lock()
        self.learn_counter = 0

    def get_state_key(self, state):
        return str([round(x / 10) * 10 for x in state])


    def choose_action(self, state, actions):
        key = self.get_state_key(state)
        with self.lock:
            if random.random() < self.epsilon or key not in self.q_table:
                return random.choice(actions)
            return max(self.q_table[key], key=self.q_table[key].get)


    def learn(self, state, action, reward, next_state, actions):
        with self.lock:
            key = self.get_state_key(state)
            next_key = self.get_state_key(next_state)

            self.q_table.setdefault(key, {a: 0.0 for a in actions})
            self.q_table.setdefault(next_key, {a: 0.0 for a in actions})

            q_predict = self.q_table[key][action]
            q_target = reward + self.gamma * max(self.q_table[next_key].values())
            self.q_table[key][action] += self.alpha * (q_target - q_predict)

            self.epsilon = max(0.01, self.epsilon * 0.995)

            print(f"✅ Learned {state=} {action=} {reward=} {next_state=}")
            self.learn_counter += 1
            if self.learn_counter % 10 == 0:
                self.save_q_table()




    def save_q_table(self):
        with open(self.table_path, "w") as f:
            json.dump(self.q_table, f)
        print("✅ Q-table saved to", self.table_path)

    def load_q_table(self):
        if os.path.exists(self.table_path):
            with open(self.table_path, "r") as f:
                self.q_table = json.load(f)
            print("📂 Q-table loaded from", self.table_path)
        else:
            print("📁 No existing Q-table. Starting fresh.")
