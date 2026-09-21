# 小学四则运算题目生成器（结对项目·第三次作业）

成员：何星宇（3124004467）、陈广智（3124007003）

## 运行环境

Python 3.10+（使用了 `X | None` 类型标注语法），无第三方依赖。

## 使用说明

生成题目（输出 Exercises.txt 与 Answers.txt 到当前目录）：

    python Myapp.py -n 10 -r 10

- `-n`：生成题目个数（缺省为 10）
- `-r`：数值范围，自然数/真分数/分母均小于 r，必填，否则报错并显示帮助

批改判题（结果输出 Grade.txt）：

    python Myapp.py -e Exercises.txt -a Answers.txt

## 测试与复现

    python test_regression.py     # 自动化回归：判题自洽、约束属性、r=1/2 边界

## 效能分析复现

    python -m cProfile -o myapp.prof Myapp.py -n 10000 -r 20
    python -m flameprof -o flame.svg myapp.prof    # pip install flameprof

仓库内 `myapp.prof` / `myapp_after.prof` 为优化前后 profile 数据，对应博客"效能分析"中的火焰图。

## 文件说明

| 文件 | 说明 |
|---|---|
| Myapp.py | 主程序（生成 + 判题，命令行） |
| test_regression.py | 回归测试 |
| Exercises.txt / Answers.txt | 生成的题目 / 答案 |
| Grade.txt | 判题统计结果 |
