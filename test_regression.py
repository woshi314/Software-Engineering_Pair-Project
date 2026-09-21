# -*- coding: utf-8 -*-
"""回归测试：验证判题精度修复、-r 1/2 崩溃修复、交换构造优化"""
import random
from fractions import Fraction as F

from Myapp import (
    build_expression_tree,
    generate_exercises,
    grade,
    parse_expression_to_fraction as pe,
)

# ---------- 1. 判题精确求值单测（浮点时代必错的用例） ----------
assert pe("1/6 + 1/8") == F(7, 24)
assert pe("3 + 3'1/9 + 3'1/3") == F(85, 9)
assert pe("9'1/5 * 5'5/8 - 1/2 / 1") == F(205, 4)
assert pe("(1'1/7 + 6'1/2) * 4'3/5") == F(2461, 70)
print("[1] parse_expression_to_fraction 精确求值 4 例全部通过")

# ---------- 2. 生成端约束回归：非负、商为真分数、操作数范围 ----------
random.seed(7)
for r in (2, 3, 10, 20):
    for _ in range(300):
        t = build_expression_tree(random.randint(1, 3), r)
        if t is None:
            continue
        assert t.val >= 0

        def check(node):
            if node.op is None:
                assert 0 <= node.val < r  # 操作数范围
                return
            check(node.left)
            check(node.right)
            if node.op == "-":
                assert node.left.val >= node.right.val
            if node.op == "÷":
                assert 0 < node.val < 1

        check(t)
print("[2] 生成约束回归（非负/真分数商/范围, r=2,3,10,20）通过，且 r=2 不再崩溃")

# ---------- 3. r=1 边界 ----------
generate_exercises(5, 1)  # 不应抛异常
print("[3] -r 1 边界运行正常")

# ---------- 4. 端到端：生成 500 题 -> 自动判题应全对 ----------
generate_exercises(500, 12)
with open("Exercises.txt", encoding="utf-8") as f:
    n_lines = len(f.read().splitlines())
grade("Exercises.txt", "Answers.txt")
with open("Grade.txt", encoding="utf-8") as f:
    g = f.read()
assert f"Correct: {n_lines}" in g and "Wrong: 0" in g, g
print(f"[4] 端到端判题: {n_lines} 题全部 Correct, Wrong: 0")
print("=== 回归测试全部通过 ===")
