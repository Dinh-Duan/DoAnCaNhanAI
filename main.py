# main.py
import pygame
import sys
import importlib
import os
from collections import deque
import time
import traceback # Import traceback for detailed error prints
import subprocess
import sys

# --- Algorithm Import ---
try:
    from algorithms import ALGORITHM_LIST
except ImportError:
    ALGORITHM_LIST = [
        ("Greedy Search", "greedy"), ("Greedy Search (Double Moves)", "greedy_double"),
        ("A* Search (Manhattan)", "a_star_manhattan"), ("A* Search (Manhattan, Double)", "a_star_manhattan_double"),
        ("A* Search (Misplaced)", "a_star_misplaced"), ("A* Search (Misplaced, Double)", "a_star_misplaced_double"),
        ("BFS (Breadth-First Search)", "bfs"), ("BFS (Double Moves)", "bfs_double"),
        ("UCS (Uniform Cost Search)", "ucs"), ("UCS (Double Moves)", "ucs_double"),
        ("Hill Climbing", "hill_climbing"), ("Hill Climbing (Double)", "hill_climbing_double"),
        ("Stochastic Hill Climbing", "stochastic_hc"), ("Stochastic Hill Climbing (Double)", "stochastic_hc_double"),
        ("DFS (Depth-First Search)", "dfs"), ("DFS (Double Moves)", "dfs_double"),
        ("Steepest Ascent Hill Climbing", "steepest_hc"), ("Steepest Ascent Hill Climbing (Double)", "steepest_hc_double"),
        ("IDDFS (Iterative Deepening DFS)", "iddfs"), ("IDDFS (Double Moves)", "iddfs_double"),
        ("IDA* Search", "ida_star"), ("IDA* (Double Moves)", "ida_star_double"),
        ("Beam Search", "beam_search"), ("Genetic Algorithm", "genetic"),
        ("Sensorless Genetic", "sensorless_genetic"), 
    ]
    print("Warning: Could not import ALGORITHM_LIST from algorithms package. Using default list.")
    if not os.path.exists('algorithms'):
        print("Error: 'algorithms' directory not found.")

# --- Grayscale Palette ---
GS_WHITE = (255, 255, 255)
GS_OFF_WHITE = (245, 245, 245)          # General background
GS_LIGHT_GRAY1 = (230, 230, 230)        # Sidebar BG, slightly darker BGs
GS_LIGHT_GRAY2 = (210, 210, 210)        # Inactive elements, borders, some tile BGs (e.g., solved, empty)
GS_MEDIUM_GRAY = (180, 180, 180)        # Standard tile backgrounds, hover states
GS_MEDIUM_DARK_GRAY = (120, 120, 120)   # Primary interactive elements (buttons, selected items)
GS_DARK_GRAY1 = (80, 80, 80)            # Secondary text
GS_DARK_GRAY2 = (50, 50, 50)            # Button hover, error text
GS_BLACK = (10, 10, 10)                 # Primary text, strong success text

# --- Constants and Colors ---
DARK_BG = GS_OFF_WHITE                  # Was (18, 27, 18)
PRIMARY = GS_MEDIUM_DARK_GRAY           # Was (52, 168, 83) - Main button color
PRIMARY_DARK = GS_DARK_GRAY2            # Was (39, 125, 61) - Button hover
SECONDARY = GS_BLACK                    # Was (255, 255, 255) - Main text color (on titles, buttons etc.)
GRAY = GS_LIGHT_GRAY2                   # Was (75, 99, 85) - Empty tile preview BG, info box outer frame
LIGHT_GRAY = GS_DARK_GRAY1              # Was (156, 175, 163) - Instruction text
TILE_BG = GS_MEDIUM_GRAY                # Was (30, 59, 41)
TILE_SOLVED = GS_LIGHT_GRAY2            # Was (34, 197, 94) - Background for solved tiles in solver; success text in editor
RED = GS_DARK_GRAY2                     # Was (209, 49, 49) - Error text color

SIDEBAR_BG = GS_LIGHT_GRAY1             # Was (25, 40, 30)
SIDEBAR_ITEM_BG = GS_WHITE              # Was (40, 65, 50) - Lighter than sidebar BG for items
SIDEBAR_ITEM_HOVER_BG = GS_LIGHT_GRAY2  # Was (60, 90, 70) - Darker than item for hover
SIDEBAR_ITEM_SELECTED_BG = PRIMARY      # Was PRIMARY - Uses the new PRIMARY (GS_MEDIUM_DARK_GRAY)

# --- Constants for Sidebar ---
SIDEBAR_WIDTH = 380
SIDEBAR_MARGIN = 20
SIDEBAR_ITEM_HEIGHT = 45
SIDEBAR_ITEM_PADDING = 5

# --- Helper Functions ---
# (get_inversions, is_solvable, is_valid_puzzle_state, get_neighbors - unchanged)
def get_inversions(state):
    state_without_blank = [x for x in state if x != 9]; inversions = 0
    for i in range(len(state_without_blank)):
        for j in range(i + 1, len(state_without_blank)):
            if state_without_blank[i] > state_without_blank[j]: inversions += 1
    return inversions
def is_solvable(state):
    if 9 not in state or len(state) != 9: return False
    return get_inversions(state) % 2 == 0
def is_valid_puzzle_state(state):
    return isinstance(state, (list, tuple)) and len(state) == 9 and sorted(state) == list(range(1, 10))
def get_neighbors(state):
    neighbors = []; s = list(state)
    try: blank_index = s.index(9)
    except ValueError: return []
    row, col = divmod(blank_index, 3); moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_index = new_row * 3 + new_col; new_s = s[:]
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbors.append(tuple(new_s))
    return neighbors


