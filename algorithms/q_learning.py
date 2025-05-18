import random
import time

ALPHA = 0.1; GAMMA = 0.9; EPSILON = 0.1
NUM_EPISODES = 1000; MAX_STEPS_PER_EPISODE = 200

def get_valid_actions(state_tuple):
    """Returns list of possible actions (neighboring state_tuples)."""
    state = list(state_tuple)
    try: blank_index = state.index(9)
    except ValueError: return []
    row, col = divmod(blank_index, 3); possible_new_states = []
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)] # dr, dc
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_s = state[:]; new_index = new_row * 3 + new_col
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            possible_new_states.append(tuple(new_s))
    return possible_new_states

def get_reward(state_tuple, goal_state_tuple):
    """Calculates reward for a state."""
    if state_tuple == goal_state_tuple: return 100
    else: return -1

class QLearningAgent:
    def __init__(self, goal_state, alpha=ALPHA, gamma=GAMMA, epsilon=EPSILON):
        self.q_table = {} # state_tuple -> {action_state_tuple: q_value}
        self.goal_state = goal_state; self.alpha = alpha; self.gamma = gamma; self.epsilon = epsilon
        self.training_episodes = 0; self.nodes_expanded_during_training = 0
    def get_q_value(self, state_tuple, action_state_tuple):
        return self.q_table.get(state_tuple, {}).get(action_state_tuple, 0.0)
    def choose_action(self, state_tuple):
        possible_actions = get_valid_actions(state_tuple)
        if not possible_actions: return None
        if random.random() < self.epsilon: return random.choice(possible_actions)
        else:
            q_values = {action: self.get_q_value(state_tuple, action) for action in possible_actions}
            max_q = -float('inf'); best_actions = []
            for action, q_val in q_values.items(): # Renamed q to q_val
                if q_val > max_q: max_q = q_val; best_actions = [action]
                elif q_val == max_q: best_actions.append(action)
            return random.choice(best_actions) if best_actions else None
    def learn(self, state_tuple, action_state_tuple, reward, next_state_tuple):
        self.nodes_expanded_during_training +=1
        old_q_value = self.get_q_value(state_tuple, action_state_tuple)
        next_possible_actions = get_valid_actions(next_state_tuple)
        max_future_q = 0.0
        if next_possible_actions:
            max_future_q = max([self.get_q_value(next_state_tuple, future_action) for future_action in next_possible_actions], default=0.0)
        new_q_value = old_q_value + self.alpha * (reward + self.gamma * max_future_q - old_q_value)
        if state_tuple not in self.q_table: self.q_table[state_tuple] = {}
        self.q_table[state_tuple][action_state_tuple] = new_q_value
    def train(self, start_state_initial, num_episodes=NUM_EPISODES, max_steps_per_episode=MAX_STEPS_PER_EPISODE):
        print(f"Q-Learning: Training for {num_episodes} episodes...")
        start_time = time.time() # Renamed start_train_time
        for episode in range(num_episodes):
            current_state = start_state_initial
            for _ in range(max_steps_per_episode): # Renamed step to _
                action_taken = self.choose_action(current_state)
                if action_taken is None: break
                next_state = action_taken; reward = get_reward(next_state, self.goal_state)
                self.learn(current_state, action_taken, reward, next_state)
                current_state = next_state
                if current_state == self.goal_state: break
            self.training_episodes +=1
            if episode > 0 and episode % (num_episodes // 10 if num_episodes >=10 else 1) == 0: # Progress print
                 print(f"Ep {episode}, Q-table size: {len(self.q_table)}")
        print(f"Training finished in {time.time() - start_time:.2f}s. Nodes expanded: {self.nodes_expanded_during_training}")
    def get_policy_path(self, start_state_tuple, max_path_length=50):
        path = [start_state_tuple]; current_state = start_state_tuple; visited_in_path = {start_state_tuple}
        for _ in range(max_path_length):
            if current_state == self.goal_state: break
            possible_actions = get_valid_actions(current_state)
            if not possible_actions: return None
            q_values = {action: self.get_q_value(current_state, action) for action in possible_actions}
            best_action = None; max_q_val = -float('inf'); candidate_actions = [] # Renamed max_q
            for action, q_val_policy in q_values.items(): # Renamed q to q_val_policy
                if action not in visited_in_path:
                    if q_val_policy > max_q_val: max_q_val = q_val_policy; candidate_actions = [action]
                    elif q_val_policy == max_q_val: candidate_actions.append(action)
            if not candidate_actions:
                non_cycle_actions = [act for act in possible_actions if act not in visited_in_path]
                if non_cycle_actions: best_action = random.choice(non_cycle_actions)
                else: return None
            else: best_action = random.choice(candidate_actions)
            if best_action is None: return None
            current_state = best_action; path.append(current_state); visited_in_path.add(current_state)
        return path if path[-1] == self.goal_state else None

q_agent = None; is_trained = False

def solve(start_state, goal_state):
    """Solves 8-puzzle using Q-Learning."""
    global q_agent, is_trained
    if q_agent is None or q_agent.goal_state != goal_state:
        q_agent = QLearningAgent(goal_state=goal_state); is_trained = False
    if not is_trained:
        q_agent.train(start_state_initial=start_state); is_trained = True
    path = q_agent.get_policy_path(start_state)
    nodes_exp = q_agent.nodes_expanded_during_training if q_agent else 0 # Ensure agent exists
    return (path, nodes_exp) if path else (None, nodes_exp)

if __name__ == '__main__':
    test_start = (1, 8, 2, 9, 4, 3, 7, 6, 5); test_goal = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    solution, nodes = solve(test_start, test_goal)
    if solution: print("Path:", solution, "Nodes (training):", nodes)
    else: print("No solution. Nodes (training):", nodes)