import random
from typing import List, Tuple, Optional, Dict, Set
import copy # For deep copying states if needed

# Định nghĩa kiểu dữ liệu cho trạng thái (một tuple các số nguyên)
State = Tuple[int, ...]
Move = str # e.g., 'Up', 'Left', 'Down_Double_Right' (if we encode double moves like this)
Chromosome = List[Move] # A sequence of moves

# --- Heuristic Function (Manhattan Distance) ---
def manhattan_distance(state: State, goal_state: State) -> int:
    """
    Tính tổng khoảng cách Manhattan cho tất cả các ô (trừ ô trống)
    đến vị trí mục tiêu của chúng.
    """
    total = 0
    try:
        size = int(len(state)**0.5)
        if size * size != len(state) or len(goal_state) != len(state):
            return float('inf') 
        blank_tile = size * size
    except TypeError:
        return float('inf')

    goal_map = {tile: i for i, tile in enumerate(goal_state)}

    for i in range(len(state)):
        tile = state[i]
        if tile != blank_tile:
            current_row, current_col = divmod(i, size)
            goal_pos = goal_map.get(tile)
            if goal_pos is None:
                return float('inf')
            goal_row, goal_col = divmod(goal_pos, size)
            total += abs(current_row - goal_row) + abs(current_col - goal_col)
    return total

# --- Move Application and Neighbor Generation Logic ---

def apply_single_move(state: State, move: str) -> Optional[State]:
    """Applies a single move (Up, Down, Left, Right) to a state."""
    s_list = list(state)
    size = int(len(state)**0.5)
    blank_tile = size * size
    try:
        blank_index = s_list.index(blank_tile)
    except ValueError:
        return None  # Should not happen if state is valid

    row, col = divmod(blank_index, size)
    dr, dc = 0, 0
    if move == 'Up': dr = -1
    elif move == 'Down': dr = 1
    elif move == 'Left': dc = -1
    elif move == 'Right': dc = -1 # Corrected: dc = 1 for Right
    else: return None # Invalid single move string

    if move == 'Right': dc = 1 # Explicit correction here too


    new_row, new_col = row + dr, col + dc

    if 0 <= new_row < size and 0 <= new_col < size:
        new_index = new_row * size + new_col
        s_list[blank_index], s_list[new_index] = s_list[new_index], s_list[blank_index]
        return tuple(s_list)
    return None


POSSIBLE_SINGLE_MOVES = ['Up', 'Down', 'Left', 'Right']

def get_possible_moves_from_state(state: State) -> List[Tuple[Move, State, int]]:
    """
    Generates all possible next moves (single and double) from the current state.
    Returns a list of tuples: (move_name_str, next_state_tuple, move_cost)
    """
    possible_moves_details = []
    current_s_list = list(state)
    size = int(len(state)**0.5)
    blank_tile = size * size
    
    try:
        original_blank_idx = current_s_list.index(blank_tile)
    except ValueError:
        return [] # Invalid state

    # 1. Single Moves
    single_move_successors = [] # Store (move_name, resulting_state, new_blank_idx)
    for move1_name in POSSIBLE_SINGLE_MOVES:
        next_state_s1 = apply_single_move(state, move1_name)
        if next_state_s1:
            possible_moves_details.append((move1_name, next_state_s1, 1))
            try:
                new_blank_idx_s1 = list(next_state_s1).index(blank_tile)
                single_move_successors.append((move1_name, next_state_s1, new_blank_idx_s1))
            except ValueError:
                continue # Should not happen if apply_single_move worked

    # 2. Double Moves (derived from single moves)
    for move1_name, state_s1, blank_idx_s1 in single_move_successors:
        for move2_name in POSSIBLE_SINGLE_MOVES:
            # Prevent immediate reversal for the second part of a double move
            # e.g., if move1 was 'Up', move2 shouldn't be 'Down' if it brings blank back
            temp_state_after_move2_check = apply_single_move(state_s1, move2_name)
            if temp_state_after_move2_check == state: # This move would undo the first part
                continue

            next_state_s2 = apply_single_move(state_s1, move2_name)
            if next_state_s2:
                # Check if this double move results in the same state as the original start_state
                # This is a bit tricky, the main check is that the blank tile doesn't return to original_blank_idx directly
                
                # A simpler check: ensure the blank's final position after two moves isn't its starting position.
                try:
                    final_blank_idx_s2 = list(next_state_s2).index(blank_tile)
                    if final_blank_idx_s2 == original_blank_idx and move1_name != move2_name : # Avoid A-B-A if moves are different
                        # This logic can be complex. The core idea is that a "double move"
                        # should be a meaningful progression, not just shuffling back and forth.
                        # For now, we rely on the cost and fitness to sort this out,
                        # but a strict definition might disallow A-B-A type double moves.
                        # Let's allow it but it will have cost 2.
                        pass

                except ValueError:
                    continue
                
                double_move_name = f"{move1_name}_Then_{move2_name}"
                possible_moves_details.append((double_move_name, next_state_s2, 2))
                
    return possible_moves_details