# --- Class Definitions ---
class MessageBox:
    # (unchanged from previous grayscale version)
    def __init__(self, width, height, title, message, button_text="OK"):
        self.rect = pygame.Rect((WIDTH - width) // 2, (HEIGHT - height) // 2, width, height)
        self.title = title; self.message = message; self.border_radius = 10; self.active = False
        button_width = 100; button_height = 40
        button_x = self.rect.x + (self.rect.width - button_width) // 2
        button_y = self.rect.bottom - button_height - 20
        self.ok_button = Button(button_x, button_y, button_width, button_height, button_text)
    def draw(self, screen, title_font, font, button_font):
        if not self.active: return
        overlay_color = (GS_BLACK[0], GS_BLACK[1], GS_BLACK[2], 128) # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill(overlay_color); screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, DARK_BG, self.rect.inflate(-4, -4), border_radius=self.border_radius)
        title_surface = title_font.render(self.title, True, SECONDARY); title_rect = title_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 20); screen.blit(title_surface, title_rect)
        lines = self.message.split('\n'); start_y = self.rect.y + 70
        for i, line in enumerate(lines): msg_surf = font.render(line, True, LIGHT_GRAY); msg_rect = msg_surf.get_rect(centerx=self.rect.centerx, y=start_y + i * 30); screen.blit(msg_surf, msg_rect)
        self.ok_button.draw(screen, button_font)
    def check_hover(self, mouse_pos):
        if not self.active: return False
        return self.ok_button.check_hover(mouse_pos)
    def handle_event(self, event):
        if not self.active: return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ok_button.is_clicked(event.pos, True): self.active = False; return True
        return False

class AnimatedTile:
    # (unchanged from previous grayscale version)
    def __init__(self, value, x, y, size):
        self.value = value; self.size = size; self.inner_size = int(size * 0.94)
        self.rect = pygame.Rect(x, y, size, size); self.inner_rect = pygame.Rect(0, 0, self.inner_size, self.inner_size); self.inner_rect.center = self.rect.center
        self.current_x = float(x); self.current_y = float(y); self.target_x = float(x); self.target_y = float(y)
        self.speed = 0.2; self.is_solved_position = False
    def set_target(self, x, y): self.target_x = float(x); self.target_y = float(y)
    def update(self):
        dx = self.target_x - self.current_x; dy = self.target_y - self.current_y
        if abs(dx) < 1 and abs(dy) < 1: self.current_x = self.target_x; self.current_y = self.target_y
        else: self.current_x += dx * self.speed; self.current_y += dy * self.speed
        self.rect.topleft = (int(self.current_x), int(self.current_y)); self.inner_rect.center = self.rect.center
    def draw(self, screen, font):
        if self.value == 9:
            pygame.draw.rect(screen, GRAY, self.inner_rect, border_radius=10) # GRAY is GS_LIGHT_GRAY2
            return
        bg_color = TILE_SOLVED if self.is_solved_position else TILE_BG
        pygame.draw.rect(screen, bg_color, self.inner_rect, border_radius=10)
        text = font.render(str(self.value), True, SECONDARY); text_rect = text.get_rect(center=self.inner_rect.center); screen.blit(text, text_rect)
    def is_at_target(self): return abs(self.current_x - self.target_x) < 1 and abs(self.current_y - self.target_y) < 1

class Button:
    # (unchanged from previous grayscale version)
     def __init__(self, x, y, width, height, text, color=PRIMARY, hover_color=PRIMARY_DARK):
         self.rect = pygame.Rect(x, y, width, height); self.text = text; self.color = color
         self.hover_color = hover_color; self.is_hovered = False; self.border_radius = 8
     def draw(self, screen, font):
         current_bg_color = self.hover_color if self.is_hovered else self.color
         pygame.draw.rect(screen, current_bg_color, self.rect, border_radius=self.border_radius)
         text_color_on_button = GS_WHITE
         text_surface = font.render(self.text, True, text_color_on_button); text_rect = text_surface.get_rect(center=self.rect.center); screen.blit(text_surface, text_rect)
     def check_hover(self, mouse_pos): self.is_hovered = self.rect.collidepoint(mouse_pos); return self.is_hovered
     def is_clicked(self, mouse_pos, mouse_click): return self.is_hovered and mouse_click

