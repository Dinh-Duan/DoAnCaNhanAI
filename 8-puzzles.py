import pygame
import copy
from collections import deque
import heapq
import time
import random
import math

# Khởi tạo Pygame
pygame.init()

# Cài đặt màn hình
WIDTH, HEIGHT = 900, 800
GRID_SIZE = 3
TILE_SIZE = 80
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("8-Puzzle Algorithm Visualizer")

# Màu sắc
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
LIGHT_GRAY = (230, 230, 230)
RED = (255, 0, 0)

# Font chữ
FONT = pygame.font.SysFont("Arial", 24)
SMALL_FONT = pygame.font.SysFont("Arial", 18)

class PuzzleState:
    def __init__(self, board, moves=0, previous=None):
        self.board = board
        self.moves = moves
        self.previous = previous
        self.blank_pos = self.find_blank()

    def find_blank(self):
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == 0:
                    return (i, j)
        return None

    def __eq__(self, other):
        return self.board == other.board

    def __lt__(self, other):
        return self.moves < other.moves

    def __hash__(self):
        return hash(str(self.board))

# Các hướng di chuyển
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def get_neighbors(state):
    neighbors = []
    x, y = state.blank_pos
    for dx, dy in DIRECTIONS:
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < 3 and 0 <= new_y < 3:
            new_board = copy.deepcopy(state.board)
            new_board[x][y], new_board[new_x][new_y] = new_board[new_x][new_y], new_board[x][y]
            neighbors.append(PuzzleState(new_board, state.moves + 1, state))
    return neighbors

def manhattan_distance(state, goal_state):
    total = 0
    for i in range(3):
        for j in range(3):
            value = state.board[i][j]
            if value != 0:
                for gi in range(3):
                    for gj in range(3):
                        if goal_state[gi][gj] == value:
                            total += abs(i - gi) + abs(j - gj)
    return total

# BFS
def bfs(initial_state, goal_state):
    visited = set()
    queue = deque([initial_state])
    while queue:
        state = queue.popleft()
        if state.board == goal_state:
            return state
        if tuple(map(tuple, state.board)) not in visited:
            visited.add(tuple(map(tuple, state.board)))
            for neighbor in get_neighbors(state):
                queue.append(neighbor)
    return None

# DFS
def dfs(initial_state, goal_state):
    visited = set()
    stack = [initial_state]
    while stack:
        state = stack.pop()
        if state.board == goal_state:
            return state
        if tuple(map(tuple, state.board)) not in visited:
            visited.add(tuple(map(tuple, state.board)))
            for neighbor in get_neighbors(state):
                stack.append(neighbor)
    return None

# UCS
def ucs(initial_state, goal_state):
    visited = set()
    pq = [(0, initial_state)]
    heapq.heapify(pq)
    while pq:
        moves, state = heapq.heappop(pq)
        if state.board == goal_state:
            return state
        if tuple(map(tuple, state.board)) not in visited:
            visited.add(tuple(map(tuple, state.board)))
            for neighbor in get_neighbors(state):
                heapq.heappush(pq, (neighbor.moves, neighbor))
    return None

# IDS
def dls(state, depth, goal_state, visited):
    if state.board == goal_state:
        return state
    if depth == 0:
        return None
    if tuple(map(tuple, state.board)) in visited:
        return None
    visited.add(tuple(map(tuple, state.board)))
    for neighbor in get_neighbors(state):
        result = dls(neighbor, depth - 1, goal_state, visited)
        if result:
            return result
    return None

def ids(initial_state, goal_state):
    depth = 0
    while True:
        visited = set()
        result = dls(initial_state, depth, goal_state, visited)
        if result:
            return result
        depth += 1

# Greedy
def greedy(initial_state, goal_state):
    visited = set()
    pq = [(manhattan_distance(initial_state, goal_state), initial_state)]
    heapq.heapify(pq)
    while pq:
        _, state = heapq.heappop(pq)
        if state.board == goal_state:
            return state
        if tuple(map(tuple, state.board)) not in visited:
            visited.add(tuple(map(tuple, state.board)))
            for neighbor in get_neighbors(state):
                heapq.heappush(pq, (manhattan_distance(neighbor, goal_state), neighbor))
    return None