# --- Genetic Algorithm Components ---

def generate_initial_population(pop_size: int, initial_max_len: int, start_state: State) -> List[Chromosome]:
    """Generates an initial population of random move sequences."""
    population: List[Chromosome] = []
    for _ in range(pop_size):
        chromosome_len = random.randint(1, initial_max_len)
        chromosome: Chromosome = []
        current_state_for_chromosome_gen = start_state
        
        for _ in range(chromosome_len):
            # Get valid moves from current_state_for_chromosome_gen
            # This ensures chromosomes are at least sequences of valid *consecutive* moves
            # though not necessarily optimal or leading to the goal.
            valid_next_steps = get_possible_moves_from_state(current_state_for_chromosome_gen)
            if not valid_next_steps:
                break # Cannot make more moves from this state

            # Choose a random move (can be single or double)
            move_name, next_s, _ = random.choice(valid_next_steps)
            chromosome.append(move_name)
            current_state_for_chromosome_gen = next_s
            
        if chromosome: # Only add if at least one move was made
            population.append(chromosome)
    # If population is empty after trying, add at least one minimal random valid path
    if not population and pop_size > 0:
        valid_next_steps = get_possible_moves_from_state(start_state)
        if valid_next_steps:
            move_name, _, _ = random.choice(valid_next_steps)
            population.append([move_name])

    return population


def calculate_fitness(chromosome: Chromosome, start_state: State, goal_state: State) -> Tuple[int, int]:
    """
    Calculates the fitness of a chromosome.
    Returns: (manhattan_distance_to_goal, total_move_cost)
    Lower Manhattan distance is better. Lower cost is better.
    """
    current_state = start_state
    total_cost = 0
    path_is_valid = True

    for move_str in chromosome:
        temp_state = current_state
        cost_this_move = 0

        if "_Then_" in move_str: # Double move
            parts = move_str.split("_Then_")
            if len(parts) == 2:
                move1, move2 = parts[0], parts[1]
                s1 = apply_single_move(temp_state, move1)
                if s1:
                    current_state = apply_single_move(s1, move2)
                    cost_this_move = 2
                else: # First part of double move failed
                    current_state = None
            else: # Malformed double move string
                current_state = None
        else: # Single move
            current_state = apply_single_move(temp_state, move_str)
            cost_this_move = 1

        if current_state is None: # Invalid move sequence
            path_is_valid = False
            break
        total_cost += cost_this_move

    if not path_is_valid or current_state is None: # Penalize invalid paths heavily
        return (float('inf'), float('inf'))

    dist = manhattan_distance(current_state, goal_state)
    return (dist, total_cost)


def selection(population: List[Chromosome], fitnesses: List[Tuple[int,int]], tournament_size: int) -> Chromosome:
    """Performs tournament selection."""
    tournament: List[Tuple[Chromosome, Tuple[int,int]]] = random.sample(list(zip(population, fitnesses)), tournament_size)
    # Sort by Manhattan distance (primary), then by cost (secondary)
    tournament.sort(key=lambda x: (x[1][0], x[1][1]))
    return tournament[0][0] # Return the best chromosome from the tournament


def crossover(parent1: Chromosome, parent2: Chromosome, crossover_rate: float) -> Tuple[Chromosome, Chromosome]:
    """Performs single-point crossover if rate allows."""
    if random.random() < crossover_rate:
        if not parent1 or not parent2: # Handle empty parents
            return parent1[:], parent2[:]
        
        min_len = min(len(parent1), len(parent2))
        if min_len <= 1: # Not enough length to crossover meaningfully
             return parent1[:], parent2[:]

        point = random.randint(1, min_len -1) # Ensure point is not at the very start/end
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    return parent1[:], parent2[:] # Return copies of parents if no crossover


