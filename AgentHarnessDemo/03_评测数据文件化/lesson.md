# Agent Harness 第 3 课：评测数据文件化

## 这课学什么

把评测题目从 Python 代码挪到 JSON 文件。

## 解决什么问题

业务同学要补一条测试题时，不应该改 Agent 程序，也不该碰评测逻辑。

## 什么场景会用

退款规则变化、增加新专员、发现线上错误案例后，都只需要在题集 JSON 里增加一条任务。

## 你现在要做的

1. 打开 `数据\routing_tasks.json`，先看四道题的数据。

2. 在项目根目录运行：

   ```powershell
   py .\AgentHarnessDemo\03_评测数据文件化\demo.py
   ```

3. 打开 `输出\batch_report.json`，确认里面有：

   ```json
   "dataset_name": "客服路由基础题集",
   "dataset_version": "v1"
   ```

## 你要记住

JSON 文件负责存题目和标准答案。

`demo.py` 负责读取题目、运行 Agent、判分和生成报告。

以后新增“修改订单”类题目，只需在 `tasks` 数组末尾加一个对象，不需要修改 `run_agent()`。

一句话：题目是数据，Agent 是程序。把两者分开，测试集才能持续增长。
