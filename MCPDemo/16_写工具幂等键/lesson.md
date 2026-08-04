# 第 16 课：写工具幂等键

## 这节课学什么

取消订单、扣款、创建退款等写操作遇到超时时，重试必须使用同一个幂等键。

服务端看到同一个键，只执行第一次请求；后续请求返回第一次结果，不再重复产生副作用。

## 先运行服务端

终端一运行：

```powershell
py .\MCPDemo\16_写工具幂等键\server.py
```

服务端的首次取消固定要 2 秒。

## 第一次：客户端超时

终端二直接运行：

```powershell
py .\MCPDemo\16_写工具幂等键\client.py
```

默认客户端只等 1 秒，因此会显示超时。它使用的幂等键是：

```text
cancel-A1001-001
```

请等 3 秒，让服务端的首次取消完成。

## 第二次：用相同幂等键重试

终端二运行：

```powershell
$env:MCP_TOOL_TIMEOUT_SECONDS = "3"
py .\MCPDemo\16_写工具幂等键\client.py
```

这次会很快返回类似：

```json
{
  "ok": true,
  "order_id": "A1001",
  "status": "已取消",
  "cancelled_count": 1,
  "idempotency_replayed": true
}
```

重点看 `cancelled_count` 仍然是 `1`，没有因为重试变成 `2`。

## 关键参数

```python
cancel_order(
    order_id="A1001",
    idempotency_key="cancel-A1001-001",
)
```

`order_id` 是要取消哪个订单。

`idempotency_key` 是“这一次取消意图”的唯一编号。网络超时后重试的是同一件事，所以必须复用同一个编号。

## 服务端核心逻辑

第一次收到键：

```text
没有记录 -> 登记 processing -> 真正取消订单 -> 保存 completed 结果
```

再次收到相同键：

```text
processing -> 告诉客户端仍在处理
completed -> 直接返回上次保存的结果
```

不会第二次执行：

```python
order["cancelled_count"] += 1
```

## 很重要

客户端超时不等于服务端没执行成功。

因此写操作重试时：

```text
错误做法：每次重试都生成新幂等键。
正确做法：同一业务意图始终复用第一次的幂等键。
```

真实企业会把幂等记录存到数据库或 Redis，不会像本课一样只放在内存。重启本课服务端会清空教学数据。
