import argparse
import random
import re
import sys
from fractions import Fraction


# ==================== 1. 分数转换与格式化 ====================
def format_fraction(frac: Fraction) -> str:
    """将 Fraction 对象转化为带分数/真分数/整数格式：例如 2'3/8, 3/5, 0, 4"""
    if frac.denominator == 1:
        return str(frac.numerator)          # 整数：4
    whole = frac.numerator // frac.denominator
    rem = frac.numerator % frac.denominator
    if whole > 0:
        return f"{whole}'{rem}/{frac.denominator}"   # 带分数：2'3/8
    return f"{rem}/{frac.denominator}"               # 真分数：3/5


def parse_fraction(s: str) -> Fraction:
    """解析 2'3/8, 3/5, 4 格式为 Fraction 对象"""
    s = s.strip()
    if "'" in s:
        whole_part, frac_part = s.split("'")
        num, den = frac_part.split("/")
        return Fraction(int(whole_part) * int(den) + int(num), int(den))
    elif "/" in s:
        num, den = s.split("/")
        return Fraction(int(num), int(den))
    else:
        return Fraction(int(s), 1)


# ==================== 2. 语法树定义与判重 ====================
class ExprNode:

    def __init__(self, val=None, op=None, left=None, right=None):
        self.val: Fraction = val  # 叶子节点值或计算结果
        self.op: str = op  # '+', '-', '×', '÷'
        self.left: ExprNode = left
        self.right: ExprNode = right

    def to_str(self, parent_op=None) -> str:
        """生成带括号的表达式文本"""
        if self.op is None:
            return format_fraction(self.val)          # 叶节点：直接输出分数

        op_precedence = {"+": 1, "-": 1, "×": 2, "÷": 2}
        my_prec = op_precedence[self.op]

        left_str = self.left.to_str(self.op)
        right_str = self.right.to_str(self.op)

        # 结合性与优先级处理括号
        # 右子树：优先级更低，或同级但本节点是 '-'/'÷'（不满足右结合）时必须加括号，如 a - (b - c)
        if self.right.op and (
            op_precedence[self.right.op] < my_prec
            or (self.op in ("-", "÷") and op_precedence[self.right.op] == my_prec)
        ):
            right_str = f"({right_str})"

        # 左子树：只有优先级更低才需要括号（同级靠左结合天然免括号）
        if self.left.op and op_precedence[self.left.op] < my_prec:
            left_str = f"({left_str})"

        expr = f"{left_str} {self.op} {right_str}"
        return expr

    def get_canonical_repr(self) -> str:
        """计算规范化字符串用于判重（利用加法与乘法的可交换性）"""
        if self.op is None:
            return format_fraction(self.val)

        c_left = self.left.get_canonical_repr()
        c_right = self.right.get_canonical_repr()

        # 加法与乘法遵循交换律：左右规范串按字典序固定排序，使交换后的等价树产出同一字符串
        if self.op in ("+", "×"):
            if c_left > c_right:
                c_left, c_right = c_right, c_left

        return f"({c_left} {self.op} {c_right})"


# ==================== 3. 随机题目生成 ====================
def generate_operand(r: int) -> ExprNode:
    """生成范围 [0, r) 的操作数（自然数或真分数）"""
    # 分母取值范围为 [2, r-1]，故 r <= 2 时不存在合法真分数，只能生成自然数
    is_fraction = random.choice([True, False])
    if is_fraction and r > 2:
        den = random.randint(2, r - 1)
        num = random.randint(1, den * r - 1)
        # 排除整除情况，保证是带分数或真分数
        while num % den == 0:
            num = random.randint(1, den * r - 1)
        return ExprNode(val=Fraction(num, den))
    else:
        return ExprNode(val=Fraction(random.randint(0, r - 1), 1))


def build_expression_tree(op_count: int, r: int) -> ExprNode | None:
    """递归生成表达式树，运算符数量 1~3

    性能优化（效能分析改进点）：对 '-' 与 '÷' 采用"交换构造代替拒绝采样"。
    原实现先随机生成左右操作数、不满足约束就整棵子树丢弃重试，
    cProfile 显示约 73% 的子树构建被拒绝浪费；
    现改为生成后按需交换左右子树，使约束天然满足，仅极端情况才重试。
    """
    if op_count == 0:
        return generate_operand(r)

    # 尝试构建子树
    for _ in range(50):
        left_ops = random.randint(0, op_count - 1)
        right_ops = op_count - 1 - left_ops

        left_node = build_expression_tree(left_ops, r)
        right_node = build_expression_tree(right_ops, r)
        if not left_node or not right_node:
            continue

        op = random.choice(["+", "-", "×", "÷"])

        # 规则 3：计算过程不能产生负数 (e1 >= e2)——交换两操作数即可满足
        if op == "-" and left_node.val < right_node.val:
            left_node, right_node = right_node, left_node

        # 规则 4：e1 ÷ e2 的结果必须是真分数 (0 < e1 / e2 < 1)
        # 先交换保证 e1 <= e2，则商 <= 1；仅剩 0÷0、a÷a 等相等情况需重新采样
        if op == "÷":
            if left_node.val > right_node.val:
                left_node, right_node = right_node, left_node
            if left_node.val == 0 or left_node.val == right_node.val:
                continue

        # 计算结果
        if op == "+":
            val = left_node.val + right_node.val
        elif op == "-":
            val = left_node.val - right_node.val
        elif op == "×":
            val = left_node.val * right_node.val
        else:
            val = left_node.val / right_node.val

        return ExprNode(val=val, op=op, left=left_node, right=right_node)

    return None


