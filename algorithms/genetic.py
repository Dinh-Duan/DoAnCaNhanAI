# algorithms/genetic.py
import random
from heapq import heappush, heappop
from typing import List, Tuple, Optional, Dict, Set

State = Tuple[int, ...]

# --- Các hàm heuristic và neighbors (có thể copy từ a_star.py hoặc định nghĩa lại) ---
def manhattan_distance(state: State, goal_state: State) -> int:
    """Tính tổng khoảng cách Manhattan."""
    total = 0
    size = int(len(state)**0.5)
    blank_tile = size * size
    goal_map = {tile: i for i, tile in enumerate(goal_state)}
    for i in range(len(state)):
        tile = state[i]
        if tile != blank_tile:
            current_row, current_col = divmod(i, size)
            goal_pos = goal_map.get(tile)
            if goal_pos is None: return float('inf')
            goal_row, goal_col = divmod(goal_pos, size)
            total += abs(current_row - goal_row) + abs(current_col - goal_col)
    return total

def get_neighbors(state: State) -> List[State]:
    """Lấy các trạng thái hàng xóm (di chuyển đơn)."""
    neighbors: List[State] = []
    s_list = list(state)
    size = int(len(state)**0.5)
    blank_tile = size * size
    try:
        blank_index = s_list.index(blank_tile)
    except ValueError:
        return []
    row, col = divmod(blank_index, size)
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < size and 0 <= new_col < size:
            new_index = new_row * size + new_col
            new_s = s_list[:]
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbors.append(tuple(new_s))
    return neighbors

# --- Các thành phần của Genetic Algorithm ---

# Individual: Đại diện cho một đường đi (chuỗi các trạng thái)
class Individual:
    def __init__(self, path: List[State], goal_state: State):
        self.path: List[State] = path
        self.goal_state: State = goal_state
        self.fitness: float = self._calculate_fitness()

    def _calculate_fitness(self) -> float:
        """
        Tính độ thích nghi.
        Fitness cao hơn là tốt hơn (heuristic thấp hơn, đường đi ngắn hơn).
        """
        if not self.path:
            return -float('inf')
        
        last_state = self.path[-1]
        heuristic_to_goal = manhattan_distance(last_state, self.goal_state)
        
        # Ưu tiên heuristic gần 0 và đường đi ngắn
        # Tránh chia cho 0 nếu heuristic_to_goal là 0
        fitness_score = 1.0 / (1.0 + heuristic_to_goal + 0.1 * len(self.path))

        # Nếu đã đạt đích, fitness rất cao
        if last_state == self.goal_state:
            fitness_score += 1000.0 / (1.0 + len(self.path)) # Thưởng thêm cho đường ngắn đến đích
        
        return fitness_score

    def __lt__(self, other: 'Individual') -> bool:
        # Dùng cho sắp xếp (ví dụ trong selection)
        return self.fitness < other.fitness # Fitness cao hơn là tốt hơn

    def __repr__(self) -> str:
        return f"Individual(len={len(self.path)}, fitness={self.fitness:.4f}, last_state={self.path[-1] if self.path else 'None'})"

def initialize_population(start_state: State, goal_state: State, population_size: int, max_initial_path_len: int) -> List[Individual]:
    """Tạo quần thể ban đầu bằng cách thực hiện các bước đi ngẫu nhiên."""
    population: List[Individual] = []
    for _ in range(population_size):
        current_state = start_state
        path = [current_state]
        path_len = random.randint(1, max_initial_path_len)
        for _ in range(path_len):
            neighbors = get_neighbors(current_state)
            if not neighbors:
                break
            current_state = random.choice(neighbors)
            path.append(current_state)
            if current_state == goal_state: # Dừng sớm nếu tìm thấy đích
                break
        population.append(Individual(path, goal_state))
    return population

