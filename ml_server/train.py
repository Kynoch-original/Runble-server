from ml_agent import QLearningAgent
import random

actions = ["up", "down", "left", "right", "attack", "wait"]
agent = QLearningAgent(actions, epsilon=0.2)

def generate_state():
    # Випадкова відстань до гравця по X і Y
    dx = random.uniform(-300, 300)
    dy = random.uniform(-300, 300)
    return [dx, dy]

def distance(state):
    return (state[0] ** 2 + state[1] ** 2) ** 0.5

for episode in range(20000):
    state = generate_state()
    action = random.choice(actions)

    # Рух зомбі в напрямку дії
    dx, dy = state
    if action == "left": dx -= 10
    if action == "right": dx += 10
    if action == "up": dy -= 10
    if action == "down": dy += 10

    next_state = [dx, dy]
    dist_now = distance(state)
    dist_next = distance(next_state)

    # Обчислюємо винагороду
    if action == "attack":
        reward = 5 if dist_now < 100 else -2
    elif dist_next < dist_now:
        reward = 1  # Зблизився
    else:
        reward = -1  # Відійшов

    agent.learn(state, action, reward, next_state, actions)

# Зберігаємо таблицю
agent.save_q_table()
print("✅ Q-table trained and saved")