# --- GUI Drawing Functions ---
def draw_menu(screen, title_font, font, button_font,
              solve_btn, edit_btn, blind_search_btn, fill_anim_btn, exit_btn, # <<< Added exit_btn
              current_start_state,
              selected_algorithm_index, sidebar_scroll_offset, sidebar_hover_index, sidebar_rect, max_display_items):
    """Vẽ màn hình menu chính với sidebar và bố cục nút mới."""
    screen.fill(DARK_BG) # DARK_BG is GS_OFF_WHITE

    # --- Vẽ Sidebar (Unchanged) ---
    pygame.draw.rect(screen, SIDEBAR_BG, sidebar_rect, border_radius=10)
    sidebar_title_surf = title_font.render("Thuật toán", True, SECONDARY)
    sidebar_title_rect = sidebar_title_surf.get_rect(centerx=sidebar_rect.centerx, y=sidebar_rect.y + 20)
    screen.blit(sidebar_title_surf, sidebar_title_rect)
    sidebar_title_height_approx = sidebar_title_rect.height + 40
    start_item_y = sidebar_rect.y + sidebar_title_height_approx
    visible_items_area_height = sidebar_rect.height - sidebar_title_height_approx - 20
    for i in range(len(ALGORITHM_LIST)):
        item_y = start_item_y + (i - sidebar_scroll_offset) * SIDEBAR_ITEM_HEIGHT
        if start_item_y <= item_y < start_item_y + visible_items_area_height:
            item_rect = pygame.Rect(sidebar_rect.x + SIDEBAR_ITEM_PADDING, item_y,
                                    sidebar_rect.width - 2 * SIDEBAR_ITEM_PADDING, SIDEBAR_ITEM_HEIGHT - SIDEBAR_ITEM_PADDING)
            bg_color = SIDEBAR_ITEM_BG; text_color = SECONDARY
            if i == selected_algorithm_index: bg_color = SIDEBAR_ITEM_SELECTED_BG; text_color = GS_WHITE
            elif i == sidebar_hover_index: bg_color = SIDEBAR_ITEM_HOVER_BG
            pygame.draw.rect(screen, bg_color, item_rect, border_radius=5)
            algo_name = ALGORITHM_LIST[i][0]; text_surf = font.render(algo_name, True, text_color)
            available_text_width = item_rect.width - 30
            if text_surf.get_width() > available_text_width:
                original_text = algo_name
                while text_surf.get_width() > available_text_width and len(original_text) > 3:
                    original_text = original_text[:-1]; text_surf = font.render(original_text + "...", True, text_color)
            text_rect = text_surf.get_rect(midleft=(item_rect.x + 15, item_rect.centery)); screen.blit(text_surf, text_rect)

    # --- Vẽ Nội dung Chính (Bố cục mới) ---
    content_start_x = sidebar_rect.right + SIDEBAR_MARGIN
    content_width = WIDTH - content_start_x - SIDEBAR_MARGIN
    content_center_x = content_start_x + content_width // 2

    # Ước lượng chiều cao các thành phần nội dung
    title_height = title_font.get_height()
    instr_line_height = font.get_height()
    num_instr_lines = 4 # Giữ nguyên số dòng hướng dẫn
    instr_block_height = num_instr_lines * instr_line_height + (num_instr_lines - 1) * 5
    button_height = solve_btn.rect.height # Giả sử các nút cùng chiều cao
    button_width = solve_btn.rect.width # Lấy chiều rộng nút làm chuẩn
    button_spacing = 20 # Tăng khoảng cách giữa các nút một chút
    # Chiều cao khối nút mới (3 hàng)
    button_block_height = 3 * button_height + 2 * button_spacing
    preview_label_height = font.get_height()
    mini_tile_size = 35; mini_padding_vert = 2; mini_tile_total_h = mini_tile_size + mini_padding_vert
    preview_grid_height = mini_tile_total_h * 3 - mini_padding_vert
    # Điều chỉnh khoảng cách dọc
    spacing_title_instr = 40 # Tăng khoảng cách
    spacing_instr_button = 50 # Tăng khoảng cách
    spacing_button_preview_label = 50 # Tăng khoảng cách
    spacing_preview_label_grid = 15

    total_content_height = (title_height + spacing_title_instr + instr_block_height + spacing_instr_button +
                            button_block_height + spacing_button_preview_label + preview_label_height +
                            spacing_preview_label_grid + preview_grid_height)

    available_content_height = HEIGHT - 2 * SIDEBAR_MARGIN
    content_start_y = SIDEBAR_MARGIN + max(0, (available_content_height - total_content_height) // 2)
    current_y = content_start_y

    # Title (Unchanged)
    title_surf_main = title_font.render("8-Puzzle Solver", True, SECONDARY)
    title_rect_menu = title_surf_main.get_rect(centerx=content_center_x, top=current_y)
    screen.blit(title_surf_main, title_rect_menu)
    current_y += title_height + spacing_title_instr

    # Instructions (Unchanged text, position depends on current_y)
    explanation = ["Chọn thuật toán từ danh sách bên trái.",
                   "Nhấn nút 'Bắt đầu' bên dưới để giải.",
                   "Hoặc chọn các nút chức năng khác.",
                   f"(Trạng thái đích: {GOAL_STATE})"]
    instr_y = current_y
    for i, text_content in enumerate(explanation):
        line = font.render(text_content, True, LIGHT_GRAY)
        line_rect = line.get_rect(centerx=content_center_x, top=instr_y + i * (instr_line_height + 5))
        screen.blit(line, line_rect)
    current_y += instr_block_height + spacing_instr_button

    # --- Menu Buttons (Bố cục mới 2x2 + 1) ---
    # Tính toán vị trí cho lưới nút
    grid_width = button_width * 2 + button_spacing
    start_grid_x = content_center_x - grid_width // 2

    # Hàng 1
    row1_y = current_y
    solve_btn.rect.topleft = (start_grid_x, row1_y)
    edit_btn.rect.topleft = (start_grid_x + button_width + button_spacing, row1_y)

    # Hàng 2
    row2_y = row1_y + button_height + button_spacing
    blind_search_btn.rect.topleft = (start_grid_x, row2_y)
    fill_anim_btn.rect.topleft = (start_grid_x + button_width + button_spacing, row2_y)

    # Hàng 3 (Nút Exit ở giữa)
    row3_y = row2_y + button_height + button_spacing
    exit_btn.rect.centerx = content_center_x
    exit_btn.rect.top = row3_y

    # Vẽ các nút
    solve_btn.draw(screen, button_font)
    edit_btn.draw(screen, button_font)
    blind_search_btn.draw(screen, button_font)
    fill_anim_btn.draw(screen, button_font)
    exit_btn.draw(screen, button_font) # <<< Vẽ nút Thoát

    current_y += button_block_height + spacing_button_preview_label # Sử dụng chiều cao khối nút mới

    # Draw start state preview (Unchanged logic, position depends on current_y)
    label = font.render("Trạng thái ban đầu hiện tại:", True, SECONDARY)
    label_rect = label.get_rect(centerx=content_center_x, top=current_y)
    screen.blit(label, label_rect)
    current_y += preview_label_height + spacing_preview_label_grid
    mini_width = (mini_tile_size + mini_padding_vert) * 3 - mini_padding_vert
    mini_start_x = content_center_x - mini_width // 2
    mini_start_y = current_y
    for i, val in enumerate(current_start_state):
        row, col = divmod(i, 3)
        x = mini_start_x + col * (mini_tile_size + mini_padding_vert)
        y = mini_start_y + row * (mini_tile_size + mini_padding_vert)
        tile_rect = pygame.Rect(x, y, mini_tile_size, mini_tile_size)
        bg_color = TILE_BG if val != 9 else GRAY
        pygame.draw.rect(screen, bg_color, tile_rect, border_radius=5)
        if val != 9:
            text_surf = button_font.render(str(val), True, SECONDARY)
            text_rect = text_surf.get_rect(center=tile_rect.center); screen.blit(text_surf, text_rect)

# --- (init_tiles, update_tiles, draw_info_box - unchanged) ---
def init_tiles(state, offset_y=150):
    puzzle_area_width = WIDTH * 0.5; puzzle_area_height = HEIGHT - offset_y - 100
    tile_size = min(puzzle_area_width / 3, puzzle_area_height / 3) * 0.9; puzzle_width = tile_size * 3
    info_box_width_approx = min(WIDTH * 0.35, 400) + 50
    available_solver_width = WIDTH - info_box_width_approx
    start_x = (available_solver_width - puzzle_width) / 2
    start_y = offset_y ; tiles = []
    for i, val in enumerate(state):
        row, col = divmod(i, 3); x = start_x + col * tile_size; y = start_y + row * tile_size
        tile = AnimatedTile(val, x, y, tile_size); tile.is_solved_position = (val != 9 and val == GOAL_STATE[i]); tiles.append(tile)
    return tiles

def update_tiles(tiles, new_state, goal_state, offset_y=150):
    if not tiles: return
    tile_size = tiles[0].size; puzzle_width = tile_size * 3
    info_box_width_approx = min(WIDTH * 0.35, 400) + 50
    available_solver_width = WIDTH - info_box_width_approx
    start_x = (available_solver_width - puzzle_width) / 2
    start_y = offset_y
    value_pos_map = {val: i for i, val in enumerate(new_state)}
    for tile in tiles:
        if tile.value in value_pos_map:
            new_index = value_pos_map[tile.value]; row, col = divmod(new_index, 3)
            target_x = start_x + col * tile_size; target_y = start_y + row * tile_size
            tile.set_target(target_x, target_y); tile.is_solved_position = (tile.value != 9 and tile.value == goal_state[new_index])

def draw_info_box(screen, font, info_font, steps_found, path_length, current_step, total_steps, algorithm_name, elapsed_time=None):
    box_width = min(WIDTH * 0.35, 400); box_height = 350
    box_x = WIDTH - box_width - 50; box_y = 150
    info_box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, GRAY, info_box_rect, border_radius=10); pygame.draw.rect(screen, DARK_BG, info_box_rect.inflate(-4, -4), border_radius=10)
    title_surf_info = font.render("Thông tin giải", True, SECONDARY)
    screen.blit(title_surf_info, title_surf_info.get_rect(centerx=info_box_rect.centerx, y=info_box_rect.y + 20))
    info_lines_content = [f"Thuật toán: {algorithm_name}", f"Node đã duyệt: {steps_found if steps_found is not None else 'N/A'}",
                  f"Độ dài đường đi: {path_length if path_length is not None else 'N/A'}",
                  f"Bước hiện tại: {current_step}/{total_steps if total_steps is not None else 'N/A'}"]
    if elapsed_time is not None: info_lines_content.append(f"Thời gian tìm kiếm: {elapsed_time:.3f} s")
    line_y = info_box_rect.y + 60
    for text_content in info_lines_content:
        line_surf = info_font.render(text_content, True, LIGHT_GRAY); screen.blit(line_surf, (info_box_rect.x + 20, line_y)); line_y += 30
    if total_steps is not None and total_steps > 0:
        progress_rect_bg = pygame.Rect(info_box_rect.x + 20, info_box_rect.bottom - 60, info_box_rect.width - 40, 20)
        pygame.draw.rect(screen, GRAY, progress_rect_bg, border_radius=10)
        progress_ratio = min(1.0, max(0.0, current_step / total_steps)); progress_width = int(progress_ratio * progress_rect_bg.width)
        if progress_width > 0:
            progress_rect_fg = pygame.Rect(progress_rect_bg.x, progress_rect_bg.y, progress_width, progress_rect_bg.height)
            pygame.draw.rect(screen, PRIMARY, progress_rect_fg, border_radius=10)

