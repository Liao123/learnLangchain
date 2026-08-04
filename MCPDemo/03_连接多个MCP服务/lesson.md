# 第 3 课：连接多个 MCP 服务

## 这节课学什么

一个客服 Agent 同时连接两个独立服务：订单服务和会员服务。

模型问订单时选订单工具，问积分时选会员工具。

## 会遇到什么场景

真实公司不会只有一个“大而全的工具服务”。订单、会员、退款、库存通常是不同系统。

Agent 需要把它们都接进来，但每个系统仍然独立维护自己的数据和工具。

## 先运行

```powershell
py .\MCPDemo\03_连接多个MCP服务\demo.py
```

第一次输入：

```text
订单 A1001 到哪里了？
```

重点看这一行：

```text
模型请求 get_order_status，来自 order_service，参数是 {'order_id': 'A1001'}
```

再重新运行一次，输入：

```text
会员 M1001 还有多少积分？
```

这次应当看到：

```text
模型请求 get_member_points，来自 member_service，参数是 {'member_id': 'M1001'}
```

## 新增的核心代码

```python
client = MultiServerMCPClient(
    {
        "order_service": {...},
        "member_service": {...},
    }
)
tools = await client.get_tools()
```

`MultiServerMCPClient` 会启动两个独立服务进程，并把两个服务公开的工具合成一个 `tools` 列表交给模型。

## 一句话流程

订单服务和会员服务各自公开工具 -> 客户端一次拿到全部工具 -> 模型选择其中一个 -> Python 把请求发到对应服务 -> 工具结果交回模型回答。

## 你现在要区分的两件事

`order_server.py`、`member_server.py`：业务系统，负责真正查询自己的数据。

`demo.py`：Agent 客户端，负责连接服务、把工具交给模型、执行模型请求的工具。

运行后可打开 `输出/multi_server_result.json`，查看模型最终实际调用了哪个服务的哪个工具。