# A*
def a_star(initial_state, goal_state):
    visited = set()
    pq = [(manhattan_distance(initial_state, goal_state), 0, initial_state)]
    heapq.heapify(pq)
    g_scores = {initial_state: 0}
    
    while pq:
        f_score, g_score, state = heapq.heappop(pq)
        if state.board == goal_state:
            return state
        if tuple(map(tuple, state.board)) in visited:
            continue
        visited.add(tuple(map(tuple, state.board)))
        
        for neighbor in get_neighbors(state):
            new_g_score = g_score + 1
            if neighbor not in g_scores or new_g_score < g_scores[neighbor]:
                g_scores[neighbor] = new_g_score
                h_score = manhattan_distance(neighbor, goal_state)
                f_score = new_g_score + h_score
                heapq.heappush(pq, (f_score, new_g_score, neighbor))
    return None

# IDA*
def ida_star(initial_state, goal_state):
    def search(state, g, threshold, visited):
        h = manhattan_distance(state, goal_state)
        f = g + h
        if f > threshold:
            return None, f
        if state.board == goal_state:
            return state, f
        if tuple(map(tuple, state.board)) in visited:
            return None, f
        
        visited.add(tuple(map(tuple, state.board)))
        min_exceeded = float('inf')
        
        for neighbor in get_neighbors(state):
            result, new_f = search(neighbor, g + 1, threshold, visited)
            if result:
                return result, new_f
            min_exceeded = min(min_exceeded, new_f)
        
        return None, min_exceeded

    threshold = manhattan_distance(initial_state, goal_state)
    while True:
        visited = set()
        result, new_threshold = search(initial_state, 0, threshold, visited)
        if result:
            return result
        if new_threshold == float('inf'):
            return None
        threshold = new_threshold

# Simple Hill Climbing (SHC)
def simple_hill_climbing(initial_state, goal_state):
    current = initial_state
    visited = set()
    
    while True:
        if current.board == goal_state:
            return current
            
        visited.add(tuple(map(tuple, current.board)))
        neighbors = get_neighbors(current)
        best_neighbor = None
        best_score = float('inf')
        
        for neighbor in neighbors:
            if tuple(map(tuple, neighbor.board)) not in visited:
                score = manhattan_distance(neighbor, goal_state)
                if score < best_score:
                    best_score = score
                    best_neighbor = neighbor
        
        if best_neighbor is None or best_score >= manhattan_distance(current, goal_state):
            return current
            
        current = best_neighbor

# Hill Climbing (HC) với Random Restart
def hill_climbing(initial_state, goal_state, max_restarts=5):
    best_solution = None
    best_score = float('inf')
    
    for _ in range(max_restarts):
        current = initial_state
        visited = set()
        
        while True:
            if current.board == goal_state:
                return current
                
            visited.add(tuple(map(tuple, current.board)))
            neighbors = get_neighbors(current)
            best_neighbor = None
            best_neighbor_score = float('inf')
            
            for neighbor in neighbors:
                if tuple(map(tuple, neighbor.board)) not in visited:
                    score = manhattan_distance(neighbor, goal_state)
                    if score < best_neighbor_score:
                        best_neighbor_score = score
                        best_neighbor = neighbor
            
            current_score = manhattan_distance(current, goal_state)
            if current_score < best_score:
                best_score = current_score
                best_solution = current
            
            if best_neighbor is None or best_neighbor_score >= current_score:
                break
                
            current = best_neighbor
        
        if best_solution.board != goal_state:
            new_board = copy.deepcopy(initial_state.board)
            for _ in range(3):
                neighbors = get_neighbors(PuzzleState(new_board))
                if neighbors:
                    new_board = random.choice(neighbors).board
            initial_state = PuzzleState(new_board)
    
    return best_solution

def stochastic_hill_climbing(initial_state, goal_state, max_iterations=1000):
    current = initial_state
    visited = set()
    iterations = 0
    
    while iterations < max_iterations:
        if current.board == goal_state:
            return current
            
        visited.add(tuple(map(tuple, current.board)))
        neighbors = get_neighbors(current)
        
        current_score = manhattan_distance(current, goal_state)
        better_neighbors = [
            neighbor for neighbor in neighbors 
            if tuple(map(tuple, neighbor.board)) not in visited 
            and manhattan_distance(neighbor, goal_state) < current_score
        ]
        
        if not better_neighbors:
            return current
            
        current = random.choice(better_neighbors)
        iterations += 1
    
    return current