# --- (init_editor_tiles, draw_editor, draw_single_puzzle, draw_blind_preview - unchanged) ---
def init_editor_tiles(state, offset_x, offset_y, tile_size):
    tiles = []
    for i, val in enumerate(state):
        row, col = divmod(i, 3); x = offset_x + col * tile_size; y = offset_y + row * tile_size
        tile = AnimatedTile(val, x, y, tile_size)
        tile.is_solved_position = False
        tiles.append(tile)
    return tiles

def draw_editor(screen, editor_tiles, editor_state, selected_idx, title_font, font, info_font, puzzle_font, button_font):
    screen.fill(DARK_BG)
    title_surf_editor = title_font.render("Chỉnh sửa trạng thái ban đầu", True, SECONDARY)
    screen.blit(title_surf_editor, title_surf_editor.get_rect(centerx=WIDTH // 2, y=70))
    instructions = ["Click vào ô để chọn, nhập số (1-9) để thay đổi.", "Số nhập vào sẽ đổi chỗ với số hiện tại trong ô.",
                   "Phải chứa đủ 1-9 và có thể giải được.", "Nhấn ENTER để lưu, ESC để hủy."]
    line_y = 120
    for text_content in instructions:
        line = info_font.render(text_content, True, LIGHT_GRAY); screen.blit(line, line.get_rect(centerx=WIDTH // 2, y=line_y)); line_y += 30
    if not editor_tiles: return None, None
    tile_size = editor_tiles[0].size; puzzle_width = tile_size * 3; puzzle_height = tile_size * 3
    start_x = (WIDTH - puzzle_width) // 2; start_y = line_y + 40
    for i, tile in enumerate(editor_tiles):
         row, col = divmod(i, 3); tile.rect.topleft = (start_x + col * tile_size, start_y + row * tile_size); tile.inner_rect.center = tile.rect.center
         if tile.value != 9:
              bg_color = TILE_BG
              pygame.draw.rect(screen, bg_color, tile.inner_rect, border_radius=10)
              text_surf_tile = puzzle_font.render(str(tile.value), True, SECONDARY)
              text_rect = text_surf_tile.get_rect(center=tile.inner_rect.center); screen.blit(text_surf_tile, text_rect)
         else:
              pygame.draw.rect(screen, GRAY, tile.inner_rect, border_radius=10)
         if i == selected_idx:
             highlight_rect = tile.rect.inflate(6, 6)
             pygame.draw.rect(screen, PRIMARY, highlight_rect, border_radius=12, width=3)
    is_valid = is_valid_puzzle_state(editor_state)
    solvable = is_solvable(tuple(editor_state)) if is_valid else False
    status_text = "Trạng thái không hợp lệ (thiếu/trùng số 1-9)" if not is_valid else \
                  f"Trạng thái {'CÓ THỂ' if solvable else 'KHÔNG THỂ'} giải được"
    status_color = RED if not is_valid or not solvable else GS_BLACK
    status_surf = font.render(status_text, True, status_color); status_rect = status_surf.get_rect(center=(WIDTH // 2, start_y + puzzle_height + 40)); screen.blit(status_surf, status_rect)
    button_width = 150; button_height = 40; button_y = status_rect.bottom + 30
    save_btn = Button(WIDTH // 2 - button_width - 10, button_y, button_width, button_height, "Lưu (Enter)")
    cancel_btn = Button(WIDTH // 2 + 10, button_y, button_width, button_height, "Hủy (Esc)")
    save_btn.check_hover(pygame.mouse.get_pos()); cancel_btn.check_hover(pygame.mouse.get_pos())
    save_btn.draw(screen, button_font); cancel_btn.draw(screen, button_font)
    return save_btn, cancel_btn

def draw_single_puzzle(screen, state, x, y, tile_size, font_to_use):
    padding = max(1, int(tile_size * 0.02)); inner_tile_size = tile_size - 2 * padding
    for i, val in enumerate(state):
        row, col = divmod(i, 3); tile_x = x + col * tile_size + padding; tile_y = y + row * tile_size + padding
        tile_rect = pygame.Rect(tile_x, tile_y, inner_tile_size, inner_tile_size)
        bg_color = TILE_BG if val != 9 else GRAY; pygame.draw.rect(screen, bg_color, tile_rect, border_radius=5)
        if val != 9:
            text_surf = font_to_use.render(str(val), True, SECONDARY); text_rect = text_surf.get_rect(center=tile_rect.center); screen.blit(text_surf, text_rect)

def draw_blind_preview(screen, title_font, font, info_font, puzzle_font_to_use, button_font, state1, state2, start_btn, back_btn):
    screen.fill(DARK_BG);
    title_surf_blind = title_font.render("Xem trước Tìm kiếm Mù", True, SECONDARY);
    screen.blit(title_surf_blind, title_surf_blind.get_rect(centerx=WIDTH // 2, y=50))
    explanation = ["Đây là 2 ví dụ về trạng thái ban đầu có thể được sử dụng.", "(Tìm kiếm thực tế sẽ tạo ngẫu nhiên 10 trạng thái tương tự).", "Nhấn 'Bắt đầu' để chạy tìm kiếm mù thực sự."]
    line_y = 110
    for text_content in explanation:
        line = info_font.render(text_content, True, LIGHT_GRAY); screen.blit(line, line.get_rect(centerx=WIDTH // 2, y=line_y)); line_y += 30
    max_tile_size = 150; preview_tile_size = min(WIDTH * 0.15, HEIGHT * 0.20, max_tile_size); puzzle_size = preview_tile_size * 3
    total_width_needed = puzzle_size * 2 + 100; start_puzzles_x = (WIDTH - total_width_needed) // 2
    puzzle1_x = start_puzzles_x; puzzle2_x = start_puzzles_x + puzzle_size + 100; puzzles_y = line_y + 40
    draw_single_puzzle(screen, state1, puzzle1_x, puzzles_y, preview_tile_size, puzzle_font_to_use)
    draw_single_puzzle(screen, state2, puzzle2_x, puzzles_y, preview_tile_size, puzzle_font_to_use)
    label1_surf = font.render("Trạng thái ví dụ 1", True, SECONDARY); label2_surf = font.render("Trạng thái ví dụ 2", True, SECONDARY)
    screen.blit(label1_surf, label1_surf.get_rect(centerx=puzzle1_x + puzzle_size // 2, bottom=puzzles_y - 10)); screen.blit(label2_surf, label2_surf.get_rect(centerx=puzzle2_x + puzzle_size // 2, bottom=puzzles_y - 10))
    button_y = puzzles_y + puzzle_size + 50
    start_btn.rect.centerx = WIDTH // 2 - start_btn.rect.width // 2 - 10; start_btn.rect.y = button_y
    back_btn.rect.centerx = WIDTH // 2 + back_btn.rect.width // 2 + 10; back_btn.rect.y = button_y
    start_btn.check_hover(pygame.mouse.get_pos()); back_btn.check_hover(pygame.mouse.get_pos()); start_btn.draw(screen, button_font); back_btn.draw(screen, button_font)


# --- Helper function to start solving (unchanged) ---
def start_solving(selected_algorithm_index, start_state, goal_state, message_box):
    global current_view, path, steps_found, elapsed_time, tiles, current_step, last_switch
    if not is_valid_puzzle_state(start_state):
        message_box.title="Lỗi Trạng Thái"; message_box.message=f"Trạng thái bắt đầu không hợp lệ:\n{start_state}"; message_box.active=True; return False
    if not is_solvable(start_state):
        message_box.title="Lỗi Trạng Thái"; message_box.message=f"Trạng thái bắt đầu không thể giải:\n{start_state}"; message_box.active=True; return False

    algorithm_name, module_name = ALGORITHM_LIST[selected_algorithm_index]
    print(f"Attempting solve: {algorithm_name}, State: {start_state}")
    try:
        module = importlib.import_module(f"algorithms.{module_name}")
        start_time_solve = time.time(); solve_result = module.solve(start_state, goal_state); elapsed_time = time.time() - start_time_solve
        path, steps_found = None, None
        if isinstance(solve_result, tuple) and len(solve_result) > 0:
            path = solve_result[0]; steps_found = solve_result[1] if len(solve_result) > 1 and isinstance(solve_result[1], int) else None
        elif isinstance(solve_result, list): path = solve_result
        if path and isinstance(path, list) and len(path) > 0:
            path_length = len(path) - 1; print(f"Solution found: {path_length} steps. Search took {elapsed_time:.3f}s.")
            if steps_found is None: steps_found = path_length
            current_view = "solver"; tiles = init_tiles(start_state, 150)
            current_step = 0; last_switch = pygame.time.get_ticks(); return True
        else: print(f"No solution found by {algorithm_name}. Search took {elapsed_time:.3f}s."); message_box.title="Không tìm thấy"; message_box.message=f"{algorithm_name} không tìm thấy đường đi."; message_box.active=True; return False
    except ImportError: print(f"Import Error: algorithms.{module_name}"); message_box.title="Lỗi Import"; message_box.message=f"Không thể tải thuật toán:\n'{module_name}'."; message_box.active=True; return False
    except AttributeError: print(f"Attribute Error: 'solve' not in algorithms.{module_name}"); message_box.title="Lỗi Thuật Toán"; message_box.message=f"Thuật toán '{module_name}' thiếu hàm 'solve'."; message_box.active=True; return False
    except Exception as e: print(f"Error solving with {algorithm_name}: {e}"); traceback.print_exc(); message_box.title="Lỗi Thực Thi"; message_box.message=f"Lỗi khi chạy {algorithm_name}:\n{e}"; message_box.active=True; return False

# --- Main Function ---
def main():
    global START_STATE, screen, GOAL_STATE, WIDTH, HEIGHT, font, title_font, puzzle_font, button_font, info_font
    global current_view, path, steps_found, elapsed_time, tiles, current_step, last_switch

    clock = pygame.time.Clock()
    running = True
    current_view = "menu"
    path = None; current_step = 0; auto_mode = True; last_switch = 0; switch_time = 500
    tiles = None; steps_found = None; elapsed_time = None
    selected_algorithm_index = 0

    # Sidebar state (unchanged)
    sidebar_scroll_offset = 0; sidebar_hover_index = -1
    sidebar_rect = pygame.Rect(SIDEBAR_MARGIN, SIDEBAR_MARGIN, SIDEBAR_WIDTH, HEIGHT - 2 * SIDEBAR_MARGIN)
    try: sidebar_title_height_approx = title_font.get_height() + 40
    except Exception: sidebar_title_height_approx = 80
    available_height_for_items = sidebar_rect.height - sidebar_title_height_approx - 20
    max_display_items = max(1, available_height_for_items // SIDEBAR_ITEM_HEIGHT)
    max_scroll_offset = max(0, len(ALGORITHM_LIST) - max_display_items)

    # Editor State (unchanged)
    current_start_state_editor = list(START_STATE)
    editor_tile_size = min(WIDTH * 0.5, HEIGHT * 0.5) / 3
    editor_puzzle_width = editor_tile_size * 3; editor_start_x = (WIDTH - editor_puzzle_width) // 2; editor_start_y = 280
    editor_tiles = init_editor_tiles(current_start_state_editor, editor_start_x, editor_start_y, editor_tile_size)
    editor_selected_idx = -1
    message_box = MessageBox(500, 250, "Thông báo", "")

    # --- UI Elements ---
    # Solver View Buttons (unchanged)
    solver_button_width = 120; solver_button_height = 40
    buttons_total_width = 4 * solver_button_width + 3 * 20; solver_buttons_start_x = (WIDTH - buttons_total_width) // 2; solver_buttons_y = HEIGHT - 70
    auto_btn = Button(solver_buttons_start_x, solver_buttons_y, solver_button_width, solver_button_height, "Auto: On")
    next_btn = Button(auto_btn.rect.right + 20, solver_buttons_y, solver_button_width, solver_button_height, "Tiếp theo")
    reset_btn = Button(next_btn.rect.right + 20, solver_buttons_y, solver_button_width, solver_button_height, "Làm lại")
    back_menu_btn = Button(reset_btn.rect.right + 20, solver_buttons_y, solver_button_width, solver_button_height, "Quay lại Menu")

    # Menu View Buttons
    menu_button_width = 250; menu_button_height = 45
    solve_btn = Button(0, 0, menu_button_width, menu_button_height, "Bắt đầu")
    edit_btn = Button(0, 0, menu_button_width, menu_button_height, "Chỉnh sửa trạng thái")
    blind_search_btn = Button(0, 0, menu_button_width, menu_button_height, "Tìm kiếm mù")
    fill_anim_btn = Button(0, 0, menu_button_width, menu_button_height, "Hoạt ảnh điền số")
    exit_btn = Button(0, 0, menu_button_width, menu_button_height, "Thoát") # <<< Nút Thoát mới

    # Editor View Buttons (unchanged init)
    editor_save_btn = None; editor_cancel_btn = None

    # Blind Preview View Buttons & States (unchanged)
    BLIND_PREVIEW_STATE_1 = (1, 2, 3, 4, 5, 6, 7, 9, 8); BLIND_PREVIEW_STATE_2 = (1, 2, 3, 4, 5, 9, 7, 8, 6)
    blind_preview_button_width = 220; blind_preview_button_height = 45
    start_blind_run_btn = Button(0, 0, blind_preview_button_width, blind_preview_button_height, "Bắt đầu Tìm kiếm mù")
    back_menu_from_preview_btn = Button(0, 0, 150, blind_preview_button_height, "Quay lại Menu")

    # --- Main Game Loop ---
    while running:
        mouse_pos = pygame.mouse.get_pos(); mouse_click = False
        sidebar_hover_index = -1

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if message_box.active:
                if message_box.handle_event(event): continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: mouse_click = True

            # --- Menu Specific Events ---
            if current_view == "menu":
                # Sidebar Scroll
                if event.type == pygame.MOUSEWHEEL and sidebar_rect.collidepoint(mouse_pos):
                    sidebar_scroll_offset -= event.y
                    sidebar_scroll_offset = max(0, min(sidebar_scroll_offset, max_scroll_offset))
                # Sidebar Keyboard Navigation
                if event.type == pygame.KEYDOWN:
                    original_selected_index = selected_algorithm_index
                    if event.key == pygame.K_DOWN:
                        selected_algorithm_index = min(selected_algorithm_index + 1, len(ALGORITHM_LIST) - 1)
                        # Adjust scroll if selection goes out of view
                        if selected_algorithm_index >= sidebar_scroll_offset + max_display_items:
                            sidebar_scroll_offset = selected_algorithm_index - max_display_items + 1
                            sidebar_scroll_offset = max(0, min(sidebar_scroll_offset, max_scroll_offset))
                    elif event.key == pygame.K_UP:
                        selected_algorithm_index = max(selected_algorithm_index - 1, 0)
                        # Adjust scroll if selection goes out of view
                        if selected_algorithm_index < sidebar_scroll_offset:
                            sidebar_scroll_offset = selected_algorithm_index
                            sidebar_scroll_offset = max(0, min(sidebar_scroll_offset, max_scroll_offset))
                    # Print selection change only if it actually changed
                    if selected_algorithm_index != original_selected_index:
                         print(f"Selected Algorithm (Keyboard): {ALGORITHM_LIST[selected_algorithm_index][0]}")

            # --- Global Key Events (ESC) & Editor Key Events ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_view == "editor": current_view = "menu"
                    elif current_view == "solver": current_view = "menu"; path = None; tiles = None
                    elif current_view == "blind_preview": current_view = "menu"
                    # In menu, ESC now handled by Exit button, but could be uncommented for direct exit
                    # elif current_view == "menu": running = False
                    else: running = False # Default exit for other potential views

                # --- Editor Specific Key Events ---
                elif current_view == "editor":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if is_valid_puzzle_state(current_start_state_editor) and is_solvable(tuple(current_start_state_editor)):
                            START_STATE = tuple(current_start_state_editor); current_view = "menu"
                        else: message_box.title="Lỗi Lưu"; message_box.message="Trạng thái không hợp lệ hoặc không giải được."; message_box.active = True
                    elif editor_selected_idx != -1 and pygame.K_1 <= event.key <= pygame.K_9:
                        new_val = event.key - pygame.K_0
                        current_val_at_selected = current_start_state_editor[editor_selected_idx]
                        if new_val != 9 and new_val != current_val_at_selected:
                            try:
                                existing_idx_of_new_val = current_start_state_editor.index(new_val)
                                # Swap values in list
                                current_start_state_editor[existing_idx_of_new_val] = current_val_at_selected
                                current_start_state_editor[editor_selected_idx] = new_val
                                # Update corresponding editor tiles visually
                                editor_tiles[existing_idx_of_new_val].value = current_val_at_selected
                                editor_tiles[editor_selected_idx].value = new_val
                            except ValueError: pass # Should not happen if state is valid
                        editor_selected_idx = -1 # Deselect after input

        # --- Mouse Hover Logic ---
        if current_view == "menu":
            # Sidebar Hover (unchanged)
            if sidebar_rect.collidepoint(mouse_pos):
                relative_y = mouse_pos[1] - (sidebar_rect.y + sidebar_title_height_approx) # Simplified check start Y
                if relative_y >= 0:
                    hover_calc_index = (relative_y // SIDEBAR_ITEM_HEIGHT) + sidebar_scroll_offset
                    # Check bounds and actual item rect collision
                    if 0 <= hover_calc_index < len(ALGORITHM_LIST):
                         item_y_check = sidebar_rect.y + sidebar_title_height_approx + (hover_calc_index - sidebar_scroll_offset) * SIDEBAR_ITEM_HEIGHT
                         item_rect_check = pygame.Rect(sidebar_rect.x + SIDEBAR_ITEM_PADDING, item_y_check, sidebar_rect.width - 2 * SIDEBAR_ITEM_PADDING, SIDEBAR_ITEM_HEIGHT - SIDEBAR_ITEM_PADDING)
                         if item_rect_check.collidepoint(mouse_pos): sidebar_hover_index = hover_calc_index

        # --- Mouse Click Logic ---
        if mouse_click:
            # --- Editor Clicks ---
            if current_view == "editor":
                if editor_save_btn and editor_save_btn.is_clicked(mouse_pos, True):
                     if is_valid_puzzle_state(current_start_state_editor) and is_solvable(tuple(current_start_state_editor)): START_STATE = tuple(current_start_state_editor); current_view = "menu"
                     else: message_box.title="Lỗi Lưu"; message_box.message="Trạng thái không hợp lệ hoặc không giải được."; message_box.active = True
                elif editor_cancel_btn and editor_cancel_btn.is_clicked(mouse_pos, True): current_view = "menu"
                else: # Click selects editor tile
                    editor_selected_idx = -1
                    for i, tile in enumerate(editor_tiles):
                        if tile.rect.collidepoint(mouse_pos): editor_selected_idx = i; break

            # --- Menu Clicks ---
            elif current_view == "menu":
                 # Sidebar item click
                 if sidebar_rect.collidepoint(mouse_pos) and sidebar_hover_index != -1:
                     selected_algorithm_index = sidebar_hover_index
                     print(f"Selected Algorithm (Mouse): {ALGORITHM_LIST[selected_algorithm_index][0]}")
                 # Menu button clicks
                 elif solve_btn.is_clicked(mouse_pos, True):
                     start_solving(selected_algorithm_index, START_STATE, GOAL_STATE, message_box)
                 elif edit_btn.is_clicked(mouse_pos, True):
                     current_start_state_editor = list(START_STATE)
                     editor_tiles = init_editor_tiles(current_start_state_editor, editor_start_x, editor_start_y, editor_tile_size)
                     editor_selected_idx = -1; current_view = "editor"
                 elif blind_search_btn.is_clicked(mouse_pos, True): current_view = "blind_preview"
                 elif fill_anim_btn.is_clicked(mouse_pos, True):
                     print("Launching Fill Animation Visualizer (fill.py)...")
                     try: process = subprocess.Popen([sys.executable, "fill.py"])
                     except FileNotFoundError: message_box.title = "Lỗi"; message_box.message = "Không tìm thấy file 'fill.py'."; message_box.active = True
                     except Exception as e: message_box.title = "Lỗi"; message_box.message = f"Lỗi khi chạy fill.py:\n{e}"; message_box.active = True
                 elif exit_btn.is_clicked(mouse_pos, True): # <<< Handle Exit Button Click >>>
                     running = False

            # --- Blind Preview Clicks ---
            elif current_view == "blind_preview":
                 if start_blind_run_btn.is_clicked(mouse_pos, True):
                     print("Launching Blind Search logic...")
                     try: import blind; blind.run_blind_search(); current_view = "menu"; pygame.display.set_caption("8-Puzzle Solver"); print("Returned from Blind Search.")
                     except ImportError: message_box.title="Lỗi Import"; message_box.message="Không tìm thấy file 'blind.py'."; message_box.active=True
                     except Exception as e: print(f"Error running Blind Search: {e}"); traceback.print_exc(); message_box.title="Lỗi Tìm Kiếm Mù"; message_box.message=f"Lỗi xảy ra khi chạy tìm kiếm mù:\n{e}"; message_box.active=True
                 elif back_menu_from_preview_btn.is_clicked(mouse_pos, True): current_view = "menu"

            # --- Solver Clicks ---
            elif current_view == "solver":
                 if auto_btn.is_clicked(mouse_pos, True): auto_mode = not auto_mode; auto_btn.text = "Auto: On" if auto_mode else "Auto: Off";
                 elif next_btn.is_clicked(mouse_pos, True):
                     if not auto_mode and path and current_step < len(path) - 1: current_step += 1; update_tiles(tiles, path[current_step], GOAL_STATE, 150)
                 elif reset_btn.is_clicked(mouse_pos, True):
                     if path: current_step = 0; last_switch = pygame.time.get_ticks(); update_tiles(tiles, path[0], GOAL_STATE, 150)
                 elif back_menu_btn.is_clicked(mouse_pos, True): current_view = "menu"; path = None; tiles = None

        # --- Drawing Logic ---
        screen.fill(DARK_BG) # Clear screen first

        # --- Draw based on current view ---
        if current_view == "editor":
            editor_save_btn, editor_cancel_btn = draw_editor(screen, editor_tiles, current_start_state_editor, editor_selected_idx, title_font, font, info_font, puzzle_font, button_font)
        elif current_view == "menu":
            draw_menu(screen, title_font, font, button_font,
                      solve_btn, edit_btn, blind_search_btn, fill_anim_btn, exit_btn, # <<< Pass exit_btn
                      START_STATE,
                      selected_algorithm_index, sidebar_scroll_offset, sidebar_hover_index, sidebar_rect, max_display_items)
            # Check hover for all menu buttons after drawing
            solve_btn.check_hover(mouse_pos); edit_btn.check_hover(mouse_pos)
            blind_search_btn.check_hover(mouse_pos); fill_anim_btn.check_hover(mouse_pos)
            exit_btn.check_hover(mouse_pos) # <<< Check hover for exit_btn
        elif current_view == "blind_preview":
            draw_blind_preview(screen, title_font, font, info_font, puzzle_font, button_font,
                               BLIND_PREVIEW_STATE_1, BLIND_PREVIEW_STATE_2, start_blind_run_btn, back_menu_from_preview_btn)
        elif current_view == "solver":
            # Update and draw tiles
            if tiles:
                 for tile in tiles: tile.update()
                 for tile in tiles: tile.draw(screen, puzzle_font)
            # Auto-play logic
            now_ticks = pygame.time.get_ticks()
            if path and tiles:
                 all_at_target = all(tile.is_at_target() for tile in tiles)
                 if auto_mode and current_step < len(path) - 1 and all_at_target and now_ticks - last_switch >= switch_time:
                     last_switch = now_ticks; current_step += 1; update_tiles(tiles, path[current_step], GOAL_STATE, 150)
            # Draw solver controls and info
            for btn in [auto_btn, next_btn, reset_btn, back_menu_btn]: btn.check_hover(mouse_pos); btn.draw(screen, button_font)
            if path: path_length = len(path) - 1; draw_info_box(screen, font, info_font, steps_found, path_length, current_step, path_length, ALGORITHM_LIST[selected_algorithm_index][0], elapsed_time)

        # Draw message box on top if active
        if message_box.active: message_box.draw(screen, title_font, font, button_font); message_box.check_hover(mouse_pos)

        pygame.display.flip(); clock.tick(60) # Update display and control FPS

    pygame.quit(); sys.exit() # Clean exit

# --- Global Variables and Initialization ---
if __name__ == "__main__":
    pygame.init(); pygame.font.init()
    try:
        screen_info = pygame.display.Info(); WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
    except pygame.error: print("Warning: Fullscreen failed. Using 1280x720 windowed."); WIDTH, HEIGHT = 1280, 720; screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("8-Puzzle Solver")
    try:
        font_name = "Arial";
        if font_name not in pygame.font.get_fonts(): available = pygame.font.get_fonts(); common = ["freesans", "helvetica", "dejavusans", "verdana", "sans"]; font_name = pygame.font.get_default_font();
        for cf in common:
             if cf.lower() in [f.lower() for f in available]: font_name = cf; break
        print(f"Using font: {font_name}")
        font = pygame.font.SysFont(font_name, 22); title_font = pygame.font.SysFont(font_name, 44, bold=True)
        puzzle_font = pygame.font.SysFont(font_name, 60, bold=True)
        button_font = pygame.font.SysFont(font_name, 20); info_font = pygame.font.SysFont(font_name, 22)
    except Exception as e: print(f"Font error: {e}. Using default."); font = pygame.font.Font(None, 24); title_font = pygame.font.Font(None, 44); puzzle_font = pygame.font.Font(None, 60); button_font = pygame.font.Font(None, 20); info_font = pygame.font.Font(None, 22)
    START_STATE = (1, 8, 2, 9, 4, 3, 7, 6, 5)
    GOAL_STATE = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    if not is_solvable(START_STATE): print(f"Warning: Default START_STATE {START_STATE} is not solvable!")
    main()