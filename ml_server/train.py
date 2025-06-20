from ml_agent import QLearningAgent
import random

actions = ["up", "down", "left", "right", "attack"]
agent = QLearningAgent(actions, epsilon=0.2)

def generate_state():
    dx = random.uniform(-300, 300)
    dy = random.uniform(-300, 300)
    return [dx, dy]

def distance(state):
    return (state[0] ** 2 + state[1] ** 2) ** 0.5

EPISODES = 100_000

for episode in range(EPISODES):
    state = generate_state()
    dx, dy = state
    dist_before = distance(state)

    action = random.choice(actions)

    # Симуляція руху
    if action == "left": dx -= 10
    elif action == "right": dx += 10
    elif action == "up": dy -= 10
    elif action == "down": dy += 10

    next_state = [dx, dy]
    dist_after = distance(next_state)

    # Ревард функція
    if action == "attack":
        reward = 10 if dist_before < 100 else -5
    elif dist_after < dist_before:
        reward = 1
    else:
        reward = -0.5

    agent.learn(state, action, reward, next_state, actions)

agent.save_q_table()
print(f"✅ Q-table trained and saved after {EPISODES} episodes")