# Simulated Annealing (SA)
def simulated_annealing(initial_state, goal_state, initial_temp=1000, cooling_rate=0.995, min_temp=1):
    current = initial_state
    current_score = manhattan_distance(current, goal_state)
    best = current
    best_score = current_score
    temp = initial_temp
    
    while temp > min_temp:
        neighbors = get_neighbors(current)
        if not neighbors:
            break
            
        next_state = random.choice(neighbors)
        next_score = manhattan_distance(next_state, goal_state)
        
        delta = next_score - current_score
        
        if delta < 0 or random.random() < math.exp(-delta / temp):
            current = next_state
            current_score = next_score
            
            if current_score < best_score:
                best = current
                best_score = current_score
        
        temp *= cooling_rate
        
        if current.board == goal_state:
            return current
    
    return best

# Beam Search
def beam_search(initial_state, goal_state, beam_width=3):
    queue = [(manhattan_distance(initial_state, goal_state), initial_state)]
    visited = set()
    
    while queue:
        next_level = []
        for _ in range(min(beam_width, len(queue))):
            if not queue:
                break
            _, state = heapq.heappop(queue)
            if tuple(map(tuple, state.board)) not in visited:
                next_level.append(state)
        
        if not next_level:
            return None
            
        for state in next_level:
            visited.add(tuple(map(tuple, state.board)))
            
            if state.board == goal_state:
                return state
            
            neighbors = get_neighbors(state)
            for neighbor in neighbors:
                if tuple(map(tuple, neighbor.board)) not in visited:
                    h_score = manhattan_distance(neighbor, goal_state)
                    heapq.heappush(queue, (h_score, neighbor))
    
    return None

# AND-OR Search Tree
def and_or_search(initial_state, goal_state):
    def ao_search(state, visited, path):
        if state.board == goal_state:
            return state
        
        state_tuple = tuple(map(tuple, state.board))
        if state_tuple in visited:
            return None
        
        visited.add(state_tuple)
        
        neighbors = get_neighbors(state)
        if not neighbors:
            return None
        
        for neighbor in neighbors:
            result = ao_search(neighbor, visited, path)
            if result:
                return result
        
        return None

    visited = set()
    result = ao_search(initial_state, visited, [])
    return result

def get_solution_path(state):
    path = []
    while state:
        path.append(state.board)
        state = state.previous
    return list(reversed(path))

# Vẽ bảng puzzle
def draw_board(board, x, y, selected_pos=None):
    for i in range(GRID_SIZE):
        for j in range(3):
            value = board[i][j]
            rect = pygame.Rect(x + j * TILE_SIZE, y + i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, GRAY if value == 0 else ORANGE, rect)
            border_color = RED if selected_pos and selected_pos == (i, j) else BLACK
            pygame.draw.rect(screen, border_color, rect, 2)
            if value != 0:
                text = FONT.render(str(value), True, BLACK)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

# Vẽ giao diện
def draw_ui(start_state, end_state, solution_path, current_step, selected_algo, selected_pos, edit_mode):
    screen.fill(LIGHT_GRAY)

    # Vẽ nút chọn thuật toán
    algorithms = ["BFS", "DFS", "UCS", "IDS", "Greedy", "A*", "IDA*", "SHC", "HC", "Stochastic HC", "SA", "Beam Search", "AND-OR"]
    button_width = 150
    button_height = 40
    for i, algo in enumerate(algorithms):
        color = YELLOW if algo == selected_algo else GRAY
        rect = pygame.Rect(50, 20 + i * (button_height + 10), button_width, button_height)
        pygame.draw.rect(screen, color, rect)
        text = SMALL_FONT.render(algo, True, BLACK)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    # Vẽ bảng START
    screen.blit(SMALL_FONT.render("START:", True, BLACK), (250, 80))
    draw_board(start_state, 250, 120, selected_pos if edit_mode else None)

    # Vẽ bảng SOLUTION
    screen.blit(SMALL_FONT.render("SOLUTION:", True, BLACK), (550, 80))
    draw_board(start_state if not solution_path else solution_path[current_step], 550, 120)

    # Vẽ bảng END
    screen.blit(SMALL_FONT.render("END:", True, BLACK), (250, 400))
    draw_board(end_state, 250, 440)

    # Vẽ nút PLAY
    pygame.draw.rect(screen, GRAY, (250, 700, 100, 40))
    screen.blit(SMALL_FONT.render("PLAY", True, BLACK), (275, 710))

    # Vẽ nút Reset
    pygame.draw.rect(screen, GRAY, (400, 700, 100, 40))
    screen.blit(SMALL_FONT.render("Reset", True, BLACK), (425, 710))

    # Hiển thị thông báo khi đang chỉnh sửa
    if edit_mode:
        screen.blit(SMALL_FONT.render("Click a tile and enter a number (0-8)", True, BLACK), (250, 760))

    pygame.display.flip()

