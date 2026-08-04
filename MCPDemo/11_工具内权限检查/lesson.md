# 第 11 课：工具内权限检查

## 这节课学什么

前几课的 Token 检查决定“能不能连接 MCP 服务”。

这一课再加一层：连接成功后，具体工具还要检查“这个身份能不能看这笔订单”。

## 会遇到什么场景

普通会员和客服专员都可以连接订单 MCP 服务，但权限不同：

```text
普通会员：只能查询自己的订单。
客服专员：可以查询任意订单。
菜单 Agent：连接有效，但没有订单读取权限。
```

因此不能只在客户端或模型里写“你只能查自己的订单”，必须在 `get_order_status` 工具内部检查。

## 第一步：启动服务端

终端一运行：

```powershell
py .\MCPDemo\11_工具内权限检查\server.py
```

## 第二步：普通会员查自己的订单

终端二运行：

```powershell
$env:MCP_DEMO_TOKEN = "member-u1001-token"
py .\MCPDemo\11_工具内权限检查\client.py
```

输入：

```text
A1001
```

结果是成功，因为 Token 的 `subject` 是 `U1001`，而订单 A1001 的主人也是 `U1001`。

## 第三步：故意查别人的订单

保持同一个 Token，重新运行客户端，输入：

```text
A1002
```

结果会是：

```json
{"ok": false, "error": "order_access_denied", "message": "当前身份无权查看这笔订单。"}
```

即使客户端、用户或模型知道 `A1002`，也拿不到它的配送状态。

## 客服专员测试

```powershell
$env:MCP_DEMO_TOKEN = "support-agent-token"
py .\MCPDemo\11_工具内权限检查\client.py
```

输入 `A1002`，这次会成功，因为它有 `orders:read:any`。

## 新 API 只看这里

```python
access_token = get_access_token()
```

这个函数返回当前请求已经验证过的身份信息。普通会员请求时，它的关键值是：

```python
access_token.subject  # "U1001"
access_token.scopes   # ["orders:read"]
```

这两个值来自服务端验证 Token 的结果，不来自模型工具参数。

## 工具里实际检查什么

```python
is_owner = order["owner_user_id"] == access_token.subject
can_read_any_order = "orders:read:any" in access_token.scopes
```

订单主人可以看；拥有更高权限的客服也可以看；其他情况返回拒绝结果。

## 一句话流程

Token 验证成功 -> 工具开始执行 -> `get_access_token()` 取可信身份 -> 比较订单主人和 scope -> 返回数据或拒绝。

运行后查看 `输出/tool_authorization_result.json`。文件不保存 Token 值。