def mutate(chromosome: Chromosome, mutation_rate: float, max_path_deviation: int, start_state_for_validation: State) -> Chromosome:
    """
    Performs mutation on a chromosome.
    Types of mutation:
    1. Change a move.
    2. Add a random valid move (single or double).
    3. Delete a move.
    Ensures the mutated path doesn't deviate too much in length.
    """
    mutated_chromosome = chromosome[:] # Work on a copy
    original_len = len(mutated_chromosome)

    if random.random() < mutation_rate: # Mutate a single gene (move)
        if mutated_chromosome:
            idx_to_mutate = random.randrange(len(mutated_chromosome))
            
            # To pick a new valid move, we need to know the state *before* this move
            temp_state = start_state_for_validation
            valid_path_so_far = True
            for i in range(idx_to_mutate):
                move_str = mutated_chromosome[i]
                prev_temp_state = temp_state
                if "_Then_" in move_str:
                    parts = move_str.split("_Then_")
                    s1 = apply_single_move(prev_temp_state, parts[0])
                    if s1: temp_state = apply_single_move(s1, parts[1])
                    else: valid_path_so_far = False; break
                else:
                    temp_state = apply_single_move(prev_temp_state, move_str)
                if temp_state is None: valid_path_so_far = False; break
            
            if valid_path_so_far and temp_state is not None:
                possible_new_moves = get_possible_moves_from_state(temp_state)
                if possible_new_moves:
                    new_move_name, _, _ = random.choice(possible_new_moves)
                    mutated_chromosome[idx_to_mutate] = new_move_name

    if random.random() < mutation_rate * 0.5 : # Add a move (lower probability)
        if len(mutated_chromosome) < original_len + max_path_deviation :
            # Find state at a random point to insert a new valid move
            insert_idx = random.randint(0, len(mutated_chromosome))
            temp_state = start_state_for_validation
            valid_path_so_far = True
            for i in range(insert_idx):
                move_str = mutated_chromosome[i]
                prev_temp_state = temp_state
                if "_Then_" in move_str:
                    parts = move_str.split("_Then_")
                    s1 = apply_single_move(prev_temp_state, parts[0])
                    if s1: temp_state = apply_single_move(s1, parts[1])
                    else: valid_path_so_far = False; break
                else:
                    temp_state = apply_single_move(prev_temp_state, move_str)
                if temp_state is None: valid_path_so_far = False; break

            if valid_path_so_far and temp_state is not None:
                possible_new_moves = get_possible_moves_from_state(temp_state)
                if possible_new_moves:
                    new_move_name, _, _ = random.choice(possible_new_moves)
                    mutated_chromosome.insert(insert_idx, new_move_name)

    if random.random() < mutation_rate * 0.5: # Delete a move (lower probability)
        if mutated_chromosome and len(mutated_chromosome) > max(1, original_len - max_path_deviation):
            del_idx = random.randrange(len(mutated_chromosome))
            del mutated_chromosome[del_idx]
            
    return mutated_chromosome


def reconstruct_path_from_moves(start_state: State, moves: Chromosome) -> Optional[List[State]]:
    """Reconstructs the state path given a sequence of moves."""
    path: List[State] = [start_state]
    current_state = start_state
    for move_str in moves:
        next_state = None
        if "_Then_" in move_str:
            parts = move_str.split("_Then_")
            if len(parts) == 2:
                s1 = apply_single_move(current_state, parts[0])
                if s1: next_state = apply_single_move(s1, parts[1])
        else:
            next_state = apply_single_move(current_state, move_str)

        if next_state is None:
            # print(f"Warning: Invalid move '{move_str}' from state {current_state} during path reconstruction.")
            return None # Invalid move sequence found
        current_state = next_state
        path.append(current_state)
    return path


