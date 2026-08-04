# 第 6 课：MCP 提示词模板

## 这节课学什么

MCP 的 `Prompt` 是服务端提供的可复用消息模板。

客户端传参数，服务端把参数填进模板，返回一组可以直接交给模型的 `HumanMessage`、`AIMessage`。

## 会遇到什么场景

客服、法务、运营团队希望所有 Agent 使用同一套标准话术或处理步骤，但不同请求要填入不同订单号、客户问题。

这时模板不必复制到每个 Agent 代码里，可以由业务服务统一提供。

## 先运行

```powershell
py .\MCPDemo\06_MCP提示词模板\demo.py
```

终端会显示：

```text
消息类型：human
消息内容：
请按星光咖啡退款客服规范处理这条请求。

订单号：A1001
退款原因：饮品洒漏
...
```

没有调用模型。你看到的是“准备好要交给模型的消息”。完整结果在 `输出/prompt_result.json`。

## 新 API 只看两处

服务端：

```python
@mcp.prompt()
def draft_refund_response(order_id: str, refund_reason: str) -> list[dict]:
```

它声明一个有两个变量的模板。调用时每个变量都要有值。

客户端：

```python
prompt_messages = await client.get_prompt(
    server_name="coffee_prompt",
    prompt_name="draft_refund_response",
    arguments={"order_id": "A1001", "refund_reason": "饮品洒漏"},
)
```

`prompt_messages` 返回的不是字符串，而是消息数组；本课实际是 `[HumanMessage(...)]`。

## 和资源、工具的区别

资源：一份业务资料，例如“积分规则”。

工具：执行或查询业务动作，例如“查询订单 A1001”。

Prompt：一套写好了变量位置的消息模板，例如“处理订单 `{order_id}` 的退款原因 `{refund_reason}`”。

## 实际怎么接模型

下一步如果要调用模型，直接把 `prompt_messages` 放进：

```python
response = model.invoke(prompt_messages)
```

模型收到的就是本课终端打印出的那条完整消息。
