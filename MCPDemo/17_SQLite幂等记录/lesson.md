# 第 17 课：SQLite 幂等记录

## 这节课学什么

上一课的幂等记录在 Python 字典里，服务一重启就没了。

这课把两份数据放到 SQLite 文件：

```text
orders：订单状态和真正取消次数。
idempotency_requests：幂等键、处理状态、第一次的结果。
```

所以服务重启后，同一个幂等键仍不会重复取消。

## 第零步：清空上次教学数据

终端运行：

```powershell
py .\MCPDemo\17_SQLite幂等记录\reset_data.py
```

它只删除本课 `输出/idempotency.sqlite`，让 A1001 回到“制作中”、幂等记录为空。

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\17_SQLite幂等记录\server.py
```

## 第二步：让客户端超时一次

终端二直接运行：

```powershell
py .\MCPDemo\17_SQLite幂等记录\client.py
```

客户端只等 1 秒，服务端要 2 秒，所以客户端超时。等 3 秒让服务端完成，然后回到终端一按 `Ctrl+C` 停止服务。

## 第三步：重启服务端再重试

终端一再次运行：

```powershell
py .\MCPDemo\17_SQLite幂等记录\server.py
```

终端二设置 3 秒等待并运行：

```powershell
$env:MCP_TOOL_TIMEOUT_SECONDS = "3"
py .\MCPDemo\17_SQLite幂等记录\client.py
```

你会得到：

```json
{
  "status": "已取消",
  "cancelled_count": 1,
  "idempotency_replayed": true
}
```

重点是服务重启了，但 `cancelled_count` 仍是 `1`。

## 最核心的变化

上一课：

```python
IDEMPOTENCY_RECORDS = {}
```

本课：

```sql
CREATE TABLE idempotency_requests (...)
```

字典随 Python 进程结束而消失；SQLite 文件会保存在磁盘上。

## 只看这条 SQL

```python
INSERT INTO idempotency_requests (idempotency_key, order_id, state, response_json)
VALUES (?, ?, 'processing', NULL)
```

第一次收到 `cancel-A1001-001`，先把它写进数据库并标为 `processing`，再开始耗时取消操作。

服务重启后，新的 Python 进程仍会从 SQLite 读到这一行。

## 为什么 `idempotency_key` 是主键

```sql
idempotency_key TEXT PRIMARY KEY
```

同一把键只能插入一次。两个请求同时到来时，一个插入成功；另一个会收到 `sqlite3.IntegrityError`，说明它不能重复执行写操作。

真实企业通常改用共享数据库或 Redis，并增加过期时间、恢复卡住的 `processing` 记录等机制；本课先掌握“幂等记录必须持久化”这一层。
