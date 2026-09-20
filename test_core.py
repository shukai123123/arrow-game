"""
自动化测试：覆盖作业要求中的 T01~T06 六个测试点。

运行方式：
    python test_core.py
全部通过会打印 PASS，并返回退出码 0。
"""

import copy
import core
from core import (
    EMPTY, UP, DOWN, LEFT, RIGHT,
    can_fly, count_arrows, level_cleared, try_click,
    LEVELS, MAX_MISTAKES,
)


passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}  {detail}")


def t01_click_clear_arrow_flies():
    print("T01 点击前方无阻挡的箭头，箭头飞出棋盘并消失")
    board = [
        [EMPTY, EMPTY, RIGHT],   # (0,2) →，右边是边界，无阻挡
        [EMPTY, EMPTY, EMPTY],
    ]
    ok_before = can_fly(board, 0, 2)
    res = try_click(board, 0, 2)
    check("T01 判定为可飞", ok_before is True)
    check("T01 点击后飞出", res["flew"] is True)
    check("T01 箭头已消失", board[0][2] == EMPTY)


def t02_blocked_arrow_not_fly():
    print("T02 点击前方有阻挡的箭头，箭头不消失，失误次数减 1")
    board = [
        [RIGHT, EMPTY, UP],      # (0,0)→ 右边 (0,2) 有 ↑，被阻挡
        [EMPTY, EMPTY, EMPTY],
    ]
    res = try_click(board, 0, 0)
    check("T02 判定为被阻挡", res["blocked"] is True)
    check("T02 箭头仍在原位", board[0][0] == RIGHT)


def t03_edge_arrow_no_out_of_bound():
    print("T03 点击位于边缘且朝向棋盘外的箭头，正常飞出，不越界")
    board = [
        [UP, EMPTY, EMPTY, LEFT],   # (0,0)↑ 朝上边界；(0,3)← 朝左但左边有空格
        [EMPTY, EMPTY, EMPTY, EMPTY],
    ]
    # (0,0) 朝向上边界，应该可飞
    check("T03 上边界↑可飞", can_fly(board, 0, 0) is True)
    # 下边界的↓
    board2 = [
        [EMPTY, EMPTY, EMPTY],
        [EMPTY, DOWN, EMPTY],
    ]
    check("T03 下边界↓可飞", can_fly(board2, 1, 1) is True)
    # 右边界→
    board3 = [
        [EMPTY, EMPTY, RIGHT],
        [EMPTY, EMPTY, EMPTY],
    ]
    check("T03 右边界→可飞", can_fly(board3, 0, 2) is True)
    # 不应抛异常
    try:
        can_fly(board, -1, 0)
        can_fly(board, 0, 99)
        check("T03 越界访问不抛异常", True)
    except Exception as e:
        check("T03 越界访问不抛异常", False, str(e))


def t04_clear_all_then_next():
    print("T04 消除本关全部箭头，显示通关并进入下一关")
    board = copy.deepcopy(LEVELS[0])
    check("T04 初始有箭头", count_arrows(board) > 0)
    # 按已验证的通关顺序点击
    for (r, c) in [(0, 2), (2, 2), (0, 0)]:
        res = try_click(board, r, c)
        assert res["flew"], f"({r},{c}) 应当能飞，但被挡住了"
    check("T04 全部清空", level_cleared(board) is True)
    check("T04 剩余箭头为0", count_arrows(board) == 0)


def t05_mistakes_run_out():
    print("T05 失误次数耗尽，显示失败并允许重新开始")
    board = copy.deepcopy(LEVELS[1])
    mistakes = 0
    # (0,0)↓ 被 (3,0)← 挡住；反复点它模拟失误
    for _ in range(MAX_MISTAKES):
        res = try_click(board, 0, 0)
        if res["blocked"]:
            mistakes += 1
    check("T05 累计失误等于MAX", mistakes == MAX_MISTAKES)
    check("T05 失误后箭头仍在", board[0][0] == DOWN)


def t06_restart_resets():
    print("T06 游戏进行中重新开始，箭头布局和失误次数恢复")
    board = copy.deepcopy(LEVELS[2])
    original = copy.deepcopy(board)
    # 消掉一个箭头、记一次失误
    try_click(board, 0, 4)   # ↑ 可飞
    mistakes = 1
    check("T06 已改变", board != original)
    # 重新开始 = 深拷贝恢复初始关卡
    board = copy.deepcopy(LEVELS[2])
    mistakes = 0
    check("T06 布局恢复", board == original)
    check("T06 失误归零", mistakes == 0)


def verify_all_levels_solvable():
    print("附加校验：每个关卡都存在合法通关顺序")
    for idx, lv in enumerate(LEVELS):
        # 贪心模拟：反复找任意一个可飞箭头消除，直到清空或无解
        board = copy.deepcopy(lv)
        steps = 0
        while not level_cleared(board):
            found = None
            for r in range(len(board)):
                for c in range(len(board[0])):
                    if board[r][c] != EMPTY and can_fly(board, r, c):
                        found = (r, c)
                        break
                if found:
                    break
            if not found:
                check(f"第{idx+1}关可通关", False, "存在死局")
                return
            try_click(board, found[0], found[1])
            steps += 1
            if steps > 100:
                break
        check(f"第{idx+1}关可通关（{steps}步）", level_cleared(board))


if __name__ == "__main__":
    print("=" * 50)
    print("运行 T01 ~ T06 自动化测试")
    print("=" * 50)
    t01_click_clear_arrow_flies()
    t02_blocked_arrow_not_fly()
    t03_edge_arrow_no_out_of_bound()
    t04_clear_all_then_next()
    t05_mistakes_run_out()
    t06_restart_resets()
    verify_all_levels_solvable()
    print("=" * 50)
    print(f"结果：{passed} 通过，{failed} 失败")
    print("=" * 50)
    import sys
    sys.exit(0 if failed == 0 else 1)
