# 第 5 课：资源与工具配合

## 这节课学什么

同一个客服 Agent 里：

- 会员积分规则是 MCP 资源，先读进模型的回答资料。
- 订单状态是 MCP 工具，模型遇到订单问题时才调用。

## 解决什么问题

不要把所有信息都当成工具查询。

固定、可信的规则资料可以先加载；会变化的订单状态要在用户提问时实时查询。

## 先运行

```powershell
py .\MCPDemo\05_资源与工具配合\demo.py
```

第一次输入：

```text
金卡会员消费 100 元能获得多少积分？
```

你应当看到没有“模型请求实时工具”这一行。模型用已经加载的规则回答：150 积分。

再重新运行一次，输入：

```text
订单 A1001 到哪里了？
```

这次应当看到：

```text
第 1 轮：模型请求实时工具 get_order_status，参数是 {'order_id': 'A1001'}
```

## 本课最重要的运行顺序

```text
Python 读取会员规则资源
-> 把规则文字塞进 SystemMessage
-> 模型看用户问题
-> 积分问题：直接回答
-> 订单问题：请求 MCP 工具
-> 工具结果交回模型
-> 模型回答
```

## 新代码只看这里

```python
resources = await client.get_resources(
    server_name="coffee_service",
    uris="coffee://knowledge/member-points",
)
policy_text = resources[0].as_string()
```

`resources[0]` 是一份 MCP 返回的资料对象；`as_string()` 取出正文，赋值给 `policy_text`。

然后把 `policy_text` 放到 `SystemMessage` 中，模型每次回答都能看到这份规则。

## 关键区别

资源不会因为 `model.bind_tools(...)` 自动变成模型可调用的工具。

本课是 Python 先明确读取固定资源，再把内容交给模型；订单这种实时数据才保留给模型自主发起工具请求。

运行后打开 `输出/resource_and_tool_result.json`，可以看到加载的规则、实际工具调用记录和最终回答。