def generate_exercises(n: int, r: int):
    seen_canonical = set()
    exercises = []
    answers = []

    attempts = 0
    max_attempts = n * 200

    while len(exercises) < n and attempts < max_attempts:
        attempts += 1
        num_ops = random.randint(1, 3)  # 最多 3 个运算符
        tree = build_expression_tree(num_ops, r)
        if not tree:
            continue

        canon = tree.get_canonical_repr()
        if canon in seen_canonical:
            continue

        seen_canonical.add(canon)
        exercises.append(f"{tree.to_str()} =")
        answers.append(format_fraction(tree.val))

    if len(exercises) < n:
        print(
            f"提示：在给定的范围 r={r}下，生成了 {len(exercises)} 道不重复题目。"
        )

    with open("Exercises.txt", "w", encoding="utf-8") as f_ex, open(
        "Answers.txt", "w", encoding="utf-8"
    ) as f_ans:
        for idx, (ex, ans) in enumerate(zip(exercises, answers), 1):
            f_ex.write(f"{idx}. {ex}\n")
            f_ans.write(f"{idx}. {ans}\n")

    print(f"成功生成 {len(exercises)} 道题目至 Exercises.txt 和 Answers.txt")


# ==================== 4. 批改与对错统计 ====================
# 数字 token 匹配：带分数 2'3/8 | 分数 3/8 | 整数 2（一次扫描按次序优先匹配）
_NUM_TOKEN_RE = re.compile(r"(\d+)'(\d+)/(\d+)|(\d+)/(\d+)|(\d+)")


def parse_expression_to_fraction(expr_str: str) -> Fraction:
    """将题目的算术表达式字符串求值（全程 Fraction 精确运算，无浮点误差）"""
    expr = expr_str.replace("×", "*").replace("÷", "/").replace("−", "-")

    # 关键点：把所有数字统一替换为 Fraction 构造，避免 eval 中 int/int
    # 退化为二进制浮点数（如 1/9 无法精确表示），导致与标准答案比对失败。
    # 2'3/8 -> (Fraction(2)+Fraction(3,8))，3/8 -> Fraction(3,8)，2 -> Fraction(2)
    def _repl(m: re.Match) -> str:
        if m.group(1) is not None:
            return f"(Fraction({m.group(1)})+Fraction({m.group(2)},{m.group(3)}))"
        if m.group(4) is not None:
            return f"Fraction({m.group(4)},{m.group(5)})"
        return f"Fraction({m.group(6)})"

    expr_eval_str = _NUM_TOKEN_RE.sub(_repl, expr)
    # 使用 Python 内置 eval 安全计算（受限作用域，仅暴露 Fraction）
    return eval(expr_eval_str, {"__builtins__": None, "Fraction": Fraction})


def grade(exercise_file: str, answer_file: str):
    try:
        with open(exercise_file, "r", encoding="utf-8") as f_ex, open(
            answer_file, "r", encoding="utf-8"
        ) as f_ans:
            ex_lines = [l.strip() for l in f_ex if l.strip()]
            ans_lines = [l.strip() for l in f_ans if l.strip()]
    except FileNotFoundError as e:
        print(f"文件读取失败: {e}")
        return

    correct_ids = []
    wrong_ids = []

    for ex_line, ans_line in zip(ex_lines, ans_lines):
        try:
            ex_id, ex_content = ex_line.split(".", 1)
            ans_id, ans_content = ans_line.split(".", 1)

            ex_content = ex_content.replace("=", "").strip()
            expected_frac = parse_fraction(ans_content.strip())
            actual_frac = parse_expression_to_fraction(ex_content)

            if expected_frac == actual_frac:
                correct_ids.append(ex_id.strip())
            else:
                wrong_ids.append(ex_id.strip())
        except Exception:
            wrong_ids.append(ex_line.split(".")[0].strip())

    with open("Grade.txt", "w", encoding="utf-8") as f_out:
        corr_str = (
            f"Correct: {len(correct_ids)} (" + ", ".join(correct_ids) + ")\n"
        )
        wrong_str = f"Wrong: {len(wrong_ids)} (" + ", ".join(wrong_ids) + ")\n"
        f_out.write(corr_str)
        f_out.write(wrong_str)

    print(f"判题完成！结果已存入 Grade.txt")
    print(
        f"Correct: {len(correct_ids)}, Wrong: {len(wrong_ids)}"
    )


# ==================== 5. 命令行入口 ====================
def main():
    parser = argparse.ArgumentParser(
        description="自动生成小学四则运算题目或对题目进行批改评分程序。"
    )
    parser.add_argument("-n", type=int, help="生成题目的个数")
    parser.add_argument(
        "-r", type=int, help="数值范围（自然数、真分数和真分数分母 < r）"
    )
    parser.add_argument("-e", type=str, help="题目文件路径 (Exercises.txt)")
    parser.add_argument("-a", type=str, help="答案文件路径 (Answers.txt)")

    args = parser.parse_args()

    # 判定功能
    if args.e and args.a:
        grade(args.e, args.a)
    # 生成功能
    elif args.r is not None:
        if args.r < 1:
            print("错误: -r 参数必须为大于或等于 1 的自然数。")
            sys.exit(1)
        n = args.n if args.n is not None else 10
        generate_exercises(n, args.r)
    else:
        print("错误: 必须指定 -r 参数生成题目，或者指定 -e 和 -a 参数进行判题。")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()