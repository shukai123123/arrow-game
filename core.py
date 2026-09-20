"""
一箭又一箭 —— 核心游戏逻辑（不依赖 pygame，便于自动化测试）。

棋盘用二维整数列表表示，每个格子取值：
    EMPTY  空
    UP     箭头朝上
    DOWN   箭头朝下
    LEFT   箭头朝左
    RIGHT  箭头朝右

通关规则：
    点击某箭头后，沿其方向向棋盘外扫描，
    若该方向上、箭头与边界之间没有任何其他箭头，则它可以飞出；
    否则被阻挡，不能消除，并记一次失误。
"""

# ---------- 方向常量 ----------
EMPTY = 0
UP = 1
DOWN = 2
LEFT = 3
RIGHT = 4

# 方向 -> (行增量 dr, 列增量 dc)
DIRS = {
    UP: (-1, 0),
    DOWN: (1, 0),
    LEFT: (0, -1),
    RIGHT: (0, 1),
}

# 方向 -> 显示字符
ARROW_CHARS = {
    UP: "↑",
    DOWN: "↓",
    LEFT: "←",
    RIGHT: "→",
}

# 每关允许的最大失误次数
MAX_MISTAKES = 3


def rows(board):
    return len(board)


def cols(board):
    return len(board[0]) if board else 0


def in_bounds(board, row, col):
    return 0 <= row < rows(board) and 0 <= col < cols(board)


def can_fly(board, row, col):
    """判断 (row, col) 处的箭头能否飞出棋盘。

    从该箭头出发，沿其方向一格一格走向边界；
    途中只要遇到任何非空格子（另一个箭头），就返回 False；
    一路走到边界都为空，则返回 True。
    """
    if not in_bounds(board, row, col):
        return False
    direction = board[row][col]
    if direction == EMPTY or direction not in DIRS:
        return False
    dr, dc = DIRS[direction]
    r, c = row + dr, col + dc
    while 0 <= r < rows(board) and 0 <= c < cols(board):
        if board[r][c] != EMPTY:
            return False
        r += dr
        c += dc
    return True


def count_arrows(board):
    """统计棋盘上剩余箭头数量。"""
    return sum(1 for row in board for v in row if v != EMPTY)


def level_cleared(board):
    """棋盘上没有箭头即本关清空。"""
    return count_arrows(board) == 0


def try_click(board, row, col):
    """尝试点击 (row, col)，返回一个结果字典。

    返回字段：
        ok      —— 点击是否落在有效箭头上
        flew    —— 箭头是否成功飞出
        blocked —— 是否因为被阻挡而失败
    """
    if not in_bounds(board, row, col):
        return {"ok": False, "flew": False, "blocked": False}
    if board[row][col] == EMPTY:
        return {"ok": False, "flew": False, "blocked": False}
    if can_fly(board, row, col):
        board[row][col] = EMPTY  # 飞出后消失
        return {"ok": True, "flew": True, "blocked": False}
    return {"ok": True, "flew": False, "blocked": True}


# ---------- 关卡数据 ----------
# 每个关卡都是一个二维列表，0 为空，1/2/3/4 为四个方向。
# 每个关卡都已人工验证存在唯一/合理的通关顺序。
LEVELS = [
    # 第 1 关（3x3，教学关）：
    #   → . ↑
    #   . . .
    #   . . ←
    # 通关顺序：先 (0,2)↑ → 再 (2,2)← → 最后 (0,0)→
    [
        [RIGHT, EMPTY, UP],
        [EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, LEFT],
    ],
    # 第 2 关（4x4）：
    #   ↓ . . →
    #   . . . .
    #   . . . .
    #   ← . . ↑
    # 通关顺序：(0,3)→ → (3,3)↑ → (3,0)← → (0,0)↓
    [
        [DOWN, EMPTY, EMPTY, RIGHT],
        [EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY],
        [LEFT, EMPTY, EMPTY, UP],
    ],
    # 第 3 关（5x5，较难）：
    #   . → . . ↑
    #   . . . . .
    #   . . . . .
    #   ↓ . . . .
    #   . . ← . .
    # 通关顺序：(0,4)↑ → (0,1)→ → (3,0)↓ → (4,2)←
    [
        [EMPTY, RIGHT, EMPTY, EMPTY, UP],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [DOWN, EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, LEFT, EMPTY, EMPTY],
    ],
]