def selection(population: List[Individual], num_parents: int) -> List[Individual]:
    """Chọn các cá thể tốt nhất làm cha mẹ (Tournament selection hoặc Roulette wheel)."""
    # Đơn giản: Chọn num_parents cá thể có fitness cao nhất
    population.sort(key=lambda ind: ind.fitness, reverse=True) # Sắp xếp giảm dần theo fitness
    return population[:num_parents]

def crossover(parent1: Individual, parent2: Individual, goal_state: State) -> Tuple[Individual, Individual]:
    """
    Lai ghép hai cá thể cha mẹ để tạo ra con.
    Tìm điểm chung gần nhất từ cuối, rồi nối phần còn lại.
    """
    path1, path2 = parent1.path, parent2.path
    
    # Tìm điểm giao nhau từ đầu path (common prefix)
    len1, len2 = len(path1), len(path2)
    min_len = min(len1, len2)
    crossover_point = 0
    for i in range(min_len):
        if path1[i] == path2[i]:
            crossover_point = i + 1
        else:
            break
            
    if crossover_point == 0: # Không có điểm chung nào từ đầu -> trả về bản sao của cha mẹ
        child1_path = list(path1)
        child2_path = list(path2)
    else:
        # Child 1: Phần đầu của parent1 + phần sau của parent2 (tính từ điểm giao)
        child1_path = path1[:crossover_point] + path2[crossover_point:]
        # Child 2: Phần đầu của parent2 + phần sau của parent1 (tính từ điểm giao)
        child2_path = path2[:crossover_point] + path1[crossover_point:]

    # Loại bỏ các vòng lặp đơn giản nếu có
    child1_path = remove_loops(child1_path)
    child2_path = remove_loops(child2_path)
    
    return Individual(child1_path, goal_state), Individual(child2_path, goal_state)

def remove_loops(path: List[State]) -> List[State]:
    """Loại bỏ các vòng lặp đơn giản trong đường đi."""
    if not path: return []
    # Đi từ đầu, nếu gặp lại trạng thái đã có, cắt bỏ đoạn giữa
    final_path = []
    visited_in_path_indices: Dict[State, int] = {}
    for i, state in enumerate(path):
        if state in visited_in_path_indices:
            # Tìm thấy vòng lặp, cắt bỏ từ lần xuất hiện trước đó
            loop_start_index = visited_in_path_indices[state]
            # Xóa các trạng thái trong vòng lặp khỏi visited_in_path_indices và final_path
            states_to_remove_from_visited = final_path[loop_start_index:]
            for s_rem in states_to_remove_from_visited:
                if s_rem in visited_in_path_indices: # Cẩn thận nếu state đó là điểm bắt đầu vòng lặp
                     del visited_in_path_indices[s_rem]

            final_path = final_path[:loop_start_index]
            # Thêm lại trạng thái hiện tại (điểm bắt đầu/kết thúc vòng lặp)
            final_path.append(state)
            visited_in_path_indices[state] = len(final_path) -1
        else:
            final_path.append(state)
            visited_in_path_indices[state] = len(final_path) -1
    return final_path


def mutate(individual: Individual, mutation_rate: float, goal_state: State, max_mutation_steps: int) -> Individual:
    """
    Đột biến cá thể bằng cách thay đổi một phần đường đi.
    Có thể chọn một điểm ngẫu nhiên và thực hiện các bước đi ngẫu nhiên từ đó.
    """
    if random.random() < mutation_rate:
        path = list(individual.path) # Tạo bản sao để thay đổi
        if not path: return individual # Không có gì để đột biến

        mutation_point_index = random.randint(0, len(path) - 1)
        current_state = path[mutation_point_index]
        
        # Cắt bỏ phần sau điểm đột biến
        mutated_path_segment = [current_state] # Bắt đầu lại từ điểm đột biến
        
        num_mutation_steps = random.randint(1, max_mutation_steps)
        
        for _ in range(num_mutation_steps):
            neighbors = get_neighbors(current_state)
            if not neighbors:
                break
            # Tránh quay lại trạng thái തൊട്ടു മുമ്പത്തെ (nếu có thể)
            prev_state = mutated_path_segment[-2] if len(mutated_path_segment) > 1 else None
            possible_next_moves = [n for n in neighbors if n != prev_state]
            if not possible_next_moves: possible_next_moves = neighbors # Nếu chỉ có 1 lựa chọn là quay lại

            current_state = random.choice(possible_next_moves)
            mutated_path_segment.append(current_state)
            if current_state == goal_state: # Dừng nếu đến đích
                break
        
        # Nối lại đường đi
        final_path = path[:mutation_point_index] + mutated_path_segment
        final_path = remove_loops(final_path) # Dọn dẹp lại
        return Individual(final_path, goal_state)
        
    return individual

