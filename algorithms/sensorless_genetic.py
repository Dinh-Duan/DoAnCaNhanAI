# algorithms/sensorless_genetic.py
import random
from typing import List, Tuple, Optional, Set, Dict

State = Tuple[int, ...]
Action = str # 'Up', 'Down', 'Left', 'Right'
ActionSequence = List[Action]

# --- Helper: Apply a sequence of actions ---
def apply_action_sequence(initial_state: State, actions: ActionSequence) -> Optional[State]:
    """Áp dụng một chuỗi hành động vào một trạng thái ban đầu."""
    current_state = list(initial_state)
    size = int(len(current_state)**0.5)
    blank_tile_value = size * size

    for action in actions:
        try:
            blank_index = current_state.index(blank_tile_value)
        except ValueError:
            return None # Trạng thái không hợp lệ (không có ô trống)

        row, col = divmod(blank_index, size)
        dr, dc = 0, 0

        if action == 'Up': dr = -1
        elif action == 'Down': dr = 1
        elif action == 'Left': dc = -1
        elif action == 'Right': dc = 1
        else: # Hành động không hợp lệ
            return None 

        new_row, new_col = row + dr, col + dc

        if 0 <= new_row < size and 0 <= new_col < size:
            new_index = new_row * size + new_col
            current_state[blank_index], current_state[new_index] = current_state[new_index], current_state[blank_index]
        else:
            # Hành động dẫn ra ngoài biên, coi như thất bại cho chuỗi này
            # Hoặc có thể bỏ qua hành động này và tiếp tục, tùy thiết kế
            return None # Chuỗi không hợp lệ nếu 1 hành động ra ngoài biên
            
    return tuple(current_state)

# --- Individual: Represents a sequence of actions ---
class SensorlessIndividual:
    def __init__(self, actions: ActionSequence, belief_states: List[State], goal_state: State):
        self.actions: ActionSequence = actions
        self.belief_states: List[State] = belief_states # Các trạng thái bắt đầu có thể
        self.goal_state: State = goal_state
        self.fitness: float = self._calculate_fitness()

    def _calculate_fitness(self) -> float:
        if not self.actions:
            return 0.0 # Chuỗi rỗng không có fitness

        num_solved = 0
        total_heuristic_after_actions = 0
        
        for start_state in self.belief_states:
            final_state = apply_action_sequence(start_state, self.actions)
            if final_state is None: # Chuỗi hành động không hợp lệ cho trạng thái này
                total_heuristic_after_actions += 1000 # Phạt nặng
                continue

            if final_state == self.goal_state:
                num_solved += 1
            
            # Heuristic có thể dùng để hướng dẫn thêm, nhưng ở đây tập trung vào việc giải được
            # total_heuristic_after_actions += manhattan_distance(final_state, self.goal_state)


        # Fitness chính: tỷ lệ giải được + phạt độ dài
        # Mục tiêu là giải được tất cả các belief states
        if not self.belief_states: return 0.0

        solved_ratio = num_solved / len(self.belief_states)
        
        # Fitness = (Tỷ lệ giải được * trọng số lớn) - (Độ dài chuỗi * trọng số nhỏ)
        # Mục tiêu: Tối đa hóa tỷ lệ giải được, tối thiểu hóa độ dài nếu tỷ lệ bằng nhau
        fitness_score = (solved_ratio * 1000.0) - (len(self.actions) * 0.1)

        # Thưởng lớn nếu giải được tất cả
        if num_solved == len(self.belief_states):
             fitness_score += 500.0 / (1.0 + len(self.actions)) # Thưởng thêm cho đường ngắn

        return fitness_score

    def __lt__(self, other: 'SensorlessIndividual') -> bool:
        return self.fitness < other.fitness

    def __repr__(self) -> str:
        solved_count = 0
        if self.belief_states:
            for start_s in self.belief_states:
                final_s = apply_action_sequence(start_s, self.actions)
                if final_s == self.goal_state:
                    solved_count +=1
        return f"SensorlessInd(len={len(self.actions)}, solved={solved_count}/{len(self.belief_states)}, fitness={self.fitness:.2f})"

# --- Genetic Algorithm Components for Sensorless version ---
def initialize_sensorless_population(belief_states: List[State], goal_state: State, population_size: int, max_action_len: int) -> List[SensorlessIndividual]:
    population: List[SensorlessIndividual] = []
    possible_actions = ['Up', 'Down', 'Left', 'Right']
    for _ in range(population_size):
        seq_len = random.randint(1, max_action_len)
        actions = [random.choice(possible_actions) for _ in range(seq_len)]
        population.append(SensorlessIndividual(actions, belief_states, goal_state))
    return population

