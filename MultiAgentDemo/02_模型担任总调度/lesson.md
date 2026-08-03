# 多 Agent 第 2 课：模型担任总调度

## 这节课学什么

把上一课的 `if "退款" in question` 换成模型判断。

模型只负责理解人话和输出路线：

```json
{"route": "order"}
```

Python 仍然负责校验路线，并用 `Command(goto=...)` 进入对应专员。

## 解决什么问题

用户不会总是刚好说“退款”。例如：

```text
钱什么时候能退回来？
我不想要了，怎么处理？
我的包裹什么时候到？
```

模型能理解这些不同说法，再选择对应专员。

## 运行前

这课需要 DeepSeek Key。PowerShell 中运行前设置：

```powershell
$env:DEEPSEEK_API_KEY = "你的真实 Key"
```

在 PyCharm 中运行时，则在该运行配置的“环境变量”里设置 `DEEPSEEK_API_KEY`。

## 运行

```powershell
py .\MultiAgentDemo\02_模型担任总调度\demo.py
```

可以输入：

```text
钱什么时候能退回来？
```

观察类似输出：

```text
总调度 AI 原始返回：{"route": "refund"}
总调度决定：交给退款专员。
最终回答：退款专员：退款通常会在 1 到 3 个工作日原路退回。
```

## 本课只记一句话

```text
模型负责把人话判断成 route；Python 只接受白名单 route，再进入固定专员节点。
```
