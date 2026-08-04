# 第 4 课：MCP 资源读取

## 这节课学什么

MCP 不只有工具，还有资源。

工具是“让系统做一件事”，例如查订单状态。

资源是“让系统给出一份资料”，例如会员积分规则、退款规则。

## 会遇到什么场景

公司已经有一份由业务团队维护的规则、菜单或操作说明。Agent 需要读取它，但不应该把“读取资料”伪装成一次业务操作。

这时服务端公开资源 URI，客户端按 URI 读取内容。

## 先运行

```powershell
py .\MCPDemo\04_MCP资源读取\demo.py
```

终端会打印两份资料：

```text
资源 URI：coffee://knowledge/member-points
资料正文：
# 会员积分规则
...

资源 URI：coffee://knowledge/refund-policy
资料正文：
# 退款规则
...
```

运行后打开 `输出/resources_result.json`，可以看到 URI、资料类型和完整正文。当前适配器把 URI 放在 `Blob.metadata["uri"]` 中。

## 最关键的两行

服务端：

```python
@mcp.resource("coffee://knowledge/member-points")
```

客户端：

```python
resources = await client.get_resources(server_name="coffee_knowledge")
```

第一行把一份资料挂到固定地址 `coffee://knowledge/member-points`；第二行把服务端的资源读回来。

## 它和 RAG 不一样

RAG：用户问题会和很多资料做相似度比较，再找可能相关的片段。

本课资源：客户端明确要求读取 `coffee://knowledge/member-points` 这个地址，服务端就返回这一份完整资料，没有相似度计算。

## 它和工具不一样

`get_order_status("A1001")`：要传订单号，服务端执行查询动作，返回某个订单的结果。

`coffee://knowledge/member-points`：不传业务参数，读取一份固定规则资料。

下一课会把这两类能力放在一起看：什么时候该让 Agent 调工具，什么时候该把资源当作回答资料。