def selection_sensorless(population: List[SensorlessIndividual], num_parents: int) -> List[SensorlessIndividual]:
    population.sort(key=lambda ind: ind.fitness, reverse=True)
    return population[:num_parents]

def crossover_sensorless(parent1: SensorlessIndividual, parent2: SensorlessIndividual, belief_states: List[State], goal_state: State) -> Tuple[SensorlessIndividual, SensorlessIndividual]:
    actions1, actions2 = parent1.actions, parent2.actions
    len1, len2 = len(actions1), len(actions2)

    if len1 == 0 or len2 == 0: # Nếu một trong hai cha mẹ không có hành động
        return SensorlessIndividual(list(actions1), belief_states, goal_state), SensorlessIndividual(list(actions2), belief_states, goal_state)

    # Single-point crossover cho chuỗi hành động
    pt1 = random.randint(0, len1 -1) if len1 > 0 else 0
    pt2 = random.randint(0, len2 -1) if len2 > 0 else 0
    
    child_actions1 = actions1[:pt1] + actions2[pt2:]
    child_actions2 = actions2[:pt2] + actions1[pt1:]
    
    return SensorlessIndividual(child_actions1, belief_states, goal_state), SensorlessIndividual(child_actions2, belief_states, goal_state)

def mutate_sensorless(individual: SensorlessIndividual, mutation_rate: float, belief_states: List[State], goal_state: State) -> SensorlessIndividual:
    actions = list(individual.actions)
    if not actions and random.random() < mutation_rate: # Nếu chuỗi rỗng, có thể thêm 1 hành động
        actions.append(random.choice(['Up', 'Down', 'Left', 'Right']))
        return SensorlessIndividual(actions, belief_states, goal_state)

    if not actions: return individual


    for i in range(len(actions)):
        if random.random() < mutation_rate:
            # Chọn một loại đột biến
            mutation_type = random.choice(['change', 'insert', 'delete'])
            
            if mutation_type == 'change':
                actions[i] = random.choice(['Up', 'Down', 'Left', 'Right'])
            elif mutation_type == 'insert' and len(actions) < 50 : # Giới hạn độ dài tối đa
                insert_pos = random.randint(0, len(actions))
                actions.insert(insert_pos, random.choice(['Up', 'Down', 'Left', 'Right']))
            elif mutation_type == 'delete' and len(actions) > 1: # Phải còn ít nhất 1 hành động
                del_pos = random.randint(0, len(actions) - 1)
                del actions[del_pos]
                if not actions: # Nếu xóa hết, thêm lại 1 cái
                    actions.append(random.choice(['Up', 'Down', 'Left', 'Right']))
                    
    return SensorlessIndividual(actions, belief_states, goal_state)

