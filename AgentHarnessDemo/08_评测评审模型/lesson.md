# Agent Harness 第 8 课：评测评审模型

## 这课学什么

用人工已经判好对错的回答，测试“评审模型”是否会按标准正确判分。

## 解决什么问题

第 7 课里，评审模型会输出 `passed`。但它本身也是模型，可能把错误回答判通过，或把正确回答判失败。

## 你现在要做的

1. 先打开 `数据\judge_cases.json`。

   里面每条都有人工标签 `expected_passed`：这才是本课的标准答案。

2. 在项目根目录运行：

   ```powershell
   py .\AgentHarnessDemo\08_评测评审模型\demo.py
   ```

3. 打开 `输出\judge_evaluation_report.json`。

## 这课真正怎么判分

不是判断退款 Agent，而是判断评审模型：

```python
judge_matches_human = judge_result.passed == case["expected_passed"]
```

人工认为应该失败，评审模型也判失败，才算这道“评审测试题”通过。

## 你要记住

评审模型的分数高，不代表它一定可靠；这里只是一个很小的开始。真实项目还要持续补充人工标注的边界案例。

一句话：用模型评审 Agent 之前，先用人工标准答案评审这个评审模型。
