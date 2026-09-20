"""
一箭又一箭 —— Pygame 图形界面主程序。

运行方式：
    pip install -r requirements.txt
    python main.py

操作：
    鼠标左键点击棋盘上的箭头。
    箭头前方无阻挡时会飞出棋盘；被阻挡时变红抖动并扣一次失误。
    顶部可以看到当前关卡、剩余箭头数、剩余失误次数；
    右侧“重新开始”按钮可重置本关。
"""

import sys
import copy
import pygame

from core import (
    EMPTY, UP, DOWN, LEFT, RIGHT,
    ARROW_CHARS, can_fly, count_arrows, level_cleared,
    try_click, LEVELS, MAX_MISTAKES,
)

# ---------- 窗口与配色 ----------
WIDTH, HEIGHT = 600, 720
CELL = 70
BOARD_TOP = 130
BOARD_LEFT = 60

BG = (245, 247, 250)
BOARD_BG = (255, 255, 255)
GRID_LINE = (210, 216, 224)
ARROW_COLOR = (45, 90, 180)
ARROW_BG = (228, 236, 248)
BLOCKED_COLOR = (214, 69, 69)
TEXT = (45, 55, 72)
SUBTEXT = (110, 120, 135)
BTN = (70, 130, 210)
BTN_HOVER = (95, 150, 225)
BTN_TEXT = (255, 255, 255)
GREEN = (56, 168, 100)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("一箭又一箭")
        self.clock = pygame.time.Clock()

        # 中文字体
        self.font_title = pygame.font.SysFont("microsoftyahei,simhei,arial", 52, bold=True)
        self.font_big = pygame.font.SysFont("microsoftyahei,simhei,arial", 40, bold=True)
        self.font_mid = pygame.font.SysFont("microsoftyahei,simhei,arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("microsoftyahei,simhei,arial", 20)
        self.font_tiny = pygame.font.SysFont("microsoftyahei,simhei,arial", 16)

        self.state = "START"      # START | PLAYING | LEVEL_CLEAR | GAME_OVER | ALL_CLEAR
        self.level_idx = 0
        self._reset_level()

        # 动画状态
        self.flying = None        # dict: row,col,dx,dy,dist,alpha
        self.shake_cell = None    # (row, col)
        self.shake_ticks = 0

    # ---------- 关卡管理 ----------
    def _reset_level(self):
        self.board = copy.deepcopy(LEVELS[self.level_idx])
        self.mistakes = 0
        self.flying = None
        self.shake_cell = None
        self.shake_ticks = 0

    def _next_level(self):
        self.level_idx += 1
        if self.level_idx >= len(LEVELS):
            self.state = "ALL_CLEAR"
        else:
            self._reset_level()
            self.state = "PLAYING"

    # ---------- 坐标换算 ----------
    def _board_pixel(self, row, col):
        """格子左上角像素坐标。"""
        x = BOARD_LEFT + col * CELL
        y = BOARD_TOP + row * CELL
        return x, y

    def _pixel_to_cell(self, px, py):
        col = (px - BOARD_LEFT) // CELL
        row = (py - BOARD_TOP) // CELL
        return int(row), int(col)

    # ---------- 事件处理 ----------
    def _handle_click(self, mx, my):
        if self.state == "START":
            if self._button_rect(210, 560, 180, 56).collidepoint(mx, my):
                self.level_idx = 0
                self._reset_level()
                self.state = "PLAYING"
            return

        if self.state == "PLAYING":
            # 重新开始按钮
            if self._restart_rect().collidepoint(mx, my):
                self._reset_level()
                return
            row, col = self._pixel_to_cell(mx, my)
            if not (0 <= row < len(self.board) and 0 <= col < len(self.board[0])):
                return
            result = try_click(self.board, row, col)
            if result["flew"]:
                # 触发飞出动画：记录方向与初始偏移
                direction = self._last_direction
                dx, dy = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}[direction]
                self.flying = {"row": row, "col": col, "dx": dx, "dy": dy,
                               "dist": 0, "char": ARROW_CHARS[direction]}
                self.board[row][col] = EMPTY
            elif result["blocked"]:
                self.mistakes += 1
                self.shake_cell = (row, col)
                self.shake_ticks = 18
                if self.mistakes >= MAX_MISTAKES:
                    self.state = "GAME_OVER"
            return

        if self.state == "LEVEL_CLEAR":
            if self._button_rect(180, 430, 240, 56).collidepoint(mx, my):
                self._next_level()
            return

        if self.state == "GAME_OVER":
            if self._button_rect(180, 430, 240, 56).collidepoint(mx, my):
                self._reset_level()
                self.state = "PLAYING"
            return

        if self.state == "ALL_CLEAR":
            if self._button_rect(180, 460, 240, 56).collidepoint(mx, my):
                self.level_idx = 0
                self._reset_level()
                self.state = "START"
            return

    # 记录上一次点击时箭头方向（try_click 清空了棋盘，所以要先取）
    # 为简单起见，在调用 try_click 前先把方向存下来。
    # （下面在 _handle_click 中读取）
    # 这里用一个属性在点击瞬间保存。

    # ---------- 按钮 ----------
    def _button_rect(self, x, y, w, h):
        return pygame.Rect(x, y, w, h)

    def _restart_rect(self):
        return pygame.Rect(WIDTH - 130, 20, 110, 40)

    # ---------- 绘制 ----------
    def _draw_button(self, rect, text, hover=False):
        color = BTN_HOVER if hover else BTN
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        label = self.font_small.render(text, True, BTN_TEXT)
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_start(self, mx, my):
        self.screen.fill(BG)
        t = self.font_title.render("一箭又一箭", True, TEXT)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, 240)))
        sub = self.font_small.render("点击箭头，按正确顺序让所有箭飞出棋盘", True, SUBTEXT)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 300)))

        rules = [
            "规则：点击箭头，若它指向的方向上没有其他箭头阻挡，",
            "      它就会飞出棋盘；否则会被挡住并扣一次失误。",
            "      清空全部箭头即可过关，失误次数用完则失败。",
        ]
        for i, line in enumerate(rules):
            s = self.font_tiny.render(line, True, SUBTEXT)
            self.screen.blit(s, s.get_rect(center=(WIDTH // 2, 380 + i * 26)))

        btn = self._button_rect(210, 560, 180, 56)
        self._draw_button(btn, "开始游戏", hover=btn.collidepoint(mx, my))

    def _draw_hud(self):
        # 顶栏信息
        level_s = self.font_mid.render(f"第 {self.level_idx + 1} 关 / 共 {len(LEVELS)} 关", True, TEXT)
        self.screen.blit(level_s, (BOARD_LEFT, 25))

        remain = count_arrows(self.board)
        arrow_s = self.font_small.render(f"剩余箭头：{remain}", True, SUBTEXT)
        self.screen.blit(arrow_s, (BOARD_LEFT, 60))

        mistake_color = BLOCKED_COLOR if self.mistakes >= MAX_MISTAKES - 1 else SUBTEXT
        mist_s = self.font_small.render(f"失误：{self.mistakes} / {MAX_MISTAKES}", True, mistake_color)
        self.screen.blit(mist_s, (BOARD_LEFT + 200, 60))

        self._draw_button(self._restart_rect(), "重新开始",
                          hover=self._restart_rect().collidepoint(pygame.mouse.get_pos()))

    def _draw_board(self):
        rows, cols = len(self.board), len(self.board[0])
        board_w = cols * CELL
        board_h = rows * CELL
        # 底板
        pygame.draw.rect(self.screen, BOARD_BG,
                         (BOARD_LEFT - 8, BOARD_TOP - 8, board_w + 16, board_h + 16),
                         border_radius=12)
        # 网格
        for r in range(rows + 1):
            pygame.draw.line(self.screen, GRID_LINE,
                             (BOARD_LEFT, BOARD_TOP + r * CELL),
                             (BOARD_LEFT + board_w, BOARD_TOP + r * CELL))
        for c in range(cols + 1):
            pygame.draw.line(self.screen, GRID_LINE,
                             (BOARD_LEFT + c * CELL, BOARD_TOP),
                             (BOARD_LEFT + c * CELL, BOARD_TOP + board_h))

        # 箭头
        shake_off = (0, 0)
        if self.shake_cell and self.shake_ticks > 0:
            sr, sc = self.shake_cell
            # 来回抖动
            import math
            shake_off = (int(3 * math.sin(self.shake_ticks * 1.6)), 0)

        for r in range(rows):
            for c in range(cols):
                v = self.board[r][c]
                if v == EMPTY:
                    continue
                x, y = self._board_pixel(r, c)
                cx = x + CELL // 2 + shake_off[0] if (self.shake_cell == (r, c)) else x + CELL // 2
                cy = y + CELL // 2 + shake_off[1] if (self.shake_cell == (r, c)) else y + CELL // 2
                is_shaking = (self.shake_cell == (r, c) and self.shake_ticks > 0)
                color = BLOCKED_COLOR if is_shaking else ARROW_COLOR
                # 箭头底色方块
                pygame.draw.rect(self.screen, ARROW_BG,
                                 (x + 6, y + 6, CELL - 12, CELL - 12), border_radius=8)
                ch = self.font_big.render(ARROW_CHARS[v], True, color)
                self.screen.blit(ch, ch.get_rect(center=(cx, cy)))

        # 飞出动画
        if self.flying:
            f = self.flying
            cx = BOARD_LEFT + f["col"] * CELL + CELL // 2 + f["dx"] * f["dist"]
            cy = BOARD_TOP + f["row"] * CELL + CELL // 2 + f["dy"] * f["dist"]
            alpha = max(0, 255 - int(f["dist"] * 1.2))
            ch = self.font_big.render(f["char"], True, ARROW_COLOR)
            ch.set_alpha(alpha)
            self.screen.blit(ch, ch.get_rect(center=(cx, cy)))

    def _draw_overlay(self, title, color, lines, btn_text, btn_rect):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        t = self.font_big.render(title, True, color)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, 330)))
        for i, line in enumerate(lines):
            s = self.font_small.render(line, True, (230, 235, 245))
            self.screen.blit(s, s.get_rect(center=(WIDTH // 2, 390 + i * 30)))

        mx, my = pygame.mouse.get_pos()
        self._draw_button(btn_rect, btn_text, hover=btn_rect.collidepoint(mx, my))

    # ---------- 主循环 ----------
    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 点击前先保存被点箭头的方向，供飞出动画使用
                    if self.state == "PLAYING":
                        row, col = self._pixel_to_cell(mx, my)
                        if (0 <= row < len(self.board) and 0 <= col < len(self.board[0])
                                and self.board[row][col] != EMPTY):
                            self._last_direction = self.board[row][col]
                    self._handle_click(mx, my)

            # 更新动画
            if self.flying:
                self.flying["dist"] += 14
                if self.flying["dist"] > (WIDTH + HEIGHT):
                    self.flying = None
                    if level_cleared(self.board):
                        self.state = "LEVEL_CLEAR"
            if self.shake_ticks > 0:
                self.shake_ticks -= 1
                if self.shake_ticks == 0:
                    self.shake_cell = None

            # 绘制
            self.screen.fill(BG)
            if self.state == "START":
                self._draw_start(mx, my)
            elif self.state == "PLAYING":
                self._draw_hud()
                self._draw_board()
            elif self.state == "LEVEL_CLEAR":
                self._draw_hud()
                self._draw_board()
                self._draw_overlay("本关通过！", GREEN,
                                   ["所有箭头都飞出了棋盘", "点击下方按钮进入下一关"],
                                   "下一关", self._button_rect(180, 430, 240, 56))
            elif self.state == "GAME_OVER":
                self._draw_hud()
                self._draw_board()
                self._draw_overlay("失误过多，本关失败", BLOCKED_COLOR,
                                   ["别灰心，再试一次！"],
                                   "重新开始", self._button_rect(180, 430, 240, 56))
            elif self.state == "ALL_CLEAR":
                self._draw_overlay("恭喜！全部关卡通关 🎉", GREEN,
                                   ["你已经完成了所有关卡"],
                                   "返回主菜单", self._button_rect(180, 460, 240, 56))

            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