# --- Main Sensorless Genetic Algorithm ---
def solve(start_state: State, # Sẽ được dùng để tạo belief_states
          goal_state: State,
          num_belief_states: int = 5,   # Số lượng trạng thái trong belief set
          belief_max_scramble: int = 10, # Số bước ngẫu nhiên tối đa để tạo belief states từ start_state
          population_size: int = 150,
          num_generations: int = 300,
          num_parents_mating: int = 40,
          mutation_rate: float = 0.1,
          max_initial_action_len: int = 20,
          elite_size: int = 10) -> Optional[ActionSequence]: # Trả về chuỗi hành động

    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    # 1. Tạo Belief States
    # Một cách đơn giản là tạo các biến thể của start_state
    belief_states: Set[State] = {start_state}
    temp_state = list(start_state)
    possible_actions = ['Up', 'Down', 'Left', 'Right']
    
    # Tạo các belief states bằng cách đi ngẫu nhiên từ start_state
    # hoặc có thể dùng các trạng thái khó từ một tập dữ liệu
    for _ in range(num_belief_states * 5): # Thử nhiều hơn để có được các state khác nhau
        if len(belief_states) >= num_belief_states:
            break
        current_s = start_state
        num_scrambles = random.randint(1, belief_max_scramble)
        path_to_scramble = [current_s]
        for _ in range(num_scrambles):
            applied_s = apply_action_sequence(current_s, [random.choice(possible_actions)])
            if applied_s and applied_s not in path_to_scramble: # Tránh vòng lặp nhỏ
                current_s = applied_s
                path_to_scramble.append(current_s)
            else: # Nếu không di chuyển được, thử lại hành động khác hoặc dừng
                break 
        if current_s != start_state: # Chỉ thêm nếu nó khác trạng thái ban đầu
            belief_states.add(current_s)

    final_belief_states = list(belief_states)
    if not final_belief_states: # Đảm bảo có ít nhất start_state
        final_belief_states = [start_state]

    print(f"Sensorless GA using {len(final_belief_states)} belief states. First few: {final_belief_states[:3]}")


    # 2. Khởi tạo quần thể
    population = initialize_sensorless_population(final_belief_states, goal_state, population_size, max_initial_action_len)
    best_solution_overall: Optional[SensorlessIndividual] = None

    for generation in range(num_generations):
        population.sort(key=lambda ind: ind.fitness, reverse=True)

        current_best_in_gen = population[0]
        
        is_current_best_a_solution = True
        if not current_best_in_gen.actions: is_current_best_a_solution = False
        else:
            for b_state in final_belief_states:
                if apply_action_sequence(b_state, current_best_in_gen.actions) != goal_state:
                    is_current_best_a_solution = False
                    break
        
        if is_current_best_a_solution:
            if best_solution_overall is None or len(current_best_in_gen.actions) < len(best_solution_overall.actions):
                best_solution_overall = current_best_in_gen
                print(f"Sensorless Gen {generation}: Found a universal sequence! Len: {len(best_solution_overall.actions)}, Fitness: {best_solution_overall.fitness:.2f}")
                # return best_solution_overall.actions # Dừng sớm nếu muốn

        if generation % 20 == 0:
            print(f"Sensorless Gen {generation}: Best fitness = {population[0].fitness:.2f}, Seq len = {len(population[0].actions)}")

        # Tạo thế hệ mới
        next_generation: List[SensorlessIndividual] = []
        if elite_size > 0:
            next_generation.extend(population[:elite_size])

        parents = selection_sensorless(population, num_parents_mating)
        if not parents: parents = population[:max(1, num_parents_mating)]


        num_offspring_needed = population_size - len(next_generation)
        offspring_created_count = 0
        attempts_to_create_offspring = 0
        max_attempts = num_offspring_needed * 5

        while offspring_created_count < num_offspring_needed and attempts_to_create_offspring < max_attempts:
            attempts_to_create_offspring +=1
            if len(parents) < 2:
                p1 = random.choice(population) if population else SensorlessIndividual([], final_belief_states, goal_state)
                p2 = random.choice(population) if population else SensorlessIndividual([], final_belief_states, goal_state)

            else:
                p1, p2 = random.sample(parents, 2)

            child1, child2 = crossover_sensorless(p1, p2, final_belief_states, goal_state)
            
            mutated_child1 = mutate_sensorless(child1, mutation_rate, final_belief_states, goal_state)
            mutated_child2 = mutate_sensorless(child2, mutation_rate, final_belief_states, goal_state)

            next_generation.append(mutated_child1)
            offspring_created_count +=1
            if offspring_created_count < num_offspring_needed:
                 next_generation.append(mutated_child2)
                 offspring_created_count +=1
        
        while len(next_generation) < population_size:
            if population: next_generation.append(random.choice(population))
            else: next_generation.append(SensorlessIndividual([], final_belief_states, goal_state))

        population = next_generation[:population_size]

    if best_solution_overall:
        print(f"Sensorless GA finished. Best universal sequence length: {len(best_solution_overall.actions)}")
        # Để phù hợp với cấu trúc trả về của các thuật toán khác, 
        # chúng ta cần chuyển chuỗi hành động này thành một "đường đi" các trạng thái
        # bằng cách áp dụng nó vào start_state ban đầu.
        final_path: List[State] = [start_state]
        current_s_for_path = start_state
        for act in best_solution_overall.actions:
            next_s_for_path = apply_action_sequence(current_s_for_path, [act])
            if next_s_for_path:
                final_path.append(next_s_for_path)
                current_s_for_path = next_s_for_path
            else: # Lỗi không mong muốn nếu chuỗi đã được xác minh
                print("Error: Best action sequence failed on original start_state during path reconstruction.")
                return None 
        return final_path # Trả về đường đi kết quả khi áp dụng lên start_state gốc
    
    population.sort(key=lambda ind: ind.fitness, reverse=True)
    print(f"Sensorless GA finished. No universal sequence found. Best fitness: {population[0].fitness:.2f} with seq len {len(population[0].actions)}")
    return None 