# --- Thuật toán chính ---
def solve(start_state: State, goal_state: State,
          population_size: int = 100,
          num_generations: int = 200,
          num_parents_mating: int = 30, # Số lượng cha mẹ được chọn để lai ghép
          mutation_rate: float = 0.15,
          max_initial_path_len: int = 25, # Độ dài tối đa của đường đi ban đầu
          max_mutation_steps: int = 5, # Số bước ngẫu nhiên tối đa khi đột biến
          elite_size: int = 5) -> Optional[List[State]]: # Giữ lại elite_size cá thể tốt nhất
    """
    Giải 8-Puzzle bằng thuật toán di truyền.
    Trả về đường đi (list các State) hoặc None.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if start_state == goal_state:
        return [start_state]

    population = initialize_population(start_state, goal_state, population_size, max_initial_path_len)
    
    best_solution_overall: Optional[Individual] = None

    for generation in range(num_generations):
        # Tính fitness cho cả quần thể (đã làm trong constructor Individual)
        # Sắp xếp quần thể theo fitness giảm dần
        population.sort(key=lambda ind: ind.fitness, reverse=True)

        # Kiểm tra giải pháp tốt nhất hiện tại
        current_best_in_gen = population[0]
        if current_best_in_gen.path and current_best_in_gen.path[-1] == goal_state:
            if best_solution_overall is None or len(current_best_in_gen.path) < len(best_solution_overall.path):
                best_solution_overall = current_best_in_gen
                print(f"Gen {generation}: Found goal! Path len: {len(best_solution_overall.path)}, Fitness: {best_solution_overall.fitness:.3f}")
                # Có thể dừng sớm ở đây nếu muốn, hoặc tiếp tục để tìm đường ngắn hơn
                # return best_solution_overall.path # Dừng sớm

        if best_solution_overall and best_solution_overall.path[-1] == goal_state:
            # Nếu đã tìm thấy đích, có thể giảm mutation rate hoặc tập trung vào tối ưu đường đi
            pass


        if generation % 20 == 0:
            print(f"Generation {generation}: Best fitness = {population[0].fitness:.4f}, Path len = {len(population[0].path)}, Last state = {population[0].path[-1] if population[0].path else 'N/A'}")

        # --- Tạo thế hệ mới ---
        next_generation: List[Individual] = []

        # 1. Elitism: Giữ lại một số cá thể tốt nhất
        if elite_size > 0:
            next_generation.extend(population[:elite_size])

        # 2. Selection: Chọn cha mẹ từ quần thể hiện tại
        parents = selection(population, num_parents_mating)
        if not parents: # Nếu không chọn được cha mẹ nào (quần thể quá nhỏ hoặc lỗi)
            parents = population[:max(1, num_parents_mating)] # Lấy tạm vài cá thể đầu

        # 3. Crossover and Mutation để tạo con cái cho phần còn lại của quần thể
        num_offspring_needed = population_size - len(next_generation)
        
        offspring_created_count = 0
        attempts_to_create_offspring = 0
        max_attempts = num_offspring_needed * 5 # Giới hạn số lần thử tạo con

        while offspring_created_count < num_offspring_needed and attempts_to_create_offspring < max_attempts:
            attempts_to_create_offspring +=1
            # Chọn ngẫu nhiên 2 cha mẹ từ danh sách parents
            if len(parents) < 2: # Cần ít nhất 2 cha mẹ để lai
                # Nếu không đủ, có thể dùng lại cá thể tốt nhất hoặc tạo ngẫu nhiên
                if population:
                    p1 = random.choice(population)
                    p2 = random.choice(population)
                else: # Trường hợp quần thể rỗng (không nên xảy ra)
                    break
            else:
                p1, p2 = random.sample(parents, 2)

            child1, child2 = crossover(p1, p2, goal_state)
            
            mutated_child1 = mutate(child1, mutation_rate, goal_state, max_mutation_steps)
            mutated_child2 = mutate(child2, mutation_rate, goal_state, max_mutation_steps)

            if mutated_child1.path: # Chỉ thêm nếu path hợp lệ
                 next_generation.append(mutated_child1)
                 offspring_created_count +=1
            if offspring_created_count < num_offspring_needed and mutated_child2.path:
                 next_generation.append(mutated_child2)
                 offspring_created_count +=1
        
        # Nếu không tạo đủ con, có thể bổ sung bằng cách copy từ elite hoặc parents
        while len(next_generation) < population_size:
            if population:
                next_generation.append(random.choice(population)) # Lấy ngẫu nhiên từ quần thể cũ
            else: # Quần thể cũ rỗng, tạo mới
                next_generation.append(Individual([start_state], goal_state))


        population = next_generation[:population_size] # Đảm bảo kích thước quần thể

    # Sau tất cả các thế hệ, trả về giải pháp tốt nhất tìm được
    if best_solution_overall and best_solution_overall.path and best_solution_overall.path[-1] == goal_state:
        print(f"Genetic Algorithm finished. Best path len: {len(best_solution_overall.path)}")
        return best_solution_overall.path
    
    # Nếu không tìm thấy đích, có thể trả về đường đi gần nhất
    # Sắp xếp lại lần cuối
    population.sort(key=lambda ind: ind.fitness, reverse=True)
    if population and population[0].path:
         print(f"Genetic Algorithm finished. No exact goal found. Best heuristic to goal: {manhattan_distance(population[0].path[-1], goal_state)}")
         # return population[0].path # Trả về đường đi "tốt nhất" dù không tới đích
         return None # Hoặc chỉ trả về None nếu không đạt đích
    
    print("Genetic Algorithm finished. No solution found.")
    return None

# Ví dụ cách gọi (để test):
if __name__ == '__main__':
    # Lưu ý: Genetic Algorithm có thể cần nhiều thế hệ và population lớn để giải 8-puzzle
    # các tham số này cần được tinh chỉnh.
    
    # Ví dụ 1: Gần đích
    # start = (1, 2, 3, 4, 5, 6, 7, 9, 8)
    # goal =  (1, 2, 3, 4, 5, 6, 7, 8, 9)

    # Ví dụ 2: Khó hơn một chút
    start = (1, 2, 3, 4, 9, 5, 7, 8, 6)
    goal =  (1, 2, 3, 4, 5, 6, 7, 8, 9)

    # Ví dụ 3: Xa hơn
    # start = (8, 1, 2, 9, 4, 3, 7, 6, 5) # Solvable
    # goal = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    print(f"Starting GA for: {start} -> {goal}")
    
    solution_path = solve(start, goal,
                            population_size=200,        # Tăng kích thước quần thể
                            num_generations=500,      # Tăng số thế hệ
                            num_parents_mating=60,    # Tăng số cha mẹ
                            mutation_rate=0.2,        # Tăng tỷ lệ đột biến một chút
                            max_initial_path_len=20,  # Giữ nguyên hoặc giảm nhẹ
                            max_mutation_steps=4,     # Giữ nguyên
                            elite_size=10)            # Tăng elite size
    
    if solution_path:
        print("\nSolution Path Found:")
        for i, s in enumerate(solution_path):
            print(f"Step {i}: {s}")
    else:
        print("\nNo solution found.")