# --- Main GA Solver ---
def solve(start_state: State, goal_state: State) -> Optional[List[State]]:
    """
    Attempts to find a path from start_state to goal_state using a Genetic Algorithm.
    Allows both single (cost 1) and double (cost 2) moves.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if len(start_state) != len(goal_state) or int(len(start_state)**0.5)**2 != len(start_state):
        # print("Lỗi: Trạng thái bắt đầu hoặc kết thúc không hợp lệ.")
        return None

    # GA Parameters
    POPULATION_SIZE = 100       # Number of individuals in the population
    MAX_GENERATIONS = 200       # Number of generations to run
    INITIAL_MAX_CHROMOSOME_LEN = 25 # Max length of initial random move sequences
    TOURNAMENT_SIZE = 5         # For selection
    CROSSOVER_RATE = 0.75
    MUTATION_RATE = 0.20        # Per-chromosome mutation probability
    MAX_PATH_DEVIATION_MUTATION = 3 # How much a path length can change due to add/delete mutation
    ELITISM_COUNT = 2           # Number of best individuals to carry to next generation

    # Initialize population
    population = generate_initial_population(POPULATION_SIZE, INITIAL_MAX_CHROMOSOME_LEN, start_state)
    if not population:
        # print("Không thể tạo population ban đầu hợp lệ.")
        return None

    best_overall_chromosome: Optional[Chromosome] = None
    best_overall_fitness: Tuple[int, int] = (float('inf'), float('inf'))

    for generation in range(MAX_GENERATIONS):
        # Calculate fitness for each individual
        fitnesses: List[Tuple[int, int]] = []
        for chromo in population:
            fitness_val = calculate_fitness(chromo, start_state, goal_state)
            fitnesses.append(fitness_val)

        # Check for solution and find best in current generation
        current_gen_best_fitness = (float('inf'), float('inf'))
        current_gen_best_chromosome = None

        for i, chromo in enumerate(population):
            dist, cost = fitnesses[i]
            if dist == 0: # Solution found!
                # print(f"Giải pháp được tìm thấy ở thế hệ {generation}!")
                # print(f"Chromosome: {chromo}, Chi phí: {cost}")
                return reconstruct_path_from_moves(start_state, chromo)
            
            if (dist < current_gen_best_fitness[0]) or \
               (dist == current_gen_best_fitness[0] and cost < current_gen_best_fitness[1]):
                current_gen_best_fitness = (dist, cost)
                current_gen_best_chromosome = chromo
        
        # Update overall best
        if (current_gen_best_fitness[0] < best_overall_fitness[0]) or \
           (current_gen_best_fitness[0] == best_overall_fitness[0] and current_gen_best_fitness[1] < best_overall_fitness[1]):
            best_overall_fitness = current_gen_best_fitness
            best_overall_chromosome = current_gen_best_chromosome
            # print(f"Gen {generation}: Best Fitness (Dist,Cost): {best_overall_fitness}, Path len: {len(best_overall_chromosome) if best_overall_chromosome else 0}")


        # Create new population
        new_population: List[Chromosome] = []

        # Elitism: Carry over the best individuals
        if ELITISM_COUNT > 0 and current_gen_best_chromosome is not None:
            # More robust elitism: sort all by fitness and take top N
            sorted_population_with_fitness = sorted(zip(population, fitnesses), key=lambda x: (x[1][0], x[1][1]))
            for i in range(min(ELITISM_COUNT, len(sorted_population_with_fitness))):
                new_population.append(sorted_population_with_fitness[i][0][:]) # Add copy

        # Fill the rest of the new population
        while len(new_population) < POPULATION_SIZE:
            parent1 = selection(population, fitnesses, TOURNAMENT_SIZE)
            parent2 = selection(population, fitnesses, TOURNAMENT_SIZE)
            
            child1, child2 = crossover(parent1, parent2, CROSSOVER_RATE)
            
            child1_mutated = mutate(child1, MUTATION_RATE, MAX_PATH_DEVIATION_MUTATION, start_state)
            child2_mutated = mutate(child2, MUTATION_RATE, MAX_PATH_DEVIATION_MUTATION, start_state)
            
            if child1_mutated: new_population.append(child1_mutated)
            if len(new_population) < POPULATION_SIZE and child2_mutated:
                new_population.append(child2_mutated)
        
        population = new_population
        if not population : # Should not happen if elitism or generation works
            # print("Population became empty. Stopping.")
            break 

    # If no solution found after all generations, return the best path found so far
    # print(f"GA hoàn thành. Fitness tốt nhất (Dist,Cost): {best_overall_fitness}")
    if best_overall_chromosome:
        # print(f"Đang thử xây dựng lại đường đi từ chromosome tốt nhất...")
        # This path might not reach the goal state, but it's the "best effort"
        return reconstruct_path_from_moves(start_state, best_overall_chromosome)
        
    return None

# Example usage (optional, for direct testing of this file)
if __name__ == '__main__':
    # Standard 8-puzzle goal
    goal = (1, 2, 3, 4, 5, 6, 7, 8, 9) # 9 is blank

    # Solvable start states
    # start1 = (1, 2, 3, 4, 5, 6, 7, 9, 8) # 1 move away (R)
    # start2 = (1, 2, 3, 4, 5, 9, 7, 6, 8) # 2 moves away (D, R) or (R, D)
    start3 = (1, 2, 3, 9, 4, 5, 7, 8, 6) # A few moves away
    start4 = (2, 8, 3, 1, 9, 4, 7, 6, 5) # More complex, solvable
    
    # Unsolvable start state for testing (should ideally be caught by is_solvable in main.py)
    # start_unsolvable = (1, 2, 3, 4, 5, 6, 8, 7, 9)


    test_start_state = start4
    print(f"Bắt đầu tìm kiếm từ: {test_start_state}")
    print(f"Trạng thái đích: {goal}")

    solution_path = solve(test_start_state, goal)

    if solution_path:
        print(f"Tìm thấy đường đi với {len(solution_path) - 1} bước (bao gồm cả trạng thái bắt đầu):")
        final_state = solution_path[-1]
        final_dist = manhattan_distance(final_state, goal)
        print(f"Trạng thái cuối cùng: {final_state}, Manhattan đến đích: {final_dist}")
        # for i, p_state in enumerate(solution_path):
        #     print(f"Bước {i}: {p_state}")
    else:
        print("Không tìm thấy giải pháp.")