# Hàm chính
def main():
    clock = pygame.time.Clock()
    start_state = [[1, 2, 3], [4, 5, 6], [0, 7, 8]]
    end_state = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
    solution_path = None
    current_step = 0
    selected_algo = "BFS"
    running = True
    edit_mode = False
    selected_pos = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # Chọn thuật toán
                algorithms = ["BFS", "DFS", "UCS", "IDS", "Greedy", "A*", "IDA*", "SHC", "HC", "Stochastic HC", "SA", "Beam Search", "AND-OR"]
                button_width = 150
                button_height = 40
                for i, algo in enumerate(algorithms):
                    if 50 <= x <= 50 + button_width and 20 + i * (button_height + 10) <= y <= 20 + i * (button_height + 10) + button_height:
                        selected_algo = algo
                # Nhấn PLAY
                if 250 <= x <= 350 and 700 <= y <= 740:
                    initial = PuzzleState(start_state)
                    goal = PuzzleState(end_state)
                    if selected_algo == "BFS":
                        solution = bfs(initial, goal.board)
                    elif selected_algo == "DFS":
                        solution = dfs(initial, goal.board)
                    elif selected_algo == "UCS":
                        solution = ucs(initial, goal.board)
                    elif selected_algo == "IDS":
                        solution = ids(initial, goal.board)
                    elif selected_algo == "Greedy":
                        solution = greedy(initial, goal.board)
                    elif selected_algo == "A*":
                        solution = a_star(initial, goal.board)
                    elif selected_algo == "IDA*":
                        solution = ida_star(initial, goal.board)
                    elif selected_algo == "SHC":
                        solution = simple_hill_climbing(initial, goal.board)
                    elif selected_algo == "HC":
                        solution = hill_climbing(initial, goal.board)
                    elif selected_algo == "Stochastic HC":
                        solution = stochastic_hill_climbing(initial, goal.board)
                    elif selected_algo == "SA":
                        solution = simulated_annealing(initial, goal.board)
                    elif selected_algo == "Beam Search":
                        solution = beam_search(initial, goal.board)
                    elif selected_algo == "AND-OR":
                        solution = and_or_search(initial, goal.board)
                    if solution:
                        solution_path = get_solution_path(solution)
                    else:
                        print("No solution found")
                # Nút Reset
                if 400 <= x <= 500 and 700 <= y <= 740:
                    solution_path = None
                    current_step = 0
                    edit_mode = False
                    selected_pos = None
                # Chọn ô để chỉnh sửa
                if 250 <= x <= 250 + 3 * TILE_SIZE and 120 <= y <= 120 + 3 * TILE_SIZE and not solution_path:
                    col = (x - 250) // TILE_SIZE
                    row = (y - 120) // TILE_SIZE
                    selected_pos = (row, col)
                    edit_mode = True

            if event.type == pygame.KEYDOWN:
                if edit_mode and event.unicode in "0123456789":
                    num = int(event.unicode)
                    if num in [x for row in start_state for x in row] and num != start_state[selected_pos[0]][selected_pos[1]]:
                        continue
                    start_state[selected_pos[0]][selected_pos[1]] = num
                    selected_pos = None
                    edit_mode = False

        draw_ui(start_state, end_state, solution_path, current_step, selected_algo, selected_pos, edit_mode)
        if solution_path and current_step < len(solution_path) - 1:
            current_step += 1
            pygame.time.delay(500)

        clock.tick(60)

    pygame.quit()
    
if __name__ == "__main__":
    main()