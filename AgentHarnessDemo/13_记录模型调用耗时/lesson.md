# Agent Harness 第 13 课：记录模型调用耗时

## 这课学什么

测量一次模型调用实际花了多少毫秒，并按业务设定的时限判分。

## 解决什么问题

回答正确不代表服务可用。如果客服回复要等 30 秒，用户体验仍然很差。

## 你现在要做的

在项目根目录运行：

```powershell
py .\AgentHarnessDemo\13_记录模型调用耗时\demo.py
```

打开 `输出\latency_report.json`。

## 你要看什么

```json
{
  "max_allowed_latency_ms": 15000,
  "call_result": {
    "latency_ms": 820,
    "error": null
  },
  "evaluation": {
    "latency_passed": true,
    "passed": true
  }
}
```

`820` 只是示例。你机器实际运行会得到自己的毫秒数。

`perf_counter()` 只包住 `model.invoke(...)`，所以测的是 API 请求和模型生成，不包含 Python 启动、读文件等其他时间。

一句话：Harness 不只问“答对了吗”，也问“在允许时间内答出来了吗”。
