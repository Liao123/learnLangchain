# Agent Harness 第 14 课：记录 Token 使用量

## 这课学什么

从模型响应中读取输入、输出和总 Token，并按单次请求预算判定是否超量。

## 解决什么问题

模型回答变长、提示词变长、RAG 资料塞得更多，都会增加 Token 消耗和成本。

## 你现在要做的

在项目根目录运行：

```powershell
py .\AgentHarnessDemo\14_记录Token使用量\demo.py
```

打开 `输出\token_usage_report.json`。

## 你要看什么

```json
{
  "max_total_tokens": 500,
  "token_usage": {
    "input_tokens": 30,
    "output_tokens": 20,
    "total_tokens": 50
  },
  "evaluation": {
    "budget_status": "within_budget",
    "passed": true
  }
}
```

数字只是示例，实际值取决于模型服务返回的数据。

如果 `budget_status` 是 `usage_unavailable`，意思是本次服务没有提供 Token 用量，不能把它误认为 0。

一句话：速度看毫秒，成本先看 Token；两者都要进入 Harness 的运行记